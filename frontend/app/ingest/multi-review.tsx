"use client";

import { useRef } from "react";
import { Eye, Loader2, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { MultiReviewResult } from "@/lib/api";
import { FileCard } from "./file-card";
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
    <div className="flex flex-col gap-2 border-t border-border/60 pt-4">
      <h3 className="text-sm font-medium">
        Feature request across all {fileCount} uploaded file{fileCount === 1 ? "" : "s"}
      </h3>
      <Textarea
        ref={instructionRef}
        className="text-xs md:text-xs"
        placeholder="e.g. 'add a deleted_at column and update every place that queries users'"
        disabled={disabled}
      />
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={disabled} onClick={() => submit("review")}>
          {activeAction === "review" ? <Loader2 className="size-3 animate-spin" /> : <Eye />}
          Review
        </Button>
        <Button variant="outline" size="sm" disabled={disabled} onClick={() => submit("fix")}>
          {activeAction === "fix" ? <Loader2 className="size-3 animate-spin" /> : <Wand2 />}
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

      {result?.action === "review" && (
        <div className="flex flex-col gap-2">
          {result.general && <ReviewMarkdown text={result.general} />}
          {result.findings.length === 0 ? (
            !result.general && <p className="text-sm text-muted-foreground">No findings.</p>
          ) : (
            <>
              <h4 className="text-xs font-medium text-muted-foreground">
                {result.findings.length} file{result.findings.length === 1 ? "" : "s"} with findings
              </h4>
              {result.findings.map((finding) => (
                <FileCard
                  key={finding.path}
                  path={finding.path}
                  icon={Eye}
                  defaultOpen={result.findings.length === 1}
                >
                  <ReviewMarkdown text={finding.notes} />
                </FileCard>
              ))}
            </>
          )}
        </div>
      )}
      {result?.action === "fix" && (
        <div className="flex flex-col gap-2">
          {result.edits.length === 0 ? (
            <p className="text-sm text-muted-foreground">No files needed changes.</p>
          ) : (
            <>
              <h4 className="text-xs font-medium text-muted-foreground">
                {result.edits.length} file{result.edits.length === 1 ? "" : "s"} changed
              </h4>
              {result.edits.map((edit) => (
                <FileCard key={edit.path} path={edit.path} icon={Wand2} defaultOpen={result.edits.length === 1}>
                  <ReviewResultView
                    result={{ ...edit, action: "fix", instruction: result.instruction }}
                    original={uploadedContent.get(edit.path)}
                  />
                </FileCard>
              ))}
            </>
          )}
        </div>
      )}
    </div>
  );
}