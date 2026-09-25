"use client";

import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ReviewAction } from "./utils";

export function AcceptedFileList({
  files,
  uploadedContent,
  reviewing,
  onReview,
  onRemove,
}: {
  files: { path: string; size: number }[];
  uploadedContent: Map<string, string>;
  reviewing: { path: string; action: ReviewAction } | null;
  onReview: (path: string, action: ReviewAction) => void;
  onRemove: (path: string) => void;
}) {
  // Disabled for every file while any one review/fix request is in flight, not just
  // this row's — avoids firing a second request or changing state mid-request.
  const globallyBusy = reviewing !== null;

  return (
    <ul className="max-h-64 overflow-y-auto text-sm">
      {files.map((file) => {
        const canAct = uploadedContent.has(file.path);
        return (
          <li key={file.path} className="flex flex-col gap-1 py-1">
            <div className="flex justify-between gap-2">
              <span className="break-all">{file.path}</span>
              <span className="shrink-0 text-muted-foreground">{file.size.toLocaleString()} B</span>
            </div>
            <div className="flex items-center gap-2">
              {canAct ? (
                <>
                  <ActionButton
                    label="Review"
                    loadingLabel="Reviewing..."
                    active={reviewing?.path === file.path && reviewing.action === "review"}
                    disabled={globallyBusy}
                    onClick={() => onReview(file.path, "review")}
                  />
                  <ActionButton
                    label="Fix"
                    loadingLabel="Fixing..."
                    active={reviewing?.path === file.path && reviewing.action === "fix"}
                    disabled={globallyBusy}
                    onClick={() => onReview(file.path, "fix")}
                  />
                </>
              ) : (
                <span className="text-xs text-muted-foreground">
                  uploaded via server path — upload the file to review/fix it
                </span>
              )}
              <Button
                variant="ghost"
                size="xs"
                className="text-destructive hover:text-destructive"
                disabled={globallyBusy}
                onClick={() => onRemove(file.path)}
              >
                Remove
              </Button>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function ActionButton({
  label,
  loadingLabel,
  active,
  disabled,
  onClick,
}: {
  label: string;
  loadingLabel: string;
  active: boolean;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <Button variant="outline" size="xs" disabled={disabled} onClick={onClick}>
      {active ? (
        <>
          <Loader2 className="size-3 animate-spin" />
          {loadingLabel}
        </>
      ) : (
        label
      )}
    </Button>
  );
}