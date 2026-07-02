import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAnswerQuiz, useQuizDetail } from '../api/queries';
import type { QuizAnswerResponse } from '../contracts';
import { PageHeading } from '../components/PageHeading';
import { Panel } from '../components/Panel';
import { QueryState } from '../components/QueryState';
import { PatternChip } from '../components/PatternChip';

export function QuizRoute() {
  const { id } = useParams<{ id: string }>();
  const quiz = useQuizDetail(id);
  const answer = useAnswerQuiz();
  const [index, setIndex] = useState(0);
  const [feedback, setFeedback] = useState<QuizAnswerResponse | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [finished, setFinished] = useState(false);

  const detail = quiz.data;
  const question = detail?.questions[index];
  const isLast = detail ? index === detail.questions.length - 1 : false;

  const choose = (choice: string) => {
    if (!detail || !question || feedback) return;
    answer.mutate(
      { quiz_id: detail.id, question_id: question.id, choice },
      {
        onSuccess: (response) => {
          setFeedback(response);
          if (response.correct) setCorrectCount((count) => count + 1);
        },
      },
    );
  };

  const advance = () => {
    setFeedback(null);
    if (isLast) {
      setFinished(true);
    } else {
      setIndex((current) => current + 1);
    }
  };

  return (
    <div className="stack">
      <PageHeading kicker="Recognition Drill" title={detail?.title ?? 'Quiz'} />

      <QueryState
        isLoading={quiz.isLoading}
        isError={quiz.isError}
        error={quiz.error}
        loadingLabel="Shuffling the questions…"
      >
        {detail ? (
          finished ? (
            <Panel title="Session summary" eyebrow="Quiz complete">
              <p>
                {correctCount} / {detail.questions.length} correct
              </p>
              <div className="command-row" style={{ marginTop: 'var(--space-3)' }}>
                <Link className="command-btn command-btn--pine" to="/learn">
                  Back to the bench
                </Link>
              </div>
            </Panel>
          ) : question ? (
            <Panel
              title={`Question ${index + 1} of ${detail.questions.length}`}
              eyebrow={detail.quiz_type.replaceAll('_', ' ')}
            >
              <div className="chip-row" style={{ marginBottom: 'var(--space-3)' }}>
                {detail.concepts.map((concept) => (
                  <PatternChip key={concept} pattern={concept} />
                ))}
              </div>
              <p style={{ whiteSpace: 'pre-wrap' }}>{question.prompt}</p>
              <div className="stack" style={{ marginTop: 'var(--space-3)' }}>
                {question.choices.map((choice) => (
                  <button
                    key={choice}
                    className="command-btn"
                    type="button"
                    disabled={Boolean(feedback) || answer.isPending}
                    onClick={() => choose(choice)}
                  >
                    {choice}
                  </button>
                ))}
              </div>
              {feedback ? (
                <div className="stack" style={{ marginTop: 'var(--space-3)' }}>
                  <p>{feedback.correct ? 'Correct.' : 'Not this time.'}</p>
                  <p className="muted">{feedback.explanation}</p>
                  <div className="command-row">
                    <button
                      className="command-btn command-btn--pine"
                      type="button"
                      onClick={advance}
                    >
                      {isLast ? 'Finish quiz' : 'Next question'}
                    </button>
                  </div>
                </div>
              ) : null}
              {answer.isError ? (
                <p className="muted">Could not record the answer. Try again.</p>
              ) : null}
            </Panel>
          ) : null
        ) : null}
      </QueryState>
    </div>
  );
}
