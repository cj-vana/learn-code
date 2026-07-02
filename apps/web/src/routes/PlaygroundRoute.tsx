import { useRef, useState } from 'react';
import { useRunPlayground } from '../api/queries';
import type { RunResult } from '../contracts';
import { CodeEditor } from '../editor/CodeEditor';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { CommandButton } from '../components/CommandButton';
import { TestReceipt } from '../components/TestReceipt';
import { describeError } from '../lib/format';

const SCRATCH_STARTER = `# Scratch bench — run anything.
for i in range(3):
    print("tick", i)
`;

interface HistoryEntry {
  id: number;
  source: string;
  stdin: string;
  status: RunResult['status'];
  durationMs: number;
  at: string;
}

export function PlaygroundRoute() {
  const [source, setSource] = useState(SCRATCH_STARTER);
  const [stdin, setStdin] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const nextId = useRef(1);
  const run = useRunPlayground();

  const onRun = () => {
    run.mutate(
      { language: 'python', source, stdin: stdin || null },
      {
        onSuccess: (result) => {
          setHistory((prev) =>
            [
              {
                id: nextId.current++,
                source,
                stdin,
                status: result.status,
                durationMs: result.duration_ms,
                at: new Date().toLocaleTimeString(),
              },
              ...prev,
            ].slice(0, 8),
          );
        },
      },
    );
  };

  const restore = (entry: HistoryEntry) => {
    setSource(entry.source);
    setStdin(entry.stdin);
  };

  return (
    <div className="stack">
      <PageHeading kicker="Scratch Bench" title="Try things out loud" />

      <div className="page-grid page-grid--solve">
        <div className="stack">
          <Panel title="Scratch code" eyebrow="python">
            <div className="editor-frame">
              <div className="editor-frame__caption">
                <span>scratch.py</span>
                <span>python</span>
              </div>
              <CodeEditor value={source} language="python" onChange={setSource} />
            </div>

            <label htmlFor="scratch-stdin" className="panel__eyebrow" style={{ display: 'block', margin: 'var(--space-3) 0 var(--space-1)' }}>
              Standard input
            </label>
            <textarea
              id="scratch-stdin"
              className="text-input"
              rows={3}
              placeholder="Piped to the program on stdin"
              value={stdin}
              onChange={(event) => setStdin(event.target.value)}
            />

            <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
              <CommandButton onClick={onRun} busy={run.isPending} aria-label="Run scratch code">
                Run
              </CommandButton>
            </div>
            {run.isError ? (
              <p className="status-note status-note--error" role="alert">
                {describeError(run.error)}
              </p>
            ) : null}
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Output" eyebrow="Most recent run">
            {run.data ? (
              <TestReceipt result={run.data} title="Scratch run" />
            ) : (
              <p className="muted">Run something to see stdout, stderr, and timing.</p>
            )}
          </Panel>

          <Panel title="Run history" eyebrow="Last few runs">
            {history.length === 0 ? (
              <p className="muted">No runs yet this session.</p>
            ) : (
              <ul className="run-history">
                {history.map((entry) => (
                  <li key={entry.id}>
                    <span>
                      {entry.at} · {entry.status} · {entry.durationMs} ms
                    </span>
                    <button
                      type="button"
                      className="command-btn command-btn--ghost"
                      style={{ padding: '2px 8px', fontSize: '0.68rem' }}
                      onClick={() => restore(entry)}
                    >
                      Restore
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
