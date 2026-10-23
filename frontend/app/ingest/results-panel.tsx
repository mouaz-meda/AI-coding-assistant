"use client";

import { Eye, Wand2 } from "lucide-react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileCard } from "./file-card";
import { ReviewResultView } from "./review-result";
import type { FileResults, ReviewAction } from "./utils";

const ACTION_ICON = { review: Eye, fix: Wand2 } as const;

export function ResultsPanel({
  results,
  activeTab,
  uploadedContent,
  onTabChange,
}: {
  results: Map<string, FileResults>;
  activeTab: Map<string, ReviewAction>;
  uploadedContent: Map<string, string>;
  onTabChange: (path: string, action: ReviewAction) => void;
}) {
  const entries = [...results.entries()].filter(([, r]) => r.review || r.fix);
  if (entries.length === 0) return null;

  return (
    <div className="flex flex-col gap-3 border-t border-border/60 pt-4">
      <h3 className="text-sm font-medium text-muted-foreground">
        {entries.length} result{entries.length === 1 ? "" : "s"}
      </h3>
      {entries.map(([path, fileResults]) => {
        const available = (["review", "fix"] as const).filter((a) => fileResults[a]);
        const active = activeTab.get(path) ?? available[available.length - 1];
        const result = fileResults[active] ?? fileResults[available[0]];
        if (!result) return null;

        return (
          <FileCard
            key={path}
            path={path}
            icon={ACTION_ICON[active]}
            defaultOpen={entries.length === 1}
            headerExtra={
              available.length > 1 && (
                <Tabs
                  value={active}
                  onValueChange={(value) => onTabChange(path, value as ReviewAction)}
                  onClick={(e) => e.stopPropagation()}
                >
                  <TabsList>
                    <TabsTrigger value="review">Review</TabsTrigger>
                    <TabsTrigger value="fix">Fix</TabsTrigger>
                  </TabsList>
                </Tabs>
              )
            }
          >
            {result.instruction && (
              <p className="text-xs text-muted-foreground">
                Instruction: <span className="italic">{result.instruction}</span>
              </p>
            )}
            <ReviewResultView result={result} original={uploadedContent.get(path)} />
          </FileCard>
        );
      })}
    </div>
  );
}