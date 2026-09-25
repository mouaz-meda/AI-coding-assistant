import type { ReviewResult } from "@/lib/api";

// Mirrors the server's skip rules so junk isn't read or sent. The server re-checks everything.
export const SKIP_DIRS = new Set([
  ".git",
  ".venv",
  "venv",
  "node_modules",
  "__pycache__",
  ".idea",
  ".next",
  "dist",
  "build",
]);
export const MAX_FILE_BYTES = 200_000;

const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  py: "python",
  js: "javascript",
  jsx: "jsx",
  ts: "typescript",
  tsx: "tsx",
  json: "json",
  css: "css",
  html: "html",
  md: "markdown",
  go: "go",
  rb: "ruby",
  java: "java",
  c: "c",
  h: "c",
  cpp: "cpp",
  cc: "cpp",
  rs: "rust",
  sh: "bash",
  yml: "yaml",
  yaml: "yaml",
  sql: "sql",
};

export function languageFromPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return LANGUAGE_BY_EXTENSION[ext] ?? "";
}

export function skippedDirectory(path: string): string | undefined {
  return path.split("/").slice(0, -1).find((part) => SKIP_DIRS.has(part));
}

export type ReviewAction = "review" | "fix";
export type FileResults = Partial<Record<ReviewAction, ReviewResult>>;