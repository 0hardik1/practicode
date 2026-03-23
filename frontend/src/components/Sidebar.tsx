import { useDeferredValue } from "react";

import type { ProblemSummary } from "../types";

interface SidebarProps {
  problems: ProblemSummary[];
  selectedProblemId: string | null;
  solvedProblemIds: Set<string>;
  searchValue: string;
  onSearchChange: (value: string) => void;
  onSelectProblem: (problemId: string) => void;
}

function difficultyLabel(difficulty: ProblemSummary["difficulty"]) {
  if (difficulty === "easy") {
    return "difficulty-easy";
  }
  if (difficulty === "medium") {
    return "difficulty-medium";
  }
  return "difficulty-hard";
}

export function Sidebar({
  problems,
  selectedProblemId,
  solvedProblemIds,
  searchValue,
  onSearchChange,
  onSelectProblem,
}: SidebarProps) {
  const deferredSearch = useDeferredValue(searchValue);
  const filteredProblems = problems.filter((problem) => {
    const query = deferredSearch.trim().toLowerCase();
    if (!query) {
      return true;
    }
    return (
      problem.title.toLowerCase().includes(query) ||
      problem.tags.some((tag) => tag.toLowerCase().includes(query))
    );
  });

  return (
    <aside className="sidebar">
      <div className="brand-card">
        <div className="brand-mark">PC</div>
        <div>
          <p className="brand-eyebrow">Local Assessment Lab</p>
          <h1>PractiCode</h1>
        </div>
      </div>

      <label className="search-shell">
        <span>Search problems</span>
        <input
          value={searchValue}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="oauth, image, api..."
        />
      </label>

      <div className="problem-list">
        {filteredProblems.map((problem) => {
          const isActive = selectedProblemId === problem.id;
          const isSolved = solvedProblemIds.has(problem.id);
          return (
            <button
              key={problem.id}
              className={`problem-card ${isActive ? "problem-card-active" : ""}`}
              onClick={() => onSelectProblem(problem.id)}
              type="button"
            >
              <div className="problem-card-top">
                <span className="problem-card-id">{problem.id.slice(0, 3)}</span>
                <span className={`difficulty-pill ${difficultyLabel(problem.difficulty)}`}>
                  {problem.difficulty}
                </span>
              </div>
              <div className="problem-card-title-row">
                <strong>{problem.title}</strong>
                {isSolved ? <span className="solved-pill">Solved</span> : null}
              </div>
              <div className="problem-card-tags">
                {problem.tags.slice(0, 3).map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

