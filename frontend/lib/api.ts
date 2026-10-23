const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type User = {
  id: number;
  email: string;
  created_at: string;
};

export class ApiError extends Error {}

// Every catch block in the app wants the same thing: the server's message if
// we have one, a generic fallback otherwise.
export function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "Something went wrong";
}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

// Shared by every call below: build headers, send JSON (or nothing, for a
// GET), and turn a non-OK response into an ApiError. `token` is nullable
// since register/login are the only unauthenticated calls.
async function apiFetch<T>(path: string, token: string | null, body?: object): Promise<T> {
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  return res.json();
}

export function register(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/register", null, { email, password });
}

export async function login(email: string, password: string): Promise<string> {
  const { access_token } = await apiFetch<{ access_token: string }>("/auth/login", null, { email, password });
  return access_token;
}

export function getCurrentUser(token: string): Promise<User> {
  return apiFetch<User>("/auth/me", token);
}

export type ProjectFile = {
  path: string;
  content: string;
};

export type SkippedFile = {
  path: string;
  reason: string;
};

export type IngestSummary = {
  accepted: { path: string; size: number }[];
  skipped: SkippedFile[];
  total_accepted: number;
  total_skipped: number;
};

export function ingestUpload(token: string, files: ProjectFile[]): Promise<IngestSummary> {
  return apiFetch<IngestSummary>("/ingest/upload", token, { files });
}

export function ingestPath(token: string, path: string): Promise<IngestSummary> {
  return apiFetch<IngestSummary>("/ingest/path", token, { path });
}

export function ingestPathFile(token: string, path: string, file: string): Promise<ProjectFile> {
  return apiFetch<ProjectFile>("/ingest/path/file", token, { path, file });
}

export type ReviewAction = "review" | "fix";

export type ReviewResult = {
  path: string;
  action: ReviewAction;
  output: string;
  diff: string | null;
  instruction: string | null;
};

export function reviewFile(
  token: string,
  path: string,
  content: string,
  action: ReviewAction,
  instruction?: string,
): Promise<ReviewResult> {
  return apiFetch<ReviewResult>("/review", token, { path, content, action, instruction: instruction || null });
}

export type FileEdit = {
  path: string;
  output: string;
  diff: string;
};

export type MultiReviewResult = {
  action: ReviewAction;
  instruction: string;
  output: string | null;
  edits: FileEdit[];
  considered_files: string[];
};

export function reviewMultipleFiles(
  token: string,
  files: ProjectFile[],
  action: ReviewAction,
  instruction: string,
): Promise<MultiReviewResult> {
  return apiFetch<MultiReviewResult>("/review/multi", token, { files, action, instruction });
}
