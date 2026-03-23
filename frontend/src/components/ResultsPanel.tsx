import type { SubmissionDetail } from "../types";

type ResultTab = "tests" | "console" | "history";

interface ResultsPanelProps {
  activeSubmission: SubmissionDetail | null;
  activeTab: ResultTab;
  executionError: string | null;
  history: SubmissionDetail[];
  liveStatus: string | null;
  onSelectHistory: (submission: SubmissionDetail) => void;
  onTabChange: (tab: ResultTab) => void;
}

function resultStatusClass(status: string) {
  if (status === "passed") {
    return "result-pass";
  }
  if (status === "running" || status === "queued") {
    return "result-running";
  }
  return "result-fail";
}

function submissionModeLabel(submission: SubmissionDetail) {
  if (submission.is_submit) {
    return "Full submit";
  }
  return submission.results?.[0]?.test_id === "__program_output__" ? "Program run" : "Visible tests";
}

function historyActionLabel(submission: SubmissionDetail) {
  if (submission.is_submit) {
    return "Submit";
  }
  return submission.results?.[0]?.test_id === "__program_output__" ? "Run" : "Run Tests";
}

export function ResultsPanel({
  activeSubmission,
  activeTab,
  executionError,
  history,
  liveStatus,
  onSelectHistory,
  onTabChange,
}: ResultsPanelProps) {
  return (
    <section className="panel results-panel">
      <header className="results-header">
        <div className="panel-heading-copy">
          <p className="panel-eyebrow">Execution</p>
          <h2>Test Results</h2>
        </div>
      </header>

      <div className="tab-strip">
        <button
          className={activeTab === "tests" ? "tab-active" : ""}
          onClick={() => onTabChange("tests")}
          type="button"
        >
          Tests
        </button>
        <button
          className={activeTab === "console" ? "tab-active" : ""}
          onClick={() => onTabChange("console")}
          type="button"
        >
          Console
        </button>
        <button
          className={activeTab === "history" ? "tab-active" : ""}
          onClick={() => onTabChange("history")}
          type="button"
        >
          History
        </button>
      </div>

      {executionError ? <div className="error-banner">{executionError}</div> : null}

      {!activeSubmission && !executionError ? (
        <div className="panel-empty">
          {liveStatus ? `Submission is ${liveStatus}...` : "Run your code to see results here."}
        </div>
      ) : null}

      {activeSubmission && activeTab === "tests" ? (
        <div className="results-scroll">
          <div className="submission-summary">
            <span className={`summary-pill ${resultStatusClass(activeSubmission.status)}`}>
              {activeSubmission.status}
            </span>
            <span>{submissionModeLabel(activeSubmission)}</span>
            <span>{activeSubmission.duration_ms ?? 0} ms</span>
          </div>
          {(activeSubmission.results ?? []).map((result) => (
            <article className="result-card" key={result.test_id}>
              <div className="result-card-top">
                <strong>{result.name}</strong>
                <span className={result.passed ? "result-pass" : "result-fail"}>
                  {result.passed ? "Passed" : "Failed"}
                </span>
              </div>
              <p>{result.message || result.error || "No message returned."}</p>
              <div className="result-grid">
                <div>
                  <span>Expected</span>
                  <pre>{JSON.stringify(result.expected, null, 2)}</pre>
                </div>
                <div>
                  <span>Actual</span>
                  <pre>{JSON.stringify(result.actual, null, 2)}</pre>
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {activeSubmission && activeTab === "console" ? (
        <div className="console-grid">
          <article>
            <div className="console-title">Stdout</div>
            <pre>{activeSubmission.stdout || "No stdout captured."}</pre>
          </article>
          <article>
            <div className="console-title">Stderr</div>
            <pre>{activeSubmission.stderr || "No stderr captured."}</pre>
          </article>
        </div>
      ) : null}

      {activeTab === "history" ? (
        <div className="history-list">
          {history.length === 0 ? (
            <div className="panel-empty">No submissions yet for this problem.</div>
          ) : (
            history.map((submission) => (
              <button
                className="history-card"
                key={submission.id}
                onClick={() => onSelectHistory(submission)}
                type="button"
              >
                <div>
                  <strong>{historyActionLabel(submission)}</strong>
                  <span>{new Date(submission.created_at).toLocaleString()}</span>
                </div>
                <span className={`summary-pill ${resultStatusClass(submission.status)}`}>
                  {submission.status}
                </span>
              </button>
            ))
          )}
        </div>
      ) : null}
    </section>
  );
}
