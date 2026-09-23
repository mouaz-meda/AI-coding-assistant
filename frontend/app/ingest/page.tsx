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
  type IngestSummary,
  type ProjectFile,
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
    setBusy(true);
    try {
      setSummary(await ingestPath(token, serverPath));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
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
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <h3 className="text-sm font-medium">Accepted</h3>
              <ul className="max-h-64 overflow-y-auto text-sm">
                {summary.accepted.map((file) => (
                  <li key={file.path} className="flex justify-between gap-2 py-0.5">
                    <span className="break-all">{file.path}</span>
                    <span className="shrink-0 text-muted-foreground">{file.size.toLocaleString()} B</span>
                  </li>
                ))}
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
          </CardContent>
        </Card>
      )}

      <Link href="/" className="text-sm text-primary underline-offset-4 hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}
