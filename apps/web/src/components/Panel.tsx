import type { ReactNode } from 'react';

export interface PanelProps {
  title: string;
  eyebrow?: string;
  tone?: 'paper' | 'ink';
  actions?: ReactNode;
  children: ReactNode;
  headingLevel?: 2 | 3;
}

/** A framed work surface: a titled panel that reads like a desk blotter or an
 *  inked blackboard depending on `tone`. */
export function Panel({
  title,
  eyebrow,
  tone = 'paper',
  actions,
  children,
  headingLevel = 2,
}: PanelProps) {
  const Heading = headingLevel === 3 ? 'h3' : 'h2';
  return (
    <section className={`panel${tone === 'ink' ? ' panel--ink' : ''}`}>
      <header className="panel__header">
        <div>
          {eyebrow ? <p className="panel__eyebrow">{eyebrow}</p> : null}
          <Heading className="panel__title">{title}</Heading>
        </div>
        {actions ? <div className="command-row">{actions}</div> : null}
      </header>
      <div className="panel__body">{children}</div>
    </section>
  );
}
