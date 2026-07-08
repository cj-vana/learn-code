import { Fragment, type ReactNode } from 'react';
import { pythonLanguage } from '@codemirror/lang-python';
import { highlightCode, tags as t, tagHighlighter } from '@lezer/highlight';

/*
 * Static syntax highlighter for fenced code blocks in rendered markdown.
 *
 * Reuses the Lezer Python parser and the same tag groups as the Solve/Scratch
 * editor (workbenchTheme.ts) so a snippet in a lesson reads identically to the
 * same code in the editor. It emits stable `tok-*` classes whose colours live
 * in global.css (`.prose pre .tok-*`); no CodeMirror view is mounted — a source
 * string is turned straight into highlighted React nodes.
 */
const highlighter = tagHighlighter([
  { tag: t.keyword, class: 'tok-keyword' },
  { tag: [t.operator, t.operatorKeyword], class: 'tok-operator' },
  { tag: [t.string, t.inserted], class: 'tok-string' },
  { tag: [t.typeName, t.className, t.number, t.changed, t.annotation], class: 'tok-lit' },
  { tag: [t.function(t.variableName), t.labelName], class: 'tok-function' },
  { tag: [t.comment, t.meta], class: 'tok-comment' },
  { tag: t.invalid, class: 'tok-invalid' },
]);

export function highlightSource(code: string, language: string): ReactNode {
  // Python is the only language the content library ships; anything else falls
  // back to plain (still monospaced) text rather than guessing a grammar.
  if (language !== 'python') return code;

  const tree = pythonLanguage.parser.parse(code);
  const nodes: ReactNode[] = [];
  let key = 0;
  highlightCode(
    code,
    tree,
    highlighter,
    (text, classes) => {
      nodes.push(
        classes ? (
          <span key={key++} className={classes}>
            {text}
          </span>
        ) : (
          <Fragment key={key++}>{text}</Fragment>
        ),
      );
    },
    () => {
      nodes.push(<Fragment key={key++}>{'\n'}</Fragment>);
    },
  );
  return nodes;
}
