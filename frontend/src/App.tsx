import type { CSSProperties } from "react";
import { startTransition, useEffect, useRef, useState } from "react";

import { api } from "./api/client";
import { EditorPane, type EditorTabView } from "./components/EditorPane";
import { ProblemFilesPanel } from "./components/ProblemFilesPanel";
import { ProblemPanel } from "./components/ProblemPanel";
import { ResultsPanel } from "./components/ResultsPanel";
import { Sidebar } from "./components/Sidebar";
import { startPaneResize } from "./paneResize";
import type {
  ProblemDetail,
  ProblemFileNode,
  ProblemSummary,
  SubmissionDetail,
} from "./types";

const TERMINAL_STATUSES = new Set(["passed", "failed", "error", "timeout"]);
const SOLUTION_TAB_ID = "__solution__";

type ProblemTab = "description" | "api-docs" | "files";
type ResultTab = "tests" | "console" | "history";

interface OpenFileTab {
  path: string;
  name: string;
  draft: string;
  original: string;
  editable: boolean;
  isBinary: boolean;
  mimeType?: string | null;
  base64Content?: string | null;
}

function storageKey(problemId: string) {
  return `practicode:${problemId}:python`;
}

function sleep(delayMs: number) {
  return new Promise((resolve) => window.setTimeout(resolve, delayMs));
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong while contacting the API.";
}

function languageForFileName(fileName: string) {
  const lowerName = fileName.toLowerCase();
  if (lowerName.endsWith(".py")) {
    return "python";
  }
  if (lowerName.endsWith(".json")) {
    return "json";
  }
  if (lowerName.endsWith(".yml") || lowerName.endsWith(".yaml")) {
    return "yaml";
  }
  if (lowerName.endsWith(".svg") || lowerName.endsWith(".xml") || lowerName.endsWith(".html")) {
    return "xml";
  }
  if (lowerName.endsWith(".md")) {
    return "markdown";
  }
  if (lowerName.endsWith(".txt")) {
    return "plaintext";
  }
  return "plaintext";
}

function SidebarToggleIcon() {
  return (
    <svg aria-hidden="true" className="toolbar-icon" viewBox="0 0 16 16">
      <path
        d="M2 3.5h12M2 8h12M2 12.5h12"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.4"
      />
    </svg>
  );
}

export default function App() {
  const [problems, setProblems] = useState<ProblemSummary[]>([]);
  const [selectedProblemId, setSelectedProblemId] = useState<string | null>(null);
  const [selectedProblem, setSelectedProblem] = useState<ProblemDetail | null>(null);
  const [problemTab, setProblemTab] = useState<ProblemTab>("description");
  const [resultsTab, setResultsTab] = useState<ResultTab>("tests");
  const [history, setHistory] = useState<SubmissionDetail[]>([]);
  const [activeSubmission, setActiveSubmission] = useState<SubmissionDetail | null>(null);
  const [code, setCode] = useState("");
  const [loadingText, setLoadingText] = useState("Loading problems...");
  const [isBusy, setIsBusy] = useState(false);
  const [liveStatus, setLiveStatus] = useState<string | null>(null);
  const [searchValue, setSearchValue] = useState("");
  const [executionError, setExecutionError] = useState<string | null>(null);
  const [fileTree, setFileTree] = useState<ProblemFileNode | null>(null);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [isFileLoading, setIsFileLoading] = useState(false);
  const [isFileSaving, setIsFileSaving] = useState(false);
  const [openFileTabs, setOpenFileTabs] = useState<Record<string, OpenFileTab>>({});
  const [openFileOrder, setOpenFileOrder] = useState<string[]>([]);
  const [activeEditorTabId, setActiveEditorTabId] = useState<string>(SOLUTION_TAB_ID);
  const [isSidebarHidden, setIsSidebarHidden] = useState(false);
  const [isProblemPanelHidden, setIsProblemPanelHidden] = useState(false);
  const [workspaceLeftSize, setWorkspaceLeftSize] = useState(34);
  const [workspaceMainLeftSize, setWorkspaceMainLeftSize] = useState(58);
  const workspaceGridRef = useRef<HTMLElement | null>(null);
  const workspaceMainRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProblems() {
      try {
        const nextProblems = await api.listProblems();
        if (cancelled) {
          return;
        }

        setProblems(nextProblems);
        if (!selectedProblemId && nextProblems.length > 0) {
          setSelectedProblemId(nextProblems[0].id);
        }
      } catch (error) {
        if (!cancelled) {
          setLoadingText(getErrorMessage(error));
        }
      }
    }

    void loadProblems();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedProblemId) {
      return;
    }

    const problemId = selectedProblemId;
    let cancelled = false;

    async function loadProblem() {
      try {
        const nextProblem = await api.getProblem(problemId);
        if (cancelled) {
          return;
        }

        setSelectedProblem(nextProblem);
        setProblemTab("description");
        setExecutionError(null);
        setLiveStatus(null);
        setOpenFileTabs({});
        setOpenFileOrder([]);
        setActiveEditorTabId(SOLUTION_TAB_ID);

        const savedCode = window.localStorage.getItem(storageKey(nextProblem.id));
        setCode(savedCode ?? nextProblem.starter_code.python ?? "");

        const previousSubmission =
          history.find((submission) => submission.problem_id === nextProblem.id) ?? null;
        setActiveSubmission(previousSubmission);
      } catch (error) {
        if (!cancelled) {
          setLoadingText(getErrorMessage(error));
        }
      }
    }

    void loadProblem();
    return () => {
      cancelled = true;
    };
  }, [selectedProblemId]);

  useEffect(() => {
    if (!selectedProblemId) {
      return;
    }

    const problemId = selectedProblemId;
    let cancelled = false;

    async function loadProblemFiles() {
      setFileError(null);
      setIsFileLoading(true);
      setFileTree(null);
      setSelectedFilePath(null);

      try {
        const treeResponse = await api.listProblemFiles(problemId);
        if (cancelled) {
          return;
        }

        setFileTree(treeResponse.root);
        setSelectedFilePath(treeResponse.root.path);
      } catch (error) {
        if (!cancelled) {
          setFileError(getErrorMessage(error));
        }
      } finally {
        if (!cancelled) {
          setIsFileLoading(false);
        }
      }
    }

    void loadProblemFiles();
    return () => {
      cancelled = true;
    };
  }, [selectedProblemId]);

  useEffect(() => {
    if (!selectedProblemId) {
      return;
    }

    const previousSubmission =
      history.find((submission) => submission.problem_id === selectedProblemId) ?? null;
    setActiveSubmission(previousSubmission);
  }, [history, selectedProblemId]);

  useEffect(() => {
    if (!selectedProblem) {
      return;
    }
    window.localStorage.setItem(storageKey(selectedProblem.id), code);
  }, [code, selectedProblem]);

  async function trackSubmission(submissionId: string) {
    let latestSubmission: SubmissionDetail | null = null;

    while (true) {
      latestSubmission = await api.getSubmission(submissionId);
      setActiveSubmission(latestSubmission);
      setLiveStatus(latestSubmission.status);
      if (TERMINAL_STATUSES.has(latestSubmission.status)) {
        setHistory((current) => [
          latestSubmission!,
          ...current.filter((submission) => submission.id !== latestSubmission!.id),
        ]);
        return latestSubmission;
      }
      await sleep(1200);
    }
  }

  async function handleExecute(mode: "execute" | "run" | "submit") {
    if (!selectedProblem) {
      return;
    }

    setIsBusy(true);
    setExecutionError(null);
    setResultsTab(mode === "execute" ? "console" : "tests");
    setLiveStatus("queued");

    try {
      const queued =
        mode === "execute"
          ? await api.executeProblem(
              selectedProblem.id,
              code,
              selectedProblem.visible_tests[0]?.input ?? {},
            )
          : mode === "run"
            ? await api.runProblem(selectedProblem.id, code)
            : await api.submitProblem(selectedProblem.id, code);
      const latest = await trackSubmission(queued.id);
      if (
        mode !== "execute" &&
        (latest.status === "failed" || latest.status === "error" || latest.status === "timeout")
      ) {
        setResultsTab("tests");
      }
    } catch (error) {
      setExecutionError(getErrorMessage(error));
      setLiveStatus(null);
    } finally {
      setIsBusy(false);
    }
  }

  async function loadFileContent(problemId: string, path: string) {
    const existingTab = openFileTabs[path];
    if (existingTab) {
      setSelectedFilePath(path);
      setActiveEditorTabId(path);
      return;
    }

    setFileError(null);
    setIsFileLoading(true);

    try {
      const fileResponse = await api.getProblemFileContent(problemId, path);
      setOpenFileTabs((current) => ({
        ...current,
        [path]: {
          path: fileResponse.path,
          name: fileResponse.name,
          draft: fileResponse.text_content ?? "",
          original: fileResponse.text_content ?? "",
          editable: fileResponse.editable,
          isBinary: fileResponse.is_binary,
          mimeType: fileResponse.mime_type,
          base64Content: fileResponse.base64_content ?? null,
        },
      }));
      setOpenFileOrder((current) => (current.includes(path) ? current : [...current, path]));
      setActiveEditorTabId(path);
    } catch (error) {
      setSelectedFilePath(path);
      setFileError(getErrorMessage(error));
    } finally {
      setIsFileLoading(false);
    }
  }

  async function handleSelectNode(node: ProblemFileNode) {
    if (!selectedProblem) {
      return;
    }

    if (node.kind === "directory") {
      setSelectedFilePath(node.path);
      setFileError(null);
      setIsFileLoading(false);
      return;
    }

    setSelectedFilePath(node.path);
    await loadFileContent(selectedProblem.id, node.path);
  }

  async function handleCreateNode(
    kind: "file" | "directory",
    name: string,
    parentPath: string | null,
  ) {
    if (!selectedProblem) {
      return;
    }

    setProblemTab("files");
    setFileError(null);

    try {
      const created = await api.createProblemNode(selectedProblem.id, name, kind, parentPath);
      const nextTree = await api.listProblemFiles(selectedProblem.id);
      setFileTree(nextTree.root);

      if (created.kind === "directory") {
        setSelectedFilePath(created.path);
        return;
      }

      await loadFileContent(selectedProblem.id, created.path);
    } catch (error) {
      setFileError(getErrorMessage(error));
    }
  }

  async function handleSaveFile() {
    if (!selectedProblem || activeEditorTabId === SOLUTION_TAB_ID) {
      return;
    }

    const activeFile = openFileTabs[activeEditorTabId];
    if (!activeFile || !activeFile.editable) {
      return;
    }

    setIsFileSaving(true);
    setFileError(null);

    try {
      const savedFile = await api.saveProblemFile(
        selectedProblem.id,
        activeFile.path,
        activeFile.draft,
      );
      const [nextProblem, nextProblems, nextTree] = await Promise.all([
        api.getProblem(selectedProblem.id),
        api.listProblems(),
        api.listProblemFiles(selectedProblem.id),
      ]);

      setSelectedProblem(nextProblem);
      setProblems(nextProblems);
      setFileTree(nextTree.root);
      setSelectedFilePath(savedFile.path);
      setOpenFileTabs((current) => ({
        ...current,
        [savedFile.path]: {
          path: savedFile.path,
          name: savedFile.name,
          draft: savedFile.text_content ?? "",
          original: savedFile.text_content ?? "",
          editable: savedFile.editable,
          isBinary: savedFile.is_binary,
          mimeType: savedFile.mime_type,
          base64Content: savedFile.base64_content ?? null,
        },
      }));
    } catch (error) {
      setFileError(getErrorMessage(error));
    } finally {
      setIsFileSaving(false);
    }
  }

  function handleEditorChange(value: string) {
    if (activeEditorTabId === SOLUTION_TAB_ID) {
      setCode(value);
      return;
    }

    setOpenFileTabs((current) => {
      const activeFile = current[activeEditorTabId];
      if (!activeFile) {
        return current;
      }
      return {
        ...current,
        [activeEditorTabId]: {
          ...activeFile,
          draft: value,
        },
      };
    });
  }

  function handleSelectEditorTab(tabId: string) {
    setActiveEditorTabId(tabId);
    if (tabId !== SOLUTION_TAB_ID) {
      setSelectedFilePath(tabId);
    }
  }

  function handleCloseEditorTab(tabId: string) {
    setOpenFileTabs((current) => {
      const nextTabs = { ...current };
      delete nextTabs[tabId];
      return nextTabs;
    });

    setOpenFileOrder((current) => {
      const closingIndex = current.indexOf(tabId);
      const nextOrder = current.filter((id) => id !== tabId);
      if (activeEditorTabId === tabId) {
        const fallbackTab = nextOrder[Math.max(0, closingIndex - 1)] ?? SOLUTION_TAB_ID;
        setActiveEditorTabId(fallbackTab);
        if (fallbackTab !== SOLUTION_TAB_ID) {
          setSelectedFilePath(fallbackTab);
        }
      }
      return nextOrder;
    });
  }

  const solvedProblemIds = new Set([
    ...history
      .filter((submission) => submission.status === "passed")
      .map((submission) => submission.problem_id),
    ...problems
      .filter((problem) => problem.tags.includes("presolved"))
      .map((problem) => problem.id),
  ]);

  const visibleHistory = selectedProblem
    ? history.filter((submission) => submission.problem_id === selectedProblem.id)
    : [];
  const editorTabs: EditorTabView[] = [
    {
      id: SOLUTION_TAB_ID,
      label: "solution.py",
      kind: "solution",
      content: code,
      language: "python",
      editable: true,
      dirty: false,
    },
    ...openFileOrder
      .map((path) => openFileTabs[path])
      .filter((tab): tab is OpenFileTab => Boolean(tab))
      .map((tab) => ({
        id: tab.path,
        label: tab.name,
        kind: "file" as const,
        content: tab.draft,
        language: languageForFileName(tab.name),
        editable: tab.editable,
        dirty: tab.draft !== tab.original,
        mimeType: tab.mimeType,
        base64Content: tab.base64Content,
        isBinary: tab.isBinary,
      })),
  ];

  return (
    <div className={`app-shell ${isSidebarHidden ? "app-shell-sidebar-hidden" : ""}`}>
      <Sidebar
        onSearchChange={setSearchValue}
        onSelectProblem={(problemId) => {
          startTransition(() => setSelectedProblemId(problemId));
        }}
        problems={problems}
        searchValue={searchValue}
        selectedProblemId={selectedProblemId}
        solvedProblemIds={solvedProblemIds}
      />

      <main className="workspace">
        <header className="workspace-topbar">
          <div className="workspace-topbar-leading">
            <div className="workspace-toggle-row">
              <button
                aria-label={isSidebarHidden ? "Show problem list" : "Hide problem list"}
                aria-pressed={!isSidebarHidden}
                className="ghost-button sidebar-toggle"
                onClick={() => setIsSidebarHidden((current) => !current)}
                type="button"
              >
                <SidebarToggleIcon />
                <span>{isSidebarHidden ? "Show Problems" : "Hide Problems"}</span>
              </button>
              <button
                aria-label={isProblemPanelHidden ? "Show problem workspace" : "Hide problem workspace"}
                aria-pressed={!isProblemPanelHidden}
                className="ghost-button sidebar-toggle"
                onClick={() => setIsProblemPanelHidden((current) => !current)}
                type="button"
              >
                <span>{isProblemPanelHidden ? "Show Workspace" : "Hide Workspace"}</span>
              </button>
            </div>
            <div>
              <p className="panel-eyebrow">Assessment Workspace</p>
              <h1>{selectedProblem?.title ?? "PractiCode"}</h1>
            </div>
          </div>

          <div className="workspace-topbar-meta">
            <span>VSCode-inspired dark mode</span>
            <span>{selectedProblem?.difficulty ?? "select a problem"}</span>
          </div>
        </header>

        {!selectedProblem ? (
          <section className="loading-screen">{loadingText}</section>
        ) : (
          <section
            className={`workspace-grid ${isProblemPanelHidden ? "workspace-grid-problem-hidden" : ""}`}
            ref={workspaceGridRef}
            style={
              {
                "--workspace-left-size": `${workspaceLeftSize}%`,
              } as CSSProperties
            }
          >
            {!isProblemPanelHidden ? (
              <ProblemPanel
                activeTab={problemTab}
                filesTab={
                  <ProblemFilesPanel
                    error={fileError}
                    onCreateNode={(kind, name, parentPath) =>
                      void handleCreateNode(kind, name, parentPath)
                    }
                    onSelectNode={(node) => void handleSelectNode(node)}
                    root={fileTree}
                    selectedPath={selectedFilePath}
                  />
                }
                onTabChange={setProblemTab}
                problem={selectedProblem}
              />
            ) : null}

            {!isProblemPanelHidden ? (
              <div
                className="pane-resizer pane-resizer-horizontal"
                onPointerDown={(event) =>
                  startPaneResize(event, workspaceGridRef.current, "x", setWorkspaceLeftSize, 22, 55)
                }
                role="separator"
                aria-label="Resize workspace columns"
              />
            ) : null}

            <div
              className="workspace-main"
              ref={workspaceMainRef}
              style={{ "--workspace-main-left-size": `${workspaceMainLeftSize}%` } as CSSProperties}
            >
              <EditorPane
                activeTabId={activeEditorTabId}
                fileError={fileError}
                isBusy={isBusy}
                isFileLoading={isFileLoading}
                isFileSaving={isFileSaving}
                liveStatus={liveStatus}
                onActiveTabChange={handleSelectEditorTab}
                onCloseTab={handleCloseEditorTab}
                onCodeChange={handleEditorChange}
                onRunCode={() => void handleExecute("execute")}
                onRun={() => void handleExecute("run")}
                onSaveFile={() => void handleSaveFile()}
                onSubmit={() => void handleExecute("submit")}
                tabs={editorTabs}
              />

              <div
                className="pane-resizer pane-resizer-horizontal"
                onPointerDown={(event) =>
                  startPaneResize(
                    event,
                    workspaceMainRef.current,
                    "x",
                    setWorkspaceMainLeftSize,
                    38,
                    78,
                  )
                }
                role="separator"
                aria-label="Resize code and results panels"
              />

              <ResultsPanel
                activeSubmission={activeSubmission}
                activeTab={resultsTab}
                executionError={executionError}
                history={visibleHistory}
                liveStatus={liveStatus}
                onSelectHistory={(submission) => {
                  setActiveSubmission(submission);
                  setResultsTab("tests");
                }}
                onTabChange={setResultsTab}
              />
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
