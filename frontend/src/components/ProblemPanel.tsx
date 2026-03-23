import type { ReactNode } from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ProblemDetail } from "../types";

type ProblemTab = "description" | "api-docs" | "files";

interface ProblemPanelProps {
  problem: ProblemDetail | null;
  activeTab: ProblemTab;
  filesTab: ReactNode;
  onTabChange: (tab: ProblemTab) => void;
}

function renderJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export function ProblemPanel({
  problem,
  activeTab,
  filesTab,
  onTabChange,
}: ProblemPanelProps) {
  if (!problem) {
    return (
      <section className="panel problem-panel">
        <div className="panel-empty">Loading problem workspace...</div>
      </section>
    );
  }

  return (
    <section className="panel problem-panel">
      <header className="panel-header">
        <div className="panel-heading-copy">
          <p className="panel-eyebrow">Problem Workspace</p>
          <h2>
            {activeTab === "description"
              ? "Description & Samples"
              : activeTab === "api-docs"
                ? "API Reference"
                : "Files & Assets"}
          </h2>
        </div>
        <div className="meta-strip">
          <span>{problem.time_limit_seconds}s</span>
          <span>{problem.memory_limit_mb}MB</span>
        </div>
      </header>

      <div className="tab-strip">
        <button
          className={activeTab === "description" ? "tab-active" : ""}
          onClick={() => onTabChange("description")}
          type="button"
        >
          Description
        </button>
        <button
          className={activeTab === "api-docs" ? "tab-active" : ""}
          onClick={() => onTabChange("api-docs")}
          type="button"
        >
          API Docs
        </button>
        <button
          className={activeTab === "files" ? "tab-active" : ""}
          onClick={() => onTabChange("files")}
          type="button"
        >
          Files
        </button>
      </div>

      <div className={activeTab === "files" ? "problem-scroll problem-scroll-files" : "problem-scroll"}>
        {activeTab === "description" ? (
          <>
            <article className="markdown-shell">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {problem.description}
              </ReactMarkdown>
            </article>

            <section className="sample-section">
              <div className="section-heading">
                <h3>Visible Test Cases</h3>
                <span>{problem.visible_tests.length} loaded</span>
              </div>
              <div className="sample-grid">
                {problem.visible_tests.map((testCase) => (
                  <article key={testCase.id} className="sample-card">
                    <div className="sample-card-header">
                      <strong>{testCase.name}</strong>
                      <span>{testCase.validation_type}</span>
                    </div>
                    <div>
                      <p>Input</p>
                      <pre>{renderJson(testCase.input)}</pre>
                    </div>
                    <div>
                      <p>Expected</p>
                      <pre>{renderJson(testCase.expected)}</pre>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </>
        ) : activeTab === "api-docs" ? (
          <article className="markdown-shell">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {problem.api_docs || "No API docs were provided for this problem."}
            </ReactMarkdown>
          </article>
        ) : (
          filesTab
        )}
      </div>
    </section>
  );
}
