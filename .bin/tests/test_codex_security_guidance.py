"""Exercise the Codex boundary with fixtures; never run the real reviewer."""

import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
ADAPTER_PATH = REPO / "dotdir/.codex/scripts/security-guidance-adapter.py"
INSTALLER = REPO / ".bin/apply-codex-security-guidance.py"
SCHEMAS = Path(__file__).parent / "fixtures/codex_hook_schemas"
EVENTS = {
    "SessionStart": "session-start",
    "UserPromptSubmit": "user-prompt-submit",
    "PostToolUse": "post-tool-use",
    "Stop": "stop",
    "SubagentStop": "subagent-stop",
}


def load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_schema(value, schema, root=None, path="$output"):
    """Validate only the keywords in the pinned runtime schemas, offline."""
    root = schema if root is None else root
    known = {"$schema", "$ref", "additionalProperties", "allOf", "const", "default",
             "definitions", "description", "enum", "properties", "required", "title", "type"}
    if set(schema) - known:
        raise AssertionError(f"Unsupported schema keywords: {set(schema) - known}")
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].removeprefix("#/").split("/"):
            node = node[part]
        validate_schema(value, node, root, path)
    for constraint in schema.get("allOf", []):
        validate_schema(value, constraint, root, path)
    expected = schema.get("type")
    types = {"object": dict, "string": str, "boolean": bool}
    if expected is not None and type(value) is not types[expected]:
        raise AssertionError(f"{path}: expected {expected}, got {value!r}")
    if "const" in schema and value != schema["const"]:
        raise AssertionError(f"{path}: wrong event discriminator")
    if "enum" in schema and value not in schema["enum"]:
        raise AssertionError(f"{path}: {value!r} is outside enum")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        missing = set(schema.get("required", [])) - set(value)
        if missing:
            raise AssertionError(f"{path}: missing {missing}")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise AssertionError(f"{path}: unknown fields {set(value) - set(properties)}")
        for key in set(properties) & set(value):
            validate_schema(value[key], properties[key], root, f"{path}.{key}")


class OutputContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = load_script(ADAPTER_PATH, "codex_security_guidance_adapter_test")

    def adapt(self, event, output, stderr="", code=0):
        stdout = output if isinstance(output, str) else json.dumps(output)
        return self.adapter.adapt_result(event, stdout, stderr, code)

    def assert_valid(self, event, result):
        value = json.loads(result.stdout) if result.stdout.strip() else {}
        schema_path = SCHEMAS / f"{EVENTS[event]}.command.output.schema.json"
        validate_schema(value, json.loads(schema_path.read_text()))
        if value.get("decision") == "block":
            self.assertIsInstance(value.get("reason"), str)
            self.assertTrue(value["reason"].strip())
        return value

    def test_clean_and_duplicate_skip_are_valid_without_metrics(self):
        for event in EVENTS:
            for output in ("", {"metrics": {"findings": 0}},
                           {"metrics": {"bash_hook_dedup": True}}):
                with self.subTest(event=event, output=output):
                    result = self.adapt(event, output)
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(self.assert_valid(event, result), {})

    def test_pattern_finding_survives_metrics_removal(self):
        finding = "Potential command injection in app.py:12; use an argument list."
        result = self.adapt("PostToolUse", {
            "metrics": {"pattern_hits": 1, "rule_mask": 4},
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse", "additionalContext": finding,
            },
        })
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.assert_valid("PostToolUse", result), {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse", "additionalContext": finding,
            },
        })

    def test_summary_does_not_replace_existing_notice_or_finding(self):
        result = self.adapt("PostToolUse", {
            "metrics": {"findings": 1},
            "rewakeSummary": "Commit security review found an issue",
            "systemMessage": "Reviewer completed",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse", "additionalContext": "Validate the redirect target.",
            },
        })
        output = self.assert_valid("PostToolUse", result)
        self.assertIn("Reviewer completed", output["systemMessage"])
        self.assertIn("Commit security review found an issue", output["systemMessage"])
        self.assertEqual(output["hookSpecificOutput"]["additionalContext"],
                         "Validate the redirect target.")

    def test_stop_and_subagent_stop_keep_block_and_reason(self):
        for event in ("Stop", "SubagentStop"):
            with self.subTest(event=event):
                result = self.adapt(event, {
                    "metrics": {"findings": 1}, "decision": "block",
                    "reason": "The authorization check is missing; fix or acknowledge it.",
                })
                self.assertEqual(result.returncode, 0)
                self.assertEqual(self.assert_valid(event, result), {
                    "decision": "block",
                    "reason": "The authorization check is missing; fix or acknowledge it.",
                })

    def test_exit_two_preserves_stderr_feedback_and_exit_status(self):
        for event in ("PostToolUse", "Stop", "SubagentStop", "UserPromptSubmit"):
            with self.subTest(event=event):
                result = self.adapt(event, {"metrics": {"findings": 1}},
                                    "Security review: reject untrusted redirect URLs.\n", 2)
                self.assertEqual(result.returncode, 2)
                self.assertIn("reject untrusted redirect URLs", result.stderr)
                self.assert_valid(event, result)

    def test_exit_two_copies_stdout_only_findings_to_stderr(self):
        result = self.adapt("PostToolUse", {
            "metrics": {"findings": 1},
            "hookSpecificOutput": {"hookEventName": "PostToolUse",
                                   "additionalContext": "SSRF: restrict the allowed URL scheme."},
        }, code=2)
        self.assertEqual(result.returncode, 2)
        self.assertIn("SSRF: restrict the allowed URL scheme.", result.stderr)
        self.assert_valid("PostToolUse", result)
        for event in ("Stop", "SubagentStop"):
            with self.subTest(event=event):
                result = self.adapt(event, {"metrics": {"findings": 1}, "decision": "block",
                                          "reason": "Do not bypass the authorization check."}, code=2)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Do not bypass the authorization check.", result.stderr)
                self.assert_valid(event, result)

    def test_session_bootstrap_preamble_becomes_one_valid_result(self):
        stdout = json.dumps({"async": True, "asyncTimeout": 180000}) + "\n" + json.dumps({
            "metrics": {"sdk_ready": False},
            "systemMessage": "Cross-file reviewer needs Python 3.10 or later.",
            "hookSpecificOutput": {"hookEventName": "SessionStart",
                                   "additionalContext": "Pattern checks remain active."},
        }) + "\n"
        result = self.adapt("SessionStart", stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.assert_valid("SessionStart", result), {
            "systemMessage": "Cross-file reviewer needs Python 3.10 or later.",
            "hookSpecificOutput": {"hookEventName": "SessionStart",
                                   "additionalContext": "Pattern checks remain active."},
        })

    def test_user_prompt_context_and_continue_control_are_retained(self):
        output = {"continue": False, "stopReason": "Review is required first.",
                  "hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                         "additionalContext": "Baseline captured."}}
        result = self.adapt("UserPromptSubmit", {"metrics": {"baseline": 1}, **output})
        self.assertEqual(self.assert_valid("UserPromptSubmit", result), output)

    def test_invalid_protocol_is_not_silently_treated_as_clean(self):
        invalid = [
            ("PostToolUse", '{"metrics":{}}\n{"decision":"block","reason":"finding"}'),
            ("PostToolUse", 'debug log\n{"metrics":{}}'),
            ("PostToolUse", '{"metrics":{},"metrics":{}}'),
            ("PostToolUse", '{"metrics":{"cost":NaN}}'),
            ("PostToolUse", {"unexpectedFinding": "Do not discard me"}),
            ("PostToolUse", {"continue": "false"}),
            ("PostToolUse", {"hookSpecificOutput": {"additionalContext": "finding"}}),
            ("PostToolUse", {"hookSpecificOutput": {"hookEventName": "Stop"}}),
            ("PostToolUse", {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                      "updatedMCPToolOutput": {"result": "changed"}}}),
            ("PostToolUse", {"suppressOutput": True}),
            ("PostToolUse", {"reason": "Finding without a decision is invalid for this event."}),
            ("Stop", {"decision": "block", "reason": "   "}),
            ("SubagentStop", {"decision": "block"}),
            ("Stop", {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": "finding"}}),
            ("SessionStart", '{"async":true,"asyncTimeout":180000}'),
            ("SessionStart", '{"async":true,"asyncTimeout":180000}\n{}\n{}'),
        ]
        for event, output in invalid:
            with self.subTest(event=event, output=output):
                with self.assertRaises(self.adapter.AdapterError):
                    self.adapt(event, output)

    def test_nonzero_result_does_not_hide_other_files_findings(self):
        first = self.adapter.HookResult("", "Reviewer warning on first file.\n", 1)
        second = self.adapt("PostToolUse", {
            "hookSpecificOutput": {"hookEventName": "PostToolUse",
                                   "additionalContext": "Authorization issue in second file."},
        }, stderr="Reviewer diagnostic on second file.\n", code=2)
        for results in ([first, second], [second, first]):
            with self.subTest(statuses=[item.returncode for item in results]):
                merged = self.adapter.merge_results("PostToolUse", results)
                self.assertEqual(merged.returncode, 2)
                for text in ("Reviewer warning on first file.", "Reviewer diagnostic on second file.",
                             "Authorization issue in second file."):
                    self.assertIn(text, merged.stderr)
                self.assert_valid("PostToolUse", merged)

    def test_failed_result_cannot_turn_a_separate_block_into_a_nonblocking_error(self):
        failure = self.adapter.HookResult("", "Review of another file could not finish.", 1)
        block = self.adapt("PostToolUse", {"decision": "block", "reason": "Fix the confirmed finding."})
        for results in ([failure, block], [block, failure]):
            with self.subTest(statuses=[item.returncode for item in results]):
                merged = self.adapter.merge_results("PostToolUse", results)
                self.assertEqual(merged.returncode, 2)
                self.assertIn("Fix the confirmed finding.", merged.stderr)
                self.assertIn("Review of another file could not finish.", merged.stderr)


class InputAndExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = load_script(ADAPTER_PATH, "codex_security_guidance_input_test")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-security-input-")
        self.addCleanup(self.temporary.cleanup)
        self.cwd = Path(self.temporary.name).resolve() / "project with spaces"
        self.cwd.mkdir()

    def payload(self, tool="Bash", command="git commit -m fix", response="[main abc1234] fix\n"):
        return {"hook_event_name": "PostToolUse", "session_id": "fixture-session",
                "turn_id": "fixture-turn", "tool_use_id": "fixture-tool-id", "cwd": str(self.cwd),
                "tool_name": tool, "tool_input": {"command": command}, "tool_response": response}

    def test_exec_hook_string_response_preserves_commit_sha_and_command(self):
        commit_output = "[main abc1234] fix authorization\n 1 file changed, 2 insertions(+)\n"
        payload = self.payload(response=commit_output)
        before = json.loads(json.dumps(payload))
        normalized = self.adapter.normalize_input(payload)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["tool_name"], "Bash")
        self.assertEqual(normalized[0]["tool_input"], {"command": "git commit -m fix"})
        self.assertEqual(normalized[0]["tool_response"], {"stdout": commit_output, "stderr": ""})
        self.assertEqual(normalized[0]["tool_use_id"], "fixture-tool-id")
        self.assertEqual(payload, before, "Normalizing must not mutate the caller's payload")

    def test_existing_bash_response_keeps_stderr_and_interrupted_flag(self):
        response = {"stdout": "output", "stderr": "git error", "interrupted": True}
        normalized = self.adapter.normalize_input(self.payload(response=response))
        self.assertEqual(normalized[0]["tool_response"], response)

    def test_patch_reads_complete_postimages_and_keeps_deleted_paths(self):
        (self.cwd / "new.py").write_text("# new file\ncall_user_function()\n")
        (self.cwd / "updated.py").write_text("dangerous_call(\n    user_input\n)\n# existing context\n")
        (self.cwd / "renamed.py").write_text("# renamed\ncheck_authorization()\n")
        patch = "\n".join([
            "*** Begin Patch", "*** Add File: new.py", "+# new file", "+call_user_function()",
            "*** Update File: updated.py", "@@", "-    previous_input", "+    user_input",
            "*** Delete File: deleted.py", "*** Update File: old.py", "*** Move to: renamed.py",
            "@@", " # renamed", "-old_call()", "+check_authorization()", "*** End Patch",
        ])
        normalized = self.adapter.normalize_input(self.payload("apply_patch", patch, "Success. Updated files."))
        self.assertEqual([(item["tool_name"], item["tool_input"]) for item in normalized], [
            ("Write", {"file_path": str(self.cwd / "new.py"), "content": "# new file\ncall_user_function()\n"}),
            ("Write", {"file_path": str(self.cwd / "updated.py"),
                       "content": "dangerous_call(\n    user_input\n)\n# existing context\n"}),
            ("Edit", {"file_path": str(self.cwd / "deleted.py"), "new_string": ""}),
            ("Edit", {"file_path": str(self.cwd / "old.py"), "new_string": ""}),
            ("Write", {"file_path": str(self.cwd / "renamed.py"), "content": "# renamed\ncheck_authorization()\n"}),
        ])
        self.assertTrue(all(item["tool_use_id"] == "fixture-tool-id" for item in normalized))

    def test_missing_postimage_and_malformed_patch_fail_visibly(self):
        for patch in ("*** Begin Patch\n*** Add File: missing.py\n+x\n*** End Patch",
                      "unframed patch", "*** Begin Patch\n*** Add File: \n+x\n*** End Patch"):
            with self.subTest(patch=patch):
                with self.assertRaises(self.adapter.AdapterError):
                    self.adapter.normalize_input(self.payload("apply_patch", patch, "Success."))

    def test_explicit_failed_patch_does_not_read_a_nonexistent_postimage(self):
        patch = "*** Begin Patch\n*** Add File: missing.py\n+x\n*** End Patch"
        for response in ({"success": False}, {"interrupted": True}, {"exit_code": 1}):
            with self.subTest(response=response):
                self.assertEqual(self.adapter.normalize_input(self.payload("apply_patch", patch, response)), [])

    def test_cli_runs_shared_entrypoint_for_every_file_and_keeps_all_findings(self):
        plugin = Path(self.temporary.name).resolve() / "fake upstream plugin"
        hooks = plugin / "hooks"
        hooks.mkdir(parents=True)
        (hooks / "sg-python.sh").write_text("#!/bin/sh\nexec " + shlex.quote(sys.executable) + ' "$@"\n')
        (hooks / "security_reminder_hook.py").write_text(
            "import json, os, pathlib, sys\n"
            "p = json.load(sys.stdin)\n"
            "assert os.getcwd() == p['cwd']\n"
            "assert os.environ['CLAUDE_PROJECT_DIR'] == p['cwd']\n"
            "assert os.environ['CLAUDE_PLUGIN_ROOT'] == str(pathlib.Path(__file__).parents[1])\n"
            "assert p['tool_name'] == 'Write'\n"
            "assert p['tool_input']['content'] == pathlib.Path(p['tool_input']['file_path']).read_text()\n"
            "name = pathlib.Path(p['tool_input']['file_path']).name\n"
            "print(json.dumps({'metrics': {'pattern_hits': 1}, 'hookSpecificOutput': "
            "{'hookEventName': 'PostToolUse', 'additionalContext': 'Finding in ' + name}}))\n"
        )
        for name in ("first.py", "second.py"):
            (self.cwd / name).write_text("# complete postimage\ncheck_input()\n")
        patch = ("*** Begin Patch\n*** Add File: first.py\n+# complete postimage\n+check_input()\n"
                 "*** Add File: second.py\n+# complete postimage\n+check_input()\n*** End Patch")
        result = subprocess.run(
            [sys.executable, str(ADAPTER_PATH), "--plugin-root", str(plugin)],
            input=json.dumps(self.payload("apply_patch", patch, "Success. Updated files.")),
            cwd=REPO, env={**os.environ, "CLAUDE_PROJECT_DIR": "/deliberately-wrong-fixture"},
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        validate_schema(output, json.loads((SCHEMAS / "post-tool-use.command.output.schema.json").read_text()))
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Finding in first.py", context)
        self.assertIn("Finding in second.py", context)
        self.assertNotIn("metrics", output)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-security-contract-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name) / "codex home"

    def plugin(self, version="2.0.8", native=None):
        root = self.home / "plugins/cache/claude-plugins-official/security-guidance" / version
        (root / ".claude-plugin").mkdir(parents=True)
        (root / "hooks").mkdir()
        upstream = {"name": "security-guidance", "version": version, "description": "original plugin"}
        (root / ".claude-plugin/plugin.json").write_text(json.dumps(upstream))
        for name in ("sg-python.sh", "security_reminder_hook.py", "ensure_agent_sdk.py"):
            (root / "hooks" / name).write_text("original upstream entrypoint: " + name)
        (root / "hooks/hooks.json").write_text(json.dumps({"hooks": {
            "PostToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": "original-review", "if": f"condition-{i}",
                 "asyncRewake": True} for i in range(7)
            ]}],
        }}))
        if native is not None:
            (root / ".codex-plugin").mkdir()
            (root / ".codex-plugin/plugin.json").write_text(json.dumps(native, indent=2) + "\n")
        return root

    def run_installer(self, *arguments):
        return subprocess.run(
            [sys.executable, str(INSTALLER), "--codex-home", str(self.home), *arguments],
            cwd=REPO,
            capture_output=True, text=True, timeout=20,
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_overlay_preserves_metadata_upstream_and_backup(self):
        native = {"name": "security-guidance", "version": "2.0.8", "description": "Codex metadata",
                  "skills": ["./skills/custom"], "mcpServers": "./servers.json",
                  "interface": {"displayName": "Security Guidance"}, "customMetadata": {"keep": True}}
        root = self.plugin(native=native)
        originals = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
        self.assert_success(self.run_installer())
        manifest_path = root / ".codex-plugin/plugin.json"
        installed = json.loads(manifest_path.read_text())
        self.assertEqual({k: v for k, v in installed.items() if k != "hooks"}, native)
        for path, contents in originals.items():
            if path != manifest_path:
                self.assertEqual(path.read_bytes(), contents, str(path))
        backup_path = root / ".codex-plugin/security-guidance-overlay.backup.json"
        backup_bytes = backup_path.read_bytes()
        self.assertEqual(json.loads(backup_bytes)["original_manifest"], originals[manifest_path].decode())
        manifest_bytes = manifest_path.read_bytes()
        self.assert_success(self.run_installer())
        self.assertEqual(manifest_path.read_bytes(), manifest_bytes)
        self.assertEqual(backup_path.read_bytes(), backup_bytes)
        self.assert_success(self.run_installer("--check"))

    def test_manifest_keeps_all_events_and_one_synchronous_bash_handler(self):
        root = self.plugin()
        self.assert_success(self.run_installer())
        hooks = json.loads((root / ".codex-plugin/plugin.json").read_text())["hooks"]["hooks"]
        self.assertEqual(set(hooks), set(EVENTS))
        bash_handlers = [handler for group in hooks["PostToolUse"]
                         if re.search(group.get("matcher", ".*"), "Bash")
                         for handler in group["hooks"]]
        self.assertEqual(len(bash_handlers), 1)
        edit_handlers = [handler for group in hooks["PostToolUse"]
                         if any(re.search(group.get("matcher", ".*"), alias)
                                for alias in ("apply_patch", "Edit", "Write"))
                         for handler in group["hooks"]]
        self.assertEqual(len(edit_handlers), 1)
        for groups in hooks.values():
            for group in groups:
                for handler in group["hooks"]:
                    self.assertFalse(handler.get("async", False))
                    self.assertFalse(set(handler) & {"if", "asyncRewake", "rewakeMessage", "rewakeSummary"})
                    self.assertIn("security-guidance-adapter.py", handler["command"])
        self.assertEqual(hooks["SessionStart"][0]["hooks"][0]["timeout"], 180)

    def test_check_and_dry_run_are_read_only_and_new_versions_are_applied(self):
        first = self.plugin()
        before = {str(path.relative_to(self.home)): path.read_bytes()
                  for path in self.home.rglob("*") if path.is_file()}
        self.assertEqual(self.run_installer("--check").returncode, 1)
        self.assert_success(self.run_installer("--dry-run"))
        after = {str(path.relative_to(self.home)): path.read_bytes()
                 for path in self.home.rglob("*") if path.is_file()}
        self.assertEqual(after, before)
        self.assert_success(self.run_installer())
        first_manifest = (first / ".codex-plugin/plugin.json").read_bytes()
        second = self.plugin("2.0.9")
        self.assertEqual(self.run_installer("--check").returncode, 1)
        self.assert_success(self.run_installer())
        self.assert_success(self.run_installer("--check"))
        self.assertEqual((first / ".codex-plugin/plugin.json").read_bytes(), first_manifest)
        second_manifest = json.loads((second / ".codex-plugin/plugin.json").read_text())
        self.assertEqual(second_manifest["version"], "2.0.9")
        self.assertIn("hooks", second_manifest)

    def test_unmanaged_custom_hooks_are_preserved_and_rejected_before_any_write(self):
        first = self.plugin()
        native = {"name": "security-guidance", "hooks": "./hooks/custom.json"}
        second = self.plugin("2.0.9", native=native)
        custom_path = second / ".codex-plugin/plugin.json"
        original = custom_path.read_bytes()
        result = self.run_installer()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(custom_path.read_bytes(), original)
        self.assertFalse((first / ".codex-plugin/plugin.json").exists())

    def test_absent_plugin_is_a_read_only_noop(self):
        self.assert_success(self.run_installer())
        self.assertFalse(self.home.exists())

    def test_portable_openai_extension_is_not_silently_shadowed(self):
        root = self.plugin()
        portable = {"name": "security-guidance", "extensions": {
            "com.openai": {"hooks": "./hooks/native.json", "skills": ["./skills"]},
        }}
        (root / "plugin.json").write_text(json.dumps(portable))
        result = self.run_installer()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(json.loads((root / "plugin.json").read_text()), portable)
        self.assertFalse((root / ".codex-plugin/plugin.json").exists())

    def test_dry_run_of_native_metadata_shows_default_upstream_hooks(self):
        root = self.plugin(native={"name": "security-guidance", "skills": ["./skills/keep"]})
        result = self.run_installer("--dry-run")
        self.assert_success(result)
        self.assertIn("original-review", result.stdout)
        self.assertIn("security-guidance-adapter.py", result.stdout)
        self.assertNotIn("hooks", json.loads((root / ".codex-plugin/plugin.json").read_text()))

    def test_user_changes_to_managed_hook_settings_are_not_overwritten(self):
        root = self.plugin()
        self.assert_success(self.run_installer())
        manifest_path = root / ".codex-plugin/plugin.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["hooks"]["hooks"]["PostToolUse"][1]["matcher"] = "Bash|custom_tool"
        manifest_path.write_text(json.dumps(manifest))
        original = manifest_path.read_bytes()
        result = self.run_installer()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(manifest_path.read_bytes(), original)

    def test_cache_version_symlink_cannot_modify_another_directory(self):
        first = self.plugin()
        outside = self.home / "plugins/marketplaces/security-guidance"
        shutil.copytree(first, outside)
        marker = outside / "must-not-change.txt"
        marker.write_text("unrelated installation")
        (first.parent / "2.0.9").symlink_to(outside, target_is_directory=True)
        result = self.run_installer()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(marker.read_text(), "unrelated installation")
        self.assertFalse((outside / ".codex-plugin").exists())
        self.assertFalse((first / ".codex-plugin").exists())


if __name__ == "__main__":
    unittest.main()
