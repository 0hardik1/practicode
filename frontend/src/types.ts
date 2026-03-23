export interface ProblemSummary {
  id: string;
  slug: string;
  title: string;
  difficulty: "easy" | "medium" | "hard";
  tags: string[];
  time_limit_seconds: number;
  memory_limit_mb: number;
}

export interface TestCaseView {
  id: string;
  name: string;
  input: unknown;
  expected: unknown;
  is_sample: boolean;
  ordinal: number;
  validation_type: string;
}

export interface ProblemDetail extends ProblemSummary {
  description: string;
  starter_code: Record<string, string>;
  api_docs: string | null;
  visible_tests: TestCaseView[];
}

export interface QueuedSubmissionResponse {
  id: string;
  status: string;
  problem_id: string;
}

export interface SubmissionResult {
  test_id: string;
  name: string;
  passed: boolean;
  duration_ms?: number | null;
  stdout?: string | null;
  stderr?: string | null;
  exit_code?: number | null;
  message?: string | null;
  error?: string | null;
  actual?: unknown;
  expected?: unknown;
}

export interface SubmissionDetail {
  id: string;
  problem_id: string;
  language: string;
  status: string;
  is_submit: boolean;
  results?: SubmissionResult[] | null;
  stdout?: string | null;
  stderr?: string | null;
  duration_ms?: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProblemFileNode {
  name: string;
  path: string;
  kind: "file" | "directory";
  editable: boolean;
  is_binary: boolean;
  mime_type?: string | null;
  size?: number | null;
  children: ProblemFileNode[];
}

export interface ProblemFileTreeResponse {
  problem_id: string;
  root: ProblemFileNode;
}

export interface ProblemFileContent {
  problem_id: string;
  path: string;
  name: string;
  editable: boolean;
  is_binary: boolean;
  mime_type?: string | null;
  size: number;
  text_content?: string | null;
  base64_content?: string | null;
}

export interface ProblemFileCreateResponse {
  problem_id: string;
  path: string;
  kind: "file" | "directory";
}

export interface CodePosition {
  line: number;
  column: number;
}

export interface IntellisenseTextEdit {
  start_line: number;
  start_column: number;
  end_line: number;
  end_column: number;
  text: string;
}

export interface PythonCompletionItem {
  label: string;
  kind: string;
  detail?: string | null;
  documentation?: string | null;
  insert_text?: string | null;
  sort_text?: string | null;
  additional_text_edits: IntellisenseTextEdit[];
}

export interface PythonCompletionResponse {
  items: PythonCompletionItem[];
}

export interface PythonHoverResponse {
  contents: string[];
}
