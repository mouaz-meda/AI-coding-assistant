"use client";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ReviewResultView } from "./review-result";
import type { FileResults, ReviewAction } from "./utils";

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
  return (
    <>
      {[...results.entries()].map(([path, fileResults]) => {
        const available = (["review", "fix"] as const).filter((a) => fileResults[a]);
        if (available.length === 0) return null;
        const active = activeTab.get(path) ?? available[available.length - 1];
        const result = fileResults[active] ?? fileResults[available[0]];
        if (!result) return null;

        return (
          <div key={path} className="flex flex-col gap-2 border-t pt-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-medium break-all">{path}</h3>
              {available.length > 1 ? (
                <Tabs value={active} onValueChange={(value) => onTabChange(path, value as ReviewAction)}>
                  <TabsList>
                    <TabsTrigger value="review">Review</TabsTrigger>
                    <TabsTrigger value="fix">Fix</TabsTrigger>
                  </TabsList>
                </Tabs>
              ) : (
                <span className="text-xs text-muted-foreground capitalize">{active}</span>
              )}
            </div>
            {result.instruction && (
              <p className="text-xs text-muted-foreground">
                Instruction: <span className="italic">{result.instruction}</span>
              </p>
            )}
            <ReviewResultView result={result} original={uploadedContent.get(path)} />
          </div>
        );
      })}
    </>
  );
}
