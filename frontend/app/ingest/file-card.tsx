"use client";

import { ChevronRight } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

// Shared shape for every "one card per file" list in this page (single-file
// results, multi-file fix edits, multi-file review findings) so they read as
// one consistent pattern instead of three slightly different ones.
export function FileCard({
  path,
  icon: Icon,
  defaultOpen,
  headerExtra,
  children,
}: {
  path: string;
  icon: ComponentType<{ className?: string }>;
  defaultOpen?: boolean;
  headerExtra?: ReactNode;
  children: ReactNode;
}) {
  return (
    <Collapsible defaultOpen={defaultOpen} className="rounded-lg border border-border/60 overflow-hidden">
      <CollapsibleTrigger className="group flex w-full items-center justify-between gap-2 bg-card px-3 py-2 text-left hover:bg-accent/40">
        <span className="flex min-w-0 items-center gap-2">
          <ChevronRight className="size-3.5 shrink-0 text-muted-foreground transition-transform group-data-[panel-open]:rotate-90" />
          <Icon className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate text-sm font-medium break-all">{path}</span>
        </span>
        {headerExtra}
      </CollapsibleTrigger>
      <CollapsibleContent className="flex flex-col gap-2 overflow-hidden border-t border-border/60 p-3">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}