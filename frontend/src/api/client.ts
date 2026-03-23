import type {
  ProblemDetail,
  ProblemFileCreateResponse,
  ProblemFileContent,
  ProblemFileTreeResponse,
  ProblemSummary,
  QueuedSubmissionResponse,
  SubmissionDetail,
} from "../types";

const API_ROOT = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  listProblems(): Promise<ProblemSummary[]> {
    return request("/api/problems");
  },
  getProblem(problemId: string): Promise<ProblemDetail> {
    return request(`/api/problems/${problemId}`);
  },
  listProblemFiles(problemId: string): Promise<ProblemFileTreeResponse> {
    return request(`/api/problems/${problemId}/files`);
  },
  getProblemFileContent(problemId: string, path: string): Promise<ProblemFileContent> {
    return request(
      `/api/problems/${problemId}/files/content?path=${encodeURIComponent(path)}`,
    );
  },
  saveProblemFile(
    problemId: string,
    path: string,
    content: string,
  ): Promise<ProblemFileContent> {
    return request(`/api/problems/${problemId}/files/content?path=${encodeURIComponent(path)}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    });
  },
  createProblemNode(
    problemId: string,
    name: string,
    kind: "file" | "directory",
    parentPath?: string | null,
  ): Promise<ProblemFileCreateResponse> {
    return request(`/api/problems/${problemId}/files`, {
      method: "POST",
      body: JSON.stringify({
        name,
        kind,
        parent_path: parentPath ?? null,
      }),
    });
  },
  executeProblem(
    problemId: string,
    code: string,
    input?: unknown,
  ): Promise<QueuedSubmissionResponse> {
    return request(`/api/problems/${problemId}/execute`, {
      method: "POST",
      body: JSON.stringify({ code, language: "python", input: input ?? null }),
    });
  },
  runProblem(problemId: string, code: string): Promise<QueuedSubmissionResponse> {
    return request(`/api/problems/${problemId}/run`, {
      method: "POST",
      body: JSON.stringify({ code, language: "python" }),
    });
  },
  submitProblem(problemId: string, code: string): Promise<QueuedSubmissionResponse> {
    return request(`/api/problems/${problemId}/submit`, {
      method: "POST",
      body: JSON.stringify({ code, language: "python" }),
    });
  },
  getSubmission(submissionId: string): Promise<SubmissionDetail> {
    return request(`/api/submissions/${submissionId}`);
  },
};
