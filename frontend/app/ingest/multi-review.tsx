"use client";

import { useRef } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { MultiReviewResult } from "@/lib/api";
import { ReviewMarkdown } from "./markdown-content";
import { ReviewResultView } from "./review-result";
import type { ReviewAction } from "./utils";

export function MultiReview({
  fileCount,
  activeAction,
  result,
  uploadedContent,
  disabled,
  onSubmit,
}: {
  fileCount: number;
  activeAction: ReviewAction | null;
  result: MultiReviewResult | null;
  uploadedContent: Map<string, string>;
  disabled: boolean;
  onSubmit: (action: ReviewAction, instruction: string) => void;
}) {
  // Uncontrolled: the value is only read on submit, via this ref — no React
  // state changes while typing, so this causes zero re-renders (not even of
  // this component) until Review/Fix is actually clicked.
  const instructionRef = useRef<HTMLTextAreaElement>(null);

  if (fileCount === 0) return null;

  function submit(action: ReviewAction) {
    const instruction = instructionRef.current?.value.trim() ?? "";
    if (instruction) onSubmit(action, instruction);
  }

  return (
    <div className="flex flex-col gap-2 border-t pt-4">
      <h3 className="text-sm font-medium">
        Feature request across all {fileCount} uploaded file{fileCount === 1 ? "" : "s"}
      </h3>
      <Textarea
        ref={instructionRef}
        placeholder="e.g. 'add a deleted_at column and update every place that queries users'"
        disabled={disabled}
      />
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={disabled} onClick={() => submit("review")}>
          {activeAction === "review" ? <Loader2 className="size-3 animate-spin" /> : null}
          Review
        </Button>
        <Button variant="outline" size="sm" disabled={disabled} onClick={() => submit("fix")}>
          {activeAction === "fix" ? <Loader2 className="size-3 animate-spin" /> : null}
          Fix
        </Button>
      </div>
      {activeAction && (
        <p className="text-sm text-muted-foreground">
          {activeAction === "review" ? "Reviewing" : "Fixing"} all files — this can take a while.
        </p>
      )}

      {result && (
        <p className="text-xs text-muted-foreground">
          Considered {result.considered_files.length} of {fileCount} file{fileCount === 1 ? "" : "s"}:{" "}
          <span className="italic break-all">{result.considered_files.join(", ")}</span>
        </p>
      )}

      {result?.action === "review" && result.output && <ReviewMarkdown text={result.output} />}
      {result?.action === "fix" && (
        <div className="flex flex-col gap-4">
          {result.edits.length === 0 ? (
            <p className="text-sm text-muted-foreground">No files needed changes.</p>
          ) : (
            result.edits.map((edit) => (
              <div key={edit.path} className="flex flex-col gap-1">
                <h4 className="text-sm font-medium break-all">{edit.path}</h4>
                <ReviewResultView
                  result={{ ...edit, action: "fix", instruction: result.instruction }}
                  original={uploadedContent.get(edit.path)}
                />
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}