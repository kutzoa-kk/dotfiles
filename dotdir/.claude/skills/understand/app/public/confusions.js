// 「分からなかった文」の記録を付箋から組み立てる（自分用に追加したファイル。UPSTREAM.md を参照）。
// 理解を終えるときにサーバーへ送り、メインの Claude が書き方の決まりに戻す材料にする。

const CONFUSION_TYPES = ['question', 'detail', 'term'];
const ANSWER_MAX = 500;
// グラフの点から作った付箋は、言い方の問題ではないので集めない
const GRAPH_VALUE_PREFIX = 'グラフの値：';

function collectConfusions(stickies, order) {
  return order
    .map((id) => stickies[id])
    .filter((st) => st && CONFUSION_TYPES.includes(st.type))
    .filter((st) => st.anchorText && !st.anchorText.startsWith(GRAPH_VALUE_PREFIX))
    .map((st) => {
      const messages = st.messages || [];
      const firstQ = messages.find((m) => m.role === 'user');
      const lastA = [...messages].reverse().find((m) => m.role === 'assistant');
      return {
        type: st.type,
        anchor: st.anchorText,
        question: firstQ ? firstQ.text : '',
        answer: lastA ? lastA.text.slice(0, ANSWER_MAX) : '',
        code: Boolean(st.code),
        fromSticky: st.parent !== 'main',
      };
    });
}

if (typeof module !== 'undefined') module.exports = { collectConfusions };
