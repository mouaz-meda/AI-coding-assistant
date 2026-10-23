"use client";

import { FolderInput, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { AcceptedFileList } from "./accepted-file-list";
import { Dropzone } from "./dropzone";
import { MultiReview } from "./multi-review";
import { ResultsPanel } from "./results-panel";
import { useIngestState } from "./use-ingest-state";

export default function IngestPage() {
  const {
    summary,
    allSkipped,
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
    selectionLabel,
    multiAction,
    multiBusy,
    multiResult,
    handleFilesSelected,
    handlePathSubmit,
    handleReview,
    handleMultiReview,
    removeFile,
    setFileTab,
    setInstruction,
  } = useIngestState();

  // While a review/fix request is running, block every other control on the page
  // rather than just the file it's for — avoids firing overlapping requests.
  const isReviewing = reviewing !== null;
  const anyBusy = busy || isReviewing || multiBusy;

  return (
    <div className="flex flex-1 flex-col">
      <SiteHeader />
      <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 p-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight">Ingest project files</h1>
          <p className="text-sm text-muted-foreground">
            Choose what the assistant should look at, then ask it to review or fix.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Add files</CardTitle>
            <CardDescription>
              Junk folders (node_modules, .git, ...), binary and oversized files are skipped automatically.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <Label className="flex items-center gap-1.5">
                <Upload className="size-3.5 text-muted-foreground" />
                Upload files or a folder
              </Label>
              <Dropzone displayText={selectionLabel} disabled={anyBusy} onFilesPicked={handleFilesSelected} />
            </div>

            <form onSubmit={handlePathSubmit} className="flex flex-col gap-2">
              <Label htmlFor="server-path" className="flex items-center gap-1.5">
                <FolderInput className="size-3.5 text-muted-foreground" />
                Or read a folder on the server
              </Label>
              <div className="flex gap-2">
                <Input
                  id="server-path"
                  placeholder="path relative to the server's INGEST_ROOT"
                  disabled={anyBusy}
                  value={serverPath}
                  onChange={(e) => setServerPath(e.target.value)}
                />
                <Button type="submit" disabled={anyBusy}>
                  Ingest
                </Button>
              </div>
            </form>

            {busy && (
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Working...
              </p>
            )}
            {reviewing && (
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                {reviewing.action === "review" ? "Reviewing" : "Fixing"}{" "}
                <span className="font-medium text-foreground">{reviewing.path}</span>
                ... this calls the LLM and can take a moment.
              </p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </CardContent>
        </Card>

        {summary && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <span className="rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground">
                  {summary.total_accepted} accepted
                </span>
                {allSkipped.length > 0 && (
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                    {allSkipped.length} skipped
                  </span>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="flex flex-col gap-2">
                  <h3 className="text-sm font-medium">Accepted</h3>
                  <AcceptedFileList
                    files={summary.accepted}
                    uploadedContent={uploadedContent}
                    ingestedRoot={ingestedRoot}
                    reviewing={reviewing}
                    instructions={instructions}
                    onReview={handleReview}
                    onRemove={removeFile}
                    onInstructionChange={setInstruction}
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <h3 className="text-sm font-medium">Skipped</h3>
                  <ul className="max-h-64 overflow-y-auto rounded-lg border border-border/60 divide-y divide-border/60 text-sm">
                    {allSkipped.length === 0 && (
                      <li className="px-2 py-3 text-center text-xs text-muted-foreground">Nothing skipped</li>
                    )}
                    {allSkipped.map((file) => (
                      <li key={file.path} className="px-2 py-1.5">
                        <span className="break-all">{file.path}</span>
                        <span className="block text-xs text-muted-foreground">{file.reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <MultiReview
                fileCount={summary.accepted.length}
                activeAction={multiAction}
                result={multiResult}
                uploadedContent={uploadedContent}
                disabled={anyBusy}
                onSubmit={handleMultiReview}
              />

              <ResultsPanel
                results={results}
                activeTab={activeTab}
                uploadedContent={uploadedContent}
                onTabChange={setFileTab}
              />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
