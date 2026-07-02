import { describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import { EditorView } from '@codemirror/view';
import { CodeEditor } from './CodeEditor';

function viewFor(container: HTMLElement): EditorView {
  const dom = container.querySelector<HTMLElement>('.cm-editor');
  expect(dom).not.toBeNull();
  const view = EditorView.findFromDOM(dom as HTMLElement);
  expect(view).not.toBeNull();
  return view as EditorView;
}

describe('CodeEditor', () => {
  it('propagates document edits to onChange with the new value', () => {
    const onChange = vi.fn();
    const { container } = render(
      <CodeEditor value="a = 1" language="python" onChange={onChange} />,
    );

    const view = viewFor(container);
    view.dispatch({ changes: { from: view.state.doc.length, insert: '2' } });

    expect(onChange).toHaveBeenCalledWith('a = 12');
  });

  it('does not echo prop-driven value changes back to onChange', () => {
    const onChange = vi.fn();
    const { container, rerender } = render(
      <CodeEditor value="first" language="python" onChange={onChange} />,
    );

    rerender(<CodeEditor value="second" language="python" onChange={onChange} />);

    expect(viewFor(container).state.doc.toString()).toBe('second');
    expect(onChange).not.toHaveBeenCalled();
  });
});
