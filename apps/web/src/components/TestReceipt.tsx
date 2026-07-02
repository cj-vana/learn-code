import type { RunResult, RunStatus } from '../contracts';

export interface TestReceiptProps {
  result: RunResult;
  title?: string;
}

const STATUS_TEXT: Record<RunStatus, string> = {
  passed: 'ALL TESTS PASS',
  failed_tests: 'TESTS FAILED',
  syntax_error: 'SYNTAX ERROR',
  runtime_error: 'RUNTIME ERROR',
  timeout: 'TIMED OUT',
  memory_exceeded: 'MEMORY EXCEEDED',
  output_exceeded: 'OUTPUT EXCEEDED',
  internal_error: 'RUNNER ERROR',
};

/** A perforated register receipt for a run: verdict at the top, an itemized
 *  line per test, totals, and the captured streams. Deliberately tactile so a
 *  run reads like a printed record rather than a toast. */
export function TestReceipt({ result, title = 'Runner Receipt' }: TestReceiptProps) {
  const passed = result.status === 'passed';
  return (
    <div className="receipt" aria-label="Test run receipt">
      <div className="receipt__head">
        <p className="receipt__title">{title}</p>
        <p className="receipt__verdict" data-passed={passed}>
          {STATUS_TEXT[result.status]}
        </p>
      </div>

      {result.test_summary.length > 0 ? (
        <div>
          {result.test_summary.map((test, index) => (
            <div key={`${test.name}-${index}`}>
              <div className="receipt__line" data-passed={test.passed}>
                <span
                  className="receipt__line-name"
                  data-mark={test.passed ? '[x]' : '[ ]'}
                >
                  {test.name}
                </span>
                <span className="receipt__vis">{test.visibility}</span>
              </div>
              {test.message ? <p className="receipt__msg">{test.message}</p> : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="muted">No individual test lines were reported.</p>
      )}

      <div className="receipt__totals">
        <span>
          {result.passed} passed / {result.failed} failed
        </span>
        <span>{result.duration_ms} ms</span>
      </div>

      {result.stdout ? (
        <div className="receipt__stream">
          <span className="receipt__vis">stdout</span>
          <pre>{result.stdout}</pre>
        </div>
      ) : null}
      {result.stderr ? (
        <div className="receipt__stream">
          <span className="receipt__vis">stderr</span>
          <pre>{result.stderr}</pre>
        </div>
      ) : null}
    </div>
  );
}
