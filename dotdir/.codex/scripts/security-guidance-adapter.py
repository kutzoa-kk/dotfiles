#!/usr/bin/env python3
"""Run the shared security-guidance hooks with Codex's synchronous protocol.

The upstream plugin remains unchanged. Authentication, state and interpreter
selection stay with its scripts; this adapter only translates hook input/output.
"""

import argparse
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import subprocess
import sys


EVENTS = {"SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SubagentStop"}
CONTEXT_EVENTS = {"SessionStart", "UserPromptSubmit", "PostToolUse"}
COMMON_FIELDS = {"continue", "stopReason", "suppressOutput", "systemMessage"}
TEXT_FIELDS = {"reason", "stopReason", "systemMessage"}


class AdapterError(ValueError):
    """An input or upstream response cannot be translated without losing data."""


@dataclass
class HookResult:
    stdout: str
    stderr: str
    returncode: int


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError("duplicate JSON key: " + key)
        result[key] = value
    return result


def _invalid_constant(value):
    raise AdapterError("non-finite JSON number: " + value)


DECODER = json.JSONDecoder(object_pairs_hook=_object, parse_constant=_invalid_constant)


def _decode(text):
    try:
        return DECODER.decode(text)
    except json.JSONDecodeError as error:
        raise AdapterError("invalid JSON: " + str(error)) from error


def _event(event):
    if not isinstance(event, str) or event not in EVENTS:
        raise AdapterError("unsupported hook event: " + str(event))


def _patch_inputs(payload):
    response = payload.get("tool_response")
    if isinstance(response, dict) and (
        response.get("interrupted") is True or response.get("success") is False
        or ("exit_code" in response and response["exit_code"] not in (None, 0))
    ):
        return []
    tool_input = payload.get("tool_input")
    patch = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(patch, str):
        raise AdapterError("apply_patch requires tool_input.command as a patch string")
    lines = patch.strip().splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise AdapterError("apply_patch requires complete Begin/End Patch markers")
    changes = []
    current = None
    for line in lines[1:-1]:
        header = next((kind for kind in ("Add", "Update", "Delete")
                       if line.startswith("*** " + kind + " File: ")), None)
        if header:
            path = line.split(": ", 1)[1]
            if not path:
                raise AdapterError("apply_patch contains an empty file path")
            current = {"kind": header, "path": path, "move": None}
            changes.append(current)
        elif current is None:
            raise AdapterError("apply_patch content precedes a file header")
        elif line.startswith("*** Move to: ") and current["kind"] == "Update":
            if current["move"] is not None or not line[len("*** Move to: "):]:
                raise AdapterError("apply_patch has an invalid Move to header")
            current["move"] = line[len("*** Move to: "):]
        elif current["kind"] == "Add" and line.startswith("+"):
            pass
        elif current["kind"] == "Update":
            if not (line.startswith(("+", " ", "-", "@@ "))
                    or line in ("", "@@", "*** End of File")):
                raise AdapterError("unrecognized apply_patch update line")
        else:
            raise AdapterError("unrecognized apply_patch file content")
    result = []
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        raise AdapterError("apply_patch requires cwd to resolve edited files")
    for change in changes:
        paths = ([change["path"], change["move"]]
                 if change["move"] else [change["path"]])
        for path in paths:
            # A deletion/old rename path must still reach record_touched_path.
            deleted = change["kind"] == "Delete" or (change["move"] and path == change["path"])
            file_path = Path(cwd) / path
            name, content = "Edit", ""
            if not deleted:
                name = "Write"
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as error:
                    raise AdapterError("cannot read apply_patch postimage " + str(file_path) + ": " + str(error)) from error
            result.append({**payload, "tool_name": name, "tool_input": {
                "file_path": str(file_path),
                "content" if name == "Write" else "new_string": content,
            }})
    return result


def normalize_input(payload):
    """Codex already maps shell calls to Bash; apply_patch needs per-file input."""
    if not isinstance(payload, dict):
        raise AdapterError("hook input must be a JSON object")
    event = payload.get("hook_event_name")
    _event(event)
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd or not Path(cwd).is_dir():
        raise AdapterError("hook cwd must name an existing directory")
    payload = {**payload, "cwd": str(Path(cwd).resolve())}
    if event == "PostToolUse" and payload.get("tool_name") == "apply_patch":
        return _patch_inputs(payload)
    if (event == "PostToolUse" and payload.get("tool_name") == "Bash"
            and isinstance(payload.get("tool_response"), str)):
        # Codex's exec_command exposes the raw completed output as a JSON
        # string. Upstream commit/push detection expects Claude's Bash object.
        payload = {**payload, "tool_response": {
            "stdout": payload["tool_response"], "stderr": "",
        }}
    return [payload]


def parse_output(stdout, event):
    """Accept one response, or SessionStart's exact bootstrap framing."""
    _event(event)
    text = stdout.strip()
    if not text:
        return {}
    try:
        first, end = DECODER.raw_decode(text)
    except json.JSONDecodeError as error:
        raise AdapterError("invalid upstream JSON: " + str(error)) from error
    rest = text[end:].strip()
    if isinstance(first, dict) and "async" in first:
        if (event != "SessionStart" or set(first) != {"async", "asyncTimeout"}
                or first["async"] is not True
                or type(first["asyncTimeout"]) is not int or first["asyncTimeout"] <= 0):
            raise AdapterError("unexpected async bootstrap declaration")
        if not rest:
            raise AdapterError("bootstrap ended without its final response")
        first = _decode(rest)
    elif rest:
        raise AdapterError("upstream returned multiple JSON documents or stray stdout")
    if not isinstance(first, dict):
        raise AdapterError("upstream response must be a JSON object")
    return first


def _join(first, second):
    if not first:
        return second
    if not second or second == first:
        return first
    return first.rstrip("\n") + "\n\n" + second


def _validate_output(output, event):
    allowed = set(COMMON_FIELDS)
    if event != "SessionStart":
        allowed.update({"decision", "reason"})
    if event in CONTEXT_EVENTS:
        allowed.add("hookSpecificOutput")
    unknown = set(output) - allowed
    if unknown:
        raise AdapterError("unsupported output fields for " + event + ": " + ", ".join(sorted(unknown)))
    for field in ("continue", "suppressOutput"):
        if field in output and type(output[field]) is not bool:
            raise AdapterError(field + " must be a boolean")
    if event == "PostToolUse" and output.get("suppressOutput") is True:
        raise AdapterError("Codex PostToolUse does not support suppressOutput")
    for field in TEXT_FIELDS:
        if field in output and not isinstance(output[field], str):
            raise AdapterError(field + " must be a string")
    if "decision" in output and output["decision"] != "block":
        raise AdapterError("decision must be block")
    if output.get("decision") == "block" and not output.get("reason", "").strip():
        raise AdapterError("a block decision must include a nonempty reason")
    if (event == "PostToolUse" and "reason" in output
            and output.get("decision") != "block" and output.get("continue", True)):
        raise AdapterError("Codex PostToolUse reason requires a block or continue:false")
    if "hookSpecificOutput" in output:
        context = output["hookSpecificOutput"]
        fields = {"hookEventName", "additionalContext"}
        if event == "PostToolUse":
            fields.add("updatedMCPToolOutput")
        if not isinstance(context, dict) or set(context) - fields:
            raise AdapterError("invalid hookSpecificOutput fields")
        if context.get("hookEventName") != event:
            raise AdapterError("hookSpecificOutput event does not match input")
        if "additionalContext" in context and not isinstance(context["additionalContext"], str):
            raise AdapterError("additionalContext must be a string")
        if context.get("updatedMCPToolOutput") is not None:
            raise AdapterError("Codex does not support updatedMCPToolOutput")


def _adapt_output(output, event):
    output = dict(output)
    if "metrics" in output:
        metrics = output.pop("metrics")
        if not isinstance(metrics, dict) or any(
            type(value) not in (bool, int, float)
            or (type(value) is float and not math.isfinite(value))
            for value in metrics.values()
        ):
            raise AdapterError("metrics must contain only booleans and finite numbers")
    if "rewakeSummary" in output:
        summary = output.pop("rewakeSummary")
        if not isinstance(summary, str):
            raise AdapterError("rewakeSummary must be a string")
        message = output.get("systemMessage", "")
        if not isinstance(message, str):
            raise AdapterError("systemMessage must be a string")
        output["systemMessage"] = _join(message, summary)
    _validate_output(output, event)
    return output


def _with_feedback(stderr, output):
    # Preserve original stderr and avoid duplicating findings already emitted
    # by the upstream Stop hook or by an earlier per-file result.
    for piece in (output.get("reason"), output.get("stopReason"),
                  output.get("hookSpecificOutput", {}).get("additionalContext"),
                  output.get("systemMessage")):
        if piece and piece not in stderr:
            stderr = _join(stderr, piece)
    return stderr


def _serialize(output):
    return json.dumps(output, ensure_ascii=False, allow_nan=False) + "\n" if output else ""


def adapt_result(event, stdout, stderr, returncode):
    output = _adapt_output(parse_output(stdout, event), event)
    # Codex ignores stdout JSON on a nonzero exit. Preserve both the original
    # status and every finding, even when upstream already wrote diagnostics.
    if returncode != 0:
        stderr = _with_feedback(stderr, output)
        if stderr and not stderr.endswith("\n"):
            stderr += "\n"
    return HookResult(_serialize(output), stderr, returncode)


def merge_results(event, results):
    """Combine per-file patch warnings into the single host hook response."""
    output, stderr, returncode = {}, "", 0
    for result in results:
        incoming = parse_output(result.stdout, event)
        stderr = _join(stderr, result.stderr)
        if result.returncode == 2 or (result.returncode and incoming.get("decision") == "block"):
            returncode = 2
        elif not returncode:
            returncode = result.returncode
        for field, value in incoming.items():
            if field in TEXT_FIELDS:
                output[field] = _join(output.get(field, ""), value)
            elif field == "hookSpecificOutput":
                context = output.setdefault(field, {"hookEventName": event})
                if "additionalContext" in value:
                    context["additionalContext"] = _join(context.get("additionalContext", ""), value["additionalContext"])
                if "updatedMCPToolOutput" in value:
                    if "updatedMCPToolOutput" in context and context["updatedMCPToolOutput"] != value["updatedMCPToolOutput"]:
                        raise AdapterError("conflicting updatedMCPToolOutput responses")
                    context["updatedMCPToolOutput"] = value["updatedMCPToolOutput"]
            elif field == "continue":
                output[field] = output.get(field, True) and value
            elif field == "suppressOutput":
                output[field] = output.get(field, False) or value
            else:
                output[field] = value
    _validate_output(output, event)
    if returncode and output.get("decision") == "block":
        returncode = 2
    if returncode:
        stderr = _with_feedback(stderr, output)
    return HookResult(_serialize(output), stderr, returncode)


def run_hook(plugin_root, payload):
    script = "ensure_agent_sdk.py" if payload["hook_event_name"] == "SessionStart" else "security_reminder_hook.py"
    shim = plugin_root / "hooks" / "sg-python.sh"
    entrypoint = plugin_root / "hooks" / script
    try:
        for path in (shim, entrypoint):
            if not path.is_file():
                raise AdapterError("missing upstream entrypoint: " + str(path))
        child = subprocess.run(
            ["bash", str(shim), str(entrypoint)],
            input=json.dumps(payload, ensure_ascii=False),
            capture_output=True, text=True, encoding="utf-8", check=False,
            cwd=payload["cwd"],
            env={**os.environ, "CLAUDE_PROJECT_DIR": payload["cwd"],
                 "CLAUDE_PLUGIN_ROOT": str(plugin_root)},
        )
    except (AdapterError, OSError, UnicodeError) as error:
        return HookResult("", "security-guidance adapter: " + str(error) + "\n", 1)
    try:
        return adapt_result(payload["hook_event_name"], child.stdout, child.stderr, child.returncode)
    except AdapterError as error:
        # Fail visibly; never pretend an unexpected upstream protocol succeeded.
        diagnostics = _join(child.stderr, "security-guidance adapter: " + str(error))
        diagnostics = _join(diagnostics, child.stdout)
        return HookResult("", diagnostics + "\n", child.returncode or 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        payload = _decode(sys.stdin.read())
        inputs = normalize_input(payload)
        results = [run_hook(args.plugin_root.resolve(), item) for item in inputs]
        result = merge_results(payload["hook_event_name"], results)
    except (AdapterError, OSError, UnicodeError) as error:
        print("security-guidance adapter: " + str(error), file=sys.stderr)
        return 1
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    # subprocess uses negative status for signals; retain shell exit semantics.
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    sys.exit(main())
