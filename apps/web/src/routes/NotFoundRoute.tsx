import { Link } from 'react-router-dom';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';

export function NotFoundRoute() {
  return (
    <div className="stack">
      <PageHeading kicker="Off the map" title="No such bench" />
      <Panel title="Nothing filed here" eyebrow="404">
        <p>That page isn't in the ledger.</p>
        <Link className="command-btn command-btn--pine" to="/learn">
          Back to today's bench
        </Link>
      </Panel>
    </div>
  );
}
