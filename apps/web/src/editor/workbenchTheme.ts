/*
 * CodeMirror theme for the Solve/Scratch benches. The editor is the one dark
 * "blackboard" surface in the paper workshop, so its palette is drawn from the
 * blackboard/ochre/pine/blueprint tokens rather than a stock editor theme.
 *
 * Kept in the editor feature so no CodeMirror styling leaks into the rest of
 * the app.
 */

import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { EditorView } from '@codemirror/view';
import type { Extension } from '@codemirror/state';
import { tags as t } from '@lezer/highlight';

const BLACKBOARD = '#1a211b';
const PANEL = '#242b22';
const PAPER = '#f3efe2';
const OCHRE = '#b2873b';
const PINE = '#7fae72';
const BLUEPRINT = '#8fb9cb';
const RUST = '#d07a5f';
const GRAPHITE = '#9a9484';
const FOCUS = '#ff8a2a';

const chrome = EditorView.theme(
  {
    '&': {
      color: PAPER,
      backgroundColor: BLACKBOARD,
      fontSize: '13.5px',
    },
    '.cm-content': {
      fontFamily:
        "ui-monospace, 'SF Mono', 'JetBrains Mono', 'Cascadia Mono', Menlo, Consolas, monospace",
      caretColor: OCHRE,
      padding: '12px 0',
    },
    '.cm-cursor, .cm-dropCursor': { borderLeftColor: OCHRE },
    '&.cm-focused': { outline: `3px solid ${FOCUS}`, outlineOffset: '-1px' },
    '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection':
      {
        backgroundColor: 'rgba(178, 135, 59, 0.3)',
      },
    '.cm-activeLine': { backgroundColor: 'rgba(243, 239, 226, 0.05)' },
    '.cm-gutters': {
      backgroundColor: PANEL,
      color: GRAPHITE,
      border: 'none',
    },
    '.cm-activeLineGutter': { backgroundColor: 'rgba(243, 239, 226, 0.06)' },
    '.cm-lineNumbers .cm-gutterElement': { padding: '0 8px 0 12px' },
  },
  { dark: true },
);

const highlight = HighlightStyle.define([
  { tag: t.keyword, color: OCHRE },
  { tag: [t.name, t.deleted, t.character, t.propertyName, t.macroName], color: PAPER },
  { tag: [t.function(t.variableName), t.labelName], color: BLUEPRINT },
  { tag: [t.definition(t.name), t.separator], color: PAPER },
  { tag: [t.typeName, t.className, t.number, t.changed, t.annotation], color: PINE },
  { tag: [t.operator, t.operatorKeyword], color: OCHRE },
  { tag: [t.string, t.inserted], color: PINE },
  { tag: [t.comment, t.meta], color: GRAPHITE, fontStyle: 'italic' },
  { tag: t.invalid, color: RUST },
]);

export const workbenchTheme: Extension = [chrome, syntaxHighlighting(highlight)];
