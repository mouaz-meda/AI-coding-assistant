"use client";

import { useEffect, useState, type ChangeEvent, type SubmitEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  ApiError,
  ingestPath,
  ingestUpload,
  reviewFile,
  type IngestSummary,
  type ProjectFile,
  type ReviewResult,
  type SkippedFile,
} from "@/lib/api";
import { getToken } from "@/lib/auth";

// Mirrors the server's skip rules so junk isn't read or sent. The server re-checks everything.
const SKIP_DIRS = new Set([".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".next", "dist", "build"]);
const MAX_FILE_BYTES = 200_000;

// React's types don't include this attribute; it turns the file input into a folder picker.
const folderPickerProps = { webkitdirectory: "" } as Record<string, string>;

function skippedDirectory(path: string): string | undefined {
  return path.split("/").slice(0, -1).find((part) => SKIP_DIRS.has(part));
}

export default function IngestPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<IngestSummary | null>(null);
  const [localSkipped, setLocalSkipped] = useState<SkippedFile[]>([]);
  const [serverPath, setServerPath] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Content for uploaded files only — /ingest/path never returns file content, so those
  // files can't be reviewed/fixed yet.
  const [uploadedContent, setUploadedContent] = useState<Map<string, string>>(new Map());
  const [reviewingPath, setReviewingPath] = useState<string | null>(null);
  const [results, setResults] = useState<Map<string, ReviewResult>>(new Map());

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  async function handleFilesSelected(e: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? []);
    e.target.value = "";
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    if (selected.length === 0) return;

    setError(null);
    setSummary(null);
    setBusy(true);
    try {
      const decoder = new TextDecoder("utf-8", { fatal: true });
      const files: ProjectFile[] = [];
      const skipped: SkippedFile[] = [];

      for (const file of selected) {
        const path = file.webkitRelativePath || file.name;
        const skippedDir = skippedDirectory(path);
        if (skippedDir) {
          skipped.push({ path, reason: `inside skipped directory '${skippedDir}'` });
        } else if (file.size > MAX_FILE_BYTES) {
          skipped.push({ path, reason: `larger than ${MAX_FILE_BYTES} bytes` });
        } else {
          try {
            files.push({ path, content: decoder.decode(await file.arrayBuffer()) });
          } catch {
            skipped.push({ path, reason: "not UTF-8 text" });
          }
        }
      }

      setLocalSkipped(skipped);
      setUploadedContent(new Map(files.map((f) => [f.path, f.content])));
      setResults(new Map());
      setSummary(await ingestUpload(token, files));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  async function handlePathSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setError(null);
    setSummary(null);
    setLocalSkipped([]);
    setUploadedContent(new Map());
    setResults(new Map());
    setBusy(true);
    try {
      setSummary(await ingestPath(token, serverPath));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  async function handleReview(path: string, action: "review" | "fix") {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    const content = uploadedContent.get(path);
    if (content === undefined) return;

    setError(null);
    setReviewingPath(path);
    try {
      const result = await reviewFile(token, path, content, action);
      setResults((prev) => new Map(prev).set(path, result));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setReviewingPath(null);
    }
  }

  const allSkipped = summary ? [...localSkipped, ...summary.skipped] : [];

  return (
    <div className="flex flex-1 flex-col items-center gap-4 p-6">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle>Ingest project files</CardTitle>
          <CardDescription>
            Choose what the assistant should look at. Junk folders (node_modules, .git, ...), binary
            and oversized files are skipped.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <Label htmlFor="files">Upload files</Label>
              <Input id="files" type="file" multiple disabled={busy} onChange={handleFilesSelected} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="folder">Upload a folder</Label>
              <Input
                id="folder"
                type="file"
                disabled={busy}
                onChange={handleFilesSelected}
                {...folderPickerProps}
              />
            </div>
          </div>

          <form onSubmit={handlePathSubmit} className="flex flex-col gap-2">
            <Label htmlFor="server-path">Or read a folder on the server</Label>
            <div className="flex gap-2">
              <Input
                id="server-path"
                placeholder="path relative to the server's INGEST_ROOT"
                value={serverPath}
                onChange={(e) => setServerPath(e.target.value)}
              />
              <Button type="submit" disabled={busy}>
                Ingest
              </Button>
            </div>
          </form>

          {busy && <p className="text-sm text-muted-foreground">Working...</p>}
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {summary && (
        <Card className="w-full max-w-2xl">
          <CardHeader>
            <CardTitle>
              {summary.total_accepted} accepted, {allSkipped.length} skipped
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">Accepted</h3>
                <ul className="max-h-64 overflow-y-auto text-sm">
                  {summary.accepted.map((file) => {
                    const canAct = uploadedContent.has(file.path);
                    const isBusy = reviewingPath === file.path;
                    return (
                      <li key={file.path} className="flex flex-col gap-1 py-1">
                        <div className="flex justify-between gap-2">
                          <span className="break-all">{file.path}</span>
                          <span className="shrink-0 text-muted-foreground">
                            {file.size.toLocaleString()} B
                          </span>
                        </div>
                        {canAct ? (
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="xs"
                              disabled={isBusy}
                              onClick={() => handleReview(file.path, "review")}
                            >
                              {isBusy ? "Working..." : "Review"}
                            </Button>
                            <Button
                              variant="outline"
                              size="xs"
                              disabled={isBusy}
                              onClick={() => handleReview(file.path, "fix")}
                            >
                              {isBusy ? "Working..." : "Fix"}
                            </Button>
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">
                            uploaded via server path — upload the file to review/fix it
                          </span>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">Skipped</h3>
                <ul className="max-h-64 overflow-y-auto text-sm">
                  {allSkipped.map((file) => (
                    <li key={file.path} className="py-0.5">
                      <span className="break-all">{file.path}</span>
                      <span className="block text-muted-foreground">{file.reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {[...results.values()].map((result) => (
              <div key={result.path} className="flex flex-col gap-2 border-t pt-4">
                <h3 className="text-sm font-medium break-all">
                  {result.path} — {result.action}
                </h3>
                {result.diff === null ? (
                  <p className="whitespace-pre-wrap text-sm">{result.output}</p>
                ) : result.diff === "" ? (
                  <p className="text-sm text-muted-foreground">No changes needed.</p>
                ) : (
                  <DiffView diff={result.diff} />
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Link href="/" className="text-sm text-primary underline-offset-4 hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}

function DiffView({ diff }: { diff: string }) {
  return (
    <pre className="max-h-96 overflow-auto rounded-lg bg-muted p-3 font-mono text-xs">
      {diff.split("\n").map((line, i) => {
        const color = line.startsWith("+")
          ? "text-green-600 dark:text-green-400"
          : line.startsWith("-")
            ? "text-red-600 dark:text-red-400"
            : undefined;
        return (
          <div key={i} className={color}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}
