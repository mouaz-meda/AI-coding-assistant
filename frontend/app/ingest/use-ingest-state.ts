"use client";

import { useEffect, useState, type ChangeEvent, type SubmitEvent } from "react";
import { useRouter } from "next/navigation";
import {
  ApiError,
  ingestPath,
  ingestPathFile,
  ingestUpload,
  reviewFile,
  reviewMultipleFiles,
  type IngestSummary,
  type MultiReviewResult,
  type ProjectFile,
  type SkippedFile,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import { MAX_FILE_BYTES, skippedDirectory, type FileResults, type ReviewAction } from "./utils";

export function useIngestState() {
  const router = useRouter();
  const [summary, setSummary] = useState<IngestSummary | null>(null);
  const [localSkipped, setLocalSkipped] = useState<SkippedFile[]>([]);
  const [serverPath, setServerPath] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  // Content for uploaded files, plus any path-ingested file fetched on demand via
  // ingestedRoot below — /ingest/path itself never returns file content up front.
  const [uploadedContent, setUploadedContent] = useState<Map<string, string>>(new Map());
  // The directory last submitted via the server-path form, so handleReview knows
  // where to fetch a given path-ingested file's content from when it's first needed.
  const [ingestedRoot, setIngestedRoot] = useState<string | null>(null);
  const [reviewing, setReviewing] = useState<{ path: string; action: ReviewAction } | null>(null);
  // Both actions' results are cached per file, keyed by action, so switching tabs
  // never re-fires a request — only a first-time Review/Fix click does.
  const [results, setResults] = useState<Map<string, FileResults>>(new Map());
  const [activeTab, setActiveTab] = useState<Map<string, ReviewAction>>(new Map());
  // Live instruction text per file, separate from results since it's input, not a fetched value.
  const [instructions, setInstructions] = useState<Map<string, string>>(new Map());
  // The browser's own "N files selected" text on a file input is native UI we can't
  // customize or rely on (it reverts the moment the input resets), so FilePicker
  // shows this instead. One per input, since each keeps its own last selection.
  const [filesLabel, setFilesLabel] = useState<string | null>(null);
  const [folderLabel, setFolderLabel] = useState<string | null>(null);
  const [multiAction, setMultiAction] = useState<ReviewAction | null>(null);
  const [multiResult, setMultiResult] = useState<MultiReviewResult | null>(null);

  useEffect(() => {
    if (!getToken()) router.push("/login");
  }, [router]);

  function requireToken(): string | null {
    const token = getToken();
    if (!token) router.push("/login");
    return token;
  }

  async function handleFilesSelected(e: ChangeEvent<HTMLInputElement>) {
    const inputEl = e.target;
    const selected = Array.from(inputEl.files ?? []);
    const token = requireToken();
    if (!token) return;
    if (selected.length === 0) return;

    const isFolder = selected.some((f) => f.webkitRelativePath);
    const label =
      selected.length === 1 && !isFolder
        ? selected[0].name
        : `${selected.length} file${selected.length === 1 ? "" : "s"}`;
    if (isFolder) {
      setFolderLabel(label);
    } else {
      setFilesLabel(label);
    }

    setError(null);
    setSummary(null);
    setIngestedRoot(null);
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
      // Reset only now (not before processing) so the browser's native "N files
      // selected" display stays visible while ingesting — still resets so the
      // same file/folder can be re-selected later.
      inputEl.value = "";
    }
  }

  async function handlePathSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();
    const token = requireToken();
    if (!token) return;

    setError(null);
    setSummary(null);
    setLocalSkipped([]);
    setUploadedContent(new Map());
    setResults(new Map());
    setIngestedRoot(null);
    setBusy(true);
    try {
      setSummary(await ingestPath(token, serverPath));
      setIngestedRoot(serverPath);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  async function handleReview(path: string, action: ReviewAction) {
    const token = requireToken();
    if (!token) return;

    const currentInstruction = instructions.get(path) ?? "";
    const cached = results.get(path)?.[action];
    // Already fetched for this exact action + instruction — just switch tabs, no request.
    // A changed instruction is treated as a new request, not a cache hit.
    if (cached && (cached.instruction ?? "") === currentInstruction) {
      setActiveTab((prev) => new Map(prev).set(path, action));
      return;
    }

    setError(null);
    setReviewing({ path, action });
    try {
      let content = uploadedContent.get(path);
      if (content === undefined) {
        // Not an uploaded file — if it came from a server-path ingest, fetch its
        // content now (and cache it) instead of giving up.
        if (ingestedRoot === null) return;
        content = (await ingestPathFile(token, ingestedRoot, path)).content;
        setUploadedContent((prev) => new Map(prev).set(path, content!));
      }

      const result = await reviewFile(token, path, content, action, currentInstruction);
      setResults((prev) => {
        const next = new Map(prev);
        next.set(path, { ...next.get(path), [action]: result });
        return next;
      });
      setActiveTab((prev) => new Map(prev).set(path, action));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setReviewing(null);
    }
  }

  function setInstruction(path: string, text: string) {
    setInstructions((prev) => new Map(prev).set(path, text));
  }

  async function handleMultiReview(action: ReviewAction, instruction: string) {
    const token = requireToken();
    if (!token) return;
    if (!instruction.trim()) return;
    if (!summary || summary.accepted.length === 0) return;

    setError(null);
    setMultiAction(action);
    try {
      // Fetch content for any accepted file not already cached (uploads have it
      // already; path-ingested files are fetched lazily, same as a single-file
      // review/fix would) so multi-review always covers every accepted file.
      const missing = summary.accepted.filter((f) => !uploadedContent.has(f.path));
      let content = uploadedContent;
      if (missing.length > 0) {
        if (ingestedRoot === null) throw new ApiError("Some accepted files have no content available");
        const fetched = await Promise.all(missing.map((f) => ingestPathFile(token, ingestedRoot, f.path)));
        content = new Map(uploadedContent);
        fetched.forEach((f) => content.set(f.path, f.content));
        setUploadedContent(content);
      }

      const files: ProjectFile[] = summary.accepted.map((f) => ({ path: f.path, content: content.get(f.path)! }));
      setMultiResult(await reviewMultipleFiles(token, files, action, instruction));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setMultiAction(null);
    }
  }

  function removeFile(path: string) {
    setSummary((prev) =>
      prev
        ? {
            ...prev,
            accepted: prev.accepted.filter((f) => f.path !== path),
            total_accepted: prev.total_accepted - 1,
          }
        : prev,
    );
    setUploadedContent((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
    setResults((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
    setActiveTab((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
    setInstructions((prev) => {
      const next = new Map(prev);
      next.delete(path);
      return next;
    });
  }

  function setFileTab(path: string, action: ReviewAction) {
    setActiveTab((prev) => new Map(prev).set(path, action));
  }

  return {
    summary,
    allSkipped: summary ? [...localSkipped, ...summary.skipped] : [],
    serverPath,
    setServerPath,
    error,
    busy,
    uploadedContent,
    ingestedRoot,
    reviewing,
    results,
    activeTab,
    instructions,
    filesLabel,
    folderLabel,
    multiAction,
    multiBusy: multiAction !== null,
    multiResult,
    handleFilesSelected,
    handlePathSubmit,
    handleReview,
    handleMultiReview,
    removeFile,
    setFileTab,
    setInstruction,
  };
}
