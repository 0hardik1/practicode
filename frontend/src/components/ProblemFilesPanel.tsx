import { useMemo, useState } from "react";

import type { ProblemFileNode } from "../types";

interface ProblemFilesPanelProps {
  root: ProblemFileNode | null;
  selectedPath: string | null;
  error: string | null;
  onSelectNode: (node: ProblemFileNode) => void;
  onCreateNode: (kind: "file" | "directory", name: string, parentPath: string | null) => void;
}

function dirname(path: string | null) {
  if (!path) {
    return null;
  }
  const parts = path.split("/");
  parts.pop();
  return parts.length > 0 ? parts.join("/") : null;
}

function findNodeByPath(node: ProblemFileNode, targetPath: string | null): ProblemFileNode | null {
  if (targetPath === null) {
    return null;
  }
  if (node.path === targetPath) {
    return node;
  }
  for (const child of node.children) {
    const result = findNodeByPath(child, targetPath);
    if (result) {
      return result;
    }
  }
  return null;
}

function FileIcon() {
  return (
    <svg aria-hidden="true" className="tree-icon" viewBox="0 0 16 16">
      <path
        d="M4 1.5h4.5L12.5 5v9.5H4z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M8.5 1.5V5H12" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function FolderIcon() {
  return (
    <svg aria-hidden="true" className="tree-icon" viewBox="0 0 16 16">
      <path
        d="M1.5 4.5h4l1.4 1.5H14v6.5H1.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M1.5 4.5v-1h3.3l1.1 1.2" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function NewFileIcon() {
  return (
    <svg aria-hidden="true" className="toolbar-icon" viewBox="0 0 16 16">
      <path
        d="M4 1.5h4.5L12.5 5v9.5H4z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M8.5 1.5V5H12" fill="none" stroke="currentColor" strokeWidth="1.2" />
      <path d="M8 7v4M6 9h4" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function NewFolderIcon() {
  return (
    <svg aria-hidden="true" className="toolbar-icon" viewBox="0 0 16 16">
      <path
        d="M1.5 4.5h4l1.4 1.5H14v6.5H1.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      <path d="M10.5 8v3M9 9.5h3" fill="none" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function FileTree({
  node,
  depth,
  selectedPath,
  onSelectNode,
}: {
  node: ProblemFileNode;
  depth: number;
  selectedPath: string | null;
  onSelectNode: (node: ProblemFileNode) => void;
}) {
  const isSelected = selectedPath === node.path;
  const sharedStyle = { paddingLeft: `${depth * 12 + 12}px` };

  if (node.kind === "directory") {
    return (
      <div className="file-group">
        <button
          className={`file-directory ${isSelected ? "file-node-active" : ""}`}
          onClick={() => onSelectNode(node)}
          style={sharedStyle}
          type="button"
        >
          <span className="file-node-name">
            <FolderIcon />
            {node.name}
          </span>
          <span>{node.children.length}</span>
        </button>
        {node.children.map((child) => (
          <FileTree
            depth={depth + 1}
            key={child.path || child.name}
            node={child}
            onSelectNode={onSelectNode}
            selectedPath={selectedPath}
          />
        ))}
      </div>
    );
  }

  return (
    <button
      className={`file-node ${isSelected ? "file-node-active" : ""}`}
      onClick={() => onSelectNode(node)}
      style={sharedStyle}
      type="button"
    >
      <span className="file-node-name">
        <FileIcon />
        {node.name}
      </span>
      <span>{node.editable ? "text" : "asset"}</span>
    </button>
  );
}

export function ProblemFilesPanel({
  root,
  selectedPath,
  error,
  onSelectNode,
  onCreateNode,
}: ProblemFilesPanelProps) {
  const [createKind, setCreateKind] = useState<"file" | "directory" | null>(null);
  const [createName, setCreateName] = useState("");
  const selectedNode = useMemo(
    () => (root ? findNodeByPath(root, selectedPath) : null),
    [root, selectedPath],
  );
  const createParentPath =
    selectedNode?.kind === "directory"
      ? selectedNode.path || null
      : dirname(selectedPath);

  return (
    <div className="files-tab-shell">
      <div className="files-toolbar">
        <div className="files-toolbar-actions">
          <button
            className={`toolbar-action ${createKind === "file" ? "tab-active" : ""}`}
            onClick={() => {
              setCreateKind("file");
              setCreateName("");
            }}
            type="button"
          >
            <NewFileIcon />
            <span>New File</span>
          </button>
          <button
            className={`toolbar-action ${createKind === "directory" ? "tab-active" : ""}`}
            onClick={() => {
              setCreateKind("directory");
              setCreateName("");
            }}
            type="button"
          >
            <NewFolderIcon />
            <span>New Folder</span>
          </button>
        </div>
        <div className="files-toolbar-target">
          Parent: <strong>{createParentPath || "/"}</strong>
        </div>
      </div>

      {createKind ? (
        <div className="create-node-bar">
          <input
            onChange={(event) => setCreateName(event.target.value)}
            placeholder={createKind === "file" ? "new_file.py" : "fixtures"}
            value={createName}
          />
          <button
            className="primary-button"
            onClick={() => {
              const trimmedName = createName.trim();
              if (!trimmedName) {
                return;
              }
              onCreateNode(createKind, trimmedName, createParentPath);
              setCreateKind(null);
              setCreateName("");
            }}
            type="button"
          >
            Create
          </button>
          <button
            className="ghost-button"
            onClick={() => {
              setCreateKind(null);
              setCreateName("");
            }}
            type="button"
          >
            Cancel
          </button>
        </div>
      ) : null}

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="files-hint-card">
        <strong>
          {selectedNode?.kind === "file"
            ? `${selectedNode.name} opens in the Code panel`
            : "Open files in the Code panel"}
        </strong>
        <p>
          Click any file to open it as a tab on the right. Select a folder to choose where new
          files or directories should be created.
        </p>
      </div>

      <div className="file-tree file-tree-standalone">
        {root ? (
          <FileTree
            depth={0}
            node={root}
            onSelectNode={onSelectNode}
            selectedPath={selectedPath}
          />
        ) : (
          <div className="panel-empty">Loading problem files...</div>
        )}
      </div>
    </div>
  );
}
