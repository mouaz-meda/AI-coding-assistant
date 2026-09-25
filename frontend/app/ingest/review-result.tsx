"use client";

import ReactDiffViewer from "react-diff-viewer-continued";
import type { ReviewResult } from "@/lib/api";
import { languageFromPath } from "./utils";
import { ReviewMarkdown } from "./markdown-content";

export function ReviewResultView({
  result,
  original,
}: {
  result: ReviewResult;
  original: string | undefined;
}) {
  if (result.diff === null) return <ReviewMarkdown text={result.output} />;
  if (result.diff === "") return <p className="text-sm text-muted-foreground">No changes needed.</p>;
  if (original === undefined) {
    return (
      <pre className="max-h-96 overflow-auto rounded-lg bg-muted p-3 font-mono text-xs">{result.diff}</pre>
    );
  }
  return (
    <div className="overflow-auto rounded-lg border text-xs">
      <ReactDiffViewer
        oldValue={original}
        newValue={result.output}
        splitView={false}
        highlightLanguage={languageFromPath(result.path)}
      />
    </div>
  );
}
