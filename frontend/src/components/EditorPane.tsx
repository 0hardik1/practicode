import Editor from "@monaco-editor/react";

import { definePractiCodeTheme } from "../editorTheme";

export interface EditorTabView {
  id: string;
  label: string;
  kind: "solution" | "file";
  content: string;
  language: string;
  editable: boolean;
  dirty: boolean;
  mimeType?: string | null;
  base64Content?: string | null;
  isBinary?: boolean;
}

interface EditorPaneProps {
  activeTabId: string;
  fileError: string | null;
  isBusy: boolean;
  isFileLoading: boolean;
  isFileSaving: boolean;
  liveStatus: string | null;
  onActiveTabChange: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
  onCodeChange: (value: string) => void;
  onRunCode: () => void;
  onRun: () => void;
  onSaveFile: () => void;
  onSubmit: () => void;
  tabs: EditorTabView[];
}

function previewSource(tab: EditorTabView) {
  if (!tab.mimeType?.startsWith("image/") || !tab.base64Content) {
    return null;
  }
  return `data:${tab.mimeType};base64,${tab.base64Content}`;
}

export function EditorPane({
  activeTabId,
  fileError,
  isBusy,
  isFileLoading,
  isFileSaving,
  liveStatus,
  onActiveTabChange,
  onCloseTab,
  onCodeChange,
  onRunCode,
  onRun,
  onSaveFile,
  onSubmit,
  tabs,
}: EditorPaneProps) {
  const activeTab = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];
  const imagePreview = activeTab ? previewSource(activeTab) : null;

  if (!activeTab) {
    return (
      <section className="panel editor-panel">
        <div className="panel-empty">Loading editor...</div>
      </section>
    );
  }

  return (
    <section className="panel editor-panel">
      <header className="editor-toolbar">
        <div>
          <p className="panel-eyebrow">Code</p>
          <h2>{activeTab.kind === "solution" ? "Python 3.12" : activeTab.label}</h2>
        </div>
        <div className="editor-toolbar-actions">
          <span className={`status-chip ${activeTab.kind === "solution" && liveStatus ? "status-active" : ""}`}>
            {activeTab.kind === "solution"
              ? liveStatus ?? "idle"
              : activeTab.editable
                ? activeTab.dirty
                  ? "modified"
                  : "file"
                : "read only"}
          </span>
          {activeTab.kind === "solution" ? (
            <>
              <button className="ghost-button editor-secondary-button" onClick={onRunCode} disabled={isBusy} type="button">
                Run
              </button>
              <button className="ghost-button" onClick={onRun} disabled={isBusy} type="button">
                Run Tests
              </button>
              <button className="primary-button" onClick={onSubmit} disabled={isBusy} type="button">
                Submit
              </button>
            </>
          ) : activeTab.editable ? (
            <button className="primary-button" onClick={onSaveFile} disabled={isFileSaving || !activeTab.dirty} type="button">
              {isFileSaving ? "Saving..." : "Save File"}
            </button>
          ) : null}
        </div>
      </header>

      <div className="editor-tab-strip">
        {tabs.map((tab) => (
          <div
            className={`editor-tab ${tab.id === activeTabId ? "editor-tab-active" : ""}`}
            key={tab.id}
          >
            <button
              className="editor-tab-button"
              onClick={() => onActiveTabChange(tab.id)}
              type="button"
            >
              <span className="editor-tab-label">
                {tab.label}
                {tab.dirty ? " •" : ""}
              </span>
            </button>
            {tab.kind === "file" ? (
              <button
                aria-label={`Close ${tab.label}`}
                className="editor-tab-close"
                onClick={(event) => {
                  event.stopPropagation();
                  onCloseTab(tab.id);
                }}
                type="button"
              >
                ×
              </button>
            ) : null}
          </div>
        ))}
      </div>

      {fileError && activeTab.kind === "file" ? <div className="error-banner">{fileError}</div> : null}

      <div className="editor-frame">
        {isFileLoading && activeTab.kind === "file" ? (
          <div className="panel-empty">Loading file...</div>
        ) : imagePreview ? (
          <div className="editor-preview">
            <img alt={activeTab.label} className="editor-preview-image" src={imagePreview} />
          </div>
        ) : activeTab.isBinary && !activeTab.editable ? (
          <div className="panel-empty">This file cannot be edited in the browser.</div>
        ) : (
          <Editor
            beforeMount={definePractiCodeTheme}
            defaultLanguage="python"
            height="100%"
            language={activeTab.language}
            onChange={(value) => onCodeChange(value ?? "")}
            options={{
              automaticLayout: true,
              fontFamily: "'IBM Plex Mono', 'SFMono-Regular', monospace",
              fontLigatures: true,
              fontSize: 14,
              minimap: { enabled: false },
              padding: { top: 18 },
              readOnly: !activeTab.editable,
              scrollBeyondLastLine: false,
              scrollbar: {
                alwaysConsumeMouseWheel: false,
              },
              smoothScrolling: true,
              tabSize: 4,
            }}
            path={`editor:${activeTab.id}`}
            theme="practicode-vscode"
            value={activeTab.content}
          />
        )}
      </div>
    </section>
  );
}
