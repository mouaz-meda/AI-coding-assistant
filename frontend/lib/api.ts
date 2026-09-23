const API_URL = process.env.NEXT_PUBLIC_API_URL;

export type User = {
  id: number;
  email: string;
  created_at: string;
};

export class ApiError extends Error {}

async function parseErrorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function register(email: string, password: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  return res.json();
}

export async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  const data = await res.json();
  return data.access_token;
}

export async function getCurrentUser(token: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  return res.json();
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

async function postIngest(
  endpoint: "upload" | "path",
  token: string,
  body: object,
): Promise<IngestSummary> {
  const res = await fetch(`${API_URL}/ingest/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  return res.json();
}

export function ingestUpload(token: string, files: ProjectFile[]): Promise<IngestSummary> {
  return postIngest("upload", token, { files });
}

export function ingestPath(token: string, path: string): Promise<IngestSummary> {
  return postIngest("path", token, { path });
}

export type ReviewAction = "review" | "fix";

export type ReviewResult = {
  path: string;
  action: ReviewAction;
  output: string;
  diff: string | null;
};

export async function reviewFile(
  token: string,
  path: string,
  content: string,
  action: ReviewAction,
): Promise<ReviewResult> {
  const res = await fetch(`${API_URL}/review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ path, content, action }),
  });
  if (!res.ok) throw new ApiError(await parseErrorDetail(res));
  return res.json();
}