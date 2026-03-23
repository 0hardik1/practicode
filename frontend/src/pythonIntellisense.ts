import type { Monaco } from "@monaco-editor/react";

import { api } from "./api/client";


let isPythonCompletionProviderRegistered = false;
let isPythonHoverProviderRegistered = false;
let activeProblemId: string | null = null;


function completionKind(monaco: Monaco, kind: string) {
  const map: Record<string, number> = {
    class: monaco.languages.CompletionItemKind.Class,
    file: monaco.languages.CompletionItemKind.File,
    function: monaco.languages.CompletionItemKind.Function,
    keyword: monaco.languages.CompletionItemKind.Keyword,
    module: monaco.languages.CompletionItemKind.Module,
    parameter: monaco.languages.CompletionItemKind.Variable,
    property: monaco.languages.CompletionItemKind.Property,
    text: monaco.languages.CompletionItemKind.Text,
    variable: monaco.languages.CompletionItemKind.Variable,
  };
  return map[kind] ?? monaco.languages.CompletionItemKind.Text;
}


function problemRelativePath(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length <= 1) {
    return parts[0] ?? "solution.py";
  }
  return parts.slice(1).join("/");
}


export function setPythonIntellisenseProblem(problemId: string | null) {
  activeProblemId = problemId;
}


export function ensurePythonIntellisense(monaco: Monaco) {
  if (!isPythonCompletionProviderRegistered) {
    monaco.languages.registerCompletionItemProvider("python", {
      triggerCharacters: ["."],
      async provideCompletionItems(model, position) {
        if (!activeProblemId) {
          return { suggestions: [] };
        }

        try {
          const response = await api.getPythonCompletions(
            activeProblemId,
            model.getValue(),
            problemRelativePath(model.uri.path),
            {
              line: position.lineNumber,
              column: position.column,
            },
          );
          const word = model.getWordUntilPosition(position);
          const range = new monaco.Range(
            position.lineNumber,
            word.startColumn,
            position.lineNumber,
            word.endColumn,
          );

          return {
            suggestions: response.items.map((item) => ({
              label: item.label,
              kind: completionKind(monaco, item.kind),
              detail: item.detail ?? undefined,
              documentation: item.documentation
                ? { value: item.documentation }
                : undefined,
              insertText: item.insert_text ?? item.label,
              range,
              sortText: item.sort_text ?? undefined,
              additionalTextEdits: item.additional_text_edits.map((edit) => ({
                range: new monaco.Range(
                  edit.start_line,
                  edit.start_column,
                  edit.end_line,
                  edit.end_column,
                ),
                text: edit.text,
              })),
            })),
          };
        } catch {
          return { suggestions: [] };
        }
      },
    });

    isPythonCompletionProviderRegistered = true;
  }

  if (!isPythonHoverProviderRegistered) {
    monaco.languages.registerHoverProvider("python", {
      async provideHover(model, position) {
        if (!activeProblemId) {
          return null;
        }

        const word = model.getWordAtPosition(position);
        if (!word) {
          return null;
        }

        try {
          const response = await api.getPythonHover(
            activeProblemId,
            model.getValue(),
            problemRelativePath(model.uri.path),
            {
              line: position.lineNumber,
              column: position.column,
            },
          );
          if (response.contents.length === 0) {
            return null;
          }

          return {
            range: new monaco.Range(
              position.lineNumber,
              word.startColumn,
              position.lineNumber,
              word.endColumn,
            ),
            contents: response.contents.map((value) => ({ value })),
          };
        } catch {
          return null;
        }
      },
    });

    isPythonHoverProviderRegistered = true;
  }
}
