import type { Monaco } from "@monaco-editor/react";

export function definePractiCodeTheme(monaco: Monaco) {
  monaco.editor.defineTheme("practicode-vscode", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "comment", foreground: "6a9955" },
      { token: "keyword", foreground: "c586c0" },
      { token: "number", foreground: "b5cea8" },
      { token: "string", foreground: "ce9178" },
      { token: "type.identifier", foreground: "4ec9b0" },
    ],
    colors: {
      "editor.background": "#11161d",
      "editorLineNumber.foreground": "#53627a",
      "editorLineNumber.activeForeground": "#9db0cc",
      "editorCursor.foreground": "#5ec4ff",
      "editor.selectionBackground": "#264f78",
      "editor.inactiveSelectionBackground": "#213248",
      "editorIndentGuide.background1": "#213248",
      "editorIndentGuide.activeBackground1": "#31577c",
    },
  });
}

