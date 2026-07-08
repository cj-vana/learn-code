import type { ComponentProps } from 'react';
import ReactMarkdown, { type Components, type ExtraProps } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { highlightSource } from '../editor/codeHighlight';

type MarkdownProps = {
  children: string;
  /** Extra classes on the wrapping `.prose` block. Ignored when `inline`. */
  className?: string;
  /**
   * Render without a block wrapper: unwraps the paragraph so authored inline
   * code and emphasis flow inside the caller's own element (a heading, button
   * label, or `<p>`). Use for short single-line fields, not multi-paragraph
   * prose.
   */
  inline?: boolean;
};

// One code renderer for both modes: fenced blocks (```lang) arrive with a
// `language-*` class and are syntax-highlighted; inline `code` becomes a chip.
// `node` is dropped so it never lands on the DOM element as an attribute.
function renderCode({ node, className, children, ...props }: ComponentProps<'code'> & ExtraProps) {
  const language = /language-(\w+)/.exec(className ?? '')?.[1];
  if (language) {
    return (
      <code className={className}>
        {highlightSource(String(children).replace(/\n$/, ''), language)}
      </code>
    );
  }
  return (
    <code className="tok-inline" {...props}>
      {children}
    </code>
  );
}

const blockComponents: Components = { code: renderCode };
const inlineComponents: Components = { code: renderCode, p: ({ children }) => <>{children}</> };

/**
 * Renders authored markdown (lesson bodies, exercise prompts, quiz text) into
 * real elements. Content is trusted, in-repo YAML; react-markdown still never
 * emits raw HTML, and every dependency resolves from node_modules, so the
 * offline/no-external-URL scope holds.
 */
export function Markdown({ children, className, inline = false }: MarkdownProps) {
  if (inline) {
    return (
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={inlineComponents}>
        {children}
      </ReactMarkdown>
    );
  }
  return (
    <div className={className ? `prose ${className}` : 'prose'}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={blockComponents}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
