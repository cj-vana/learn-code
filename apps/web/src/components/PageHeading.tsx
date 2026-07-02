export interface PageHeadingProps {
  kicker: string;
  title: string;
}

/** The stamped title block at the top of each bench. */
export function PageHeading({ kicker, title }: PageHeadingProps) {
  return (
    <div className="page-heading">
      <h1>{title}</h1>
      <span className="page-heading__kicker">{kicker}</span>
    </div>
  );
}
