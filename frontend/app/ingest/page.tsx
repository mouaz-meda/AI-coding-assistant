"use client";

import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { AcceptedFileList } from "./accepted-file-list";
import { FilePicker } from "./file-picker";
import { MultiReview } from "./multi-review";
import { ResultsPanel } from "./results-panel";
import { useIngestState } from "./use-ingest-state";

// React's types don't include this attribute; it turns the file input into a folder picker.
const folderPickerProps = { webkitdirectory: "" } as Record<string, string>;

export default function IngestPage() {
  const {
    summary,
    allSkipped,
    serverPath,
    setServerPath,
    error,
    busy,
    uploadedContent,
    reviewing,
    results,
    activeTab,
    instructions,
    filesLabel,
    folderLabel,
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
              <FilePicker
                id="files"
                placeholder="No file chosen"
                displayText={filesLabel}
                multiple
                disabled={anyBusy}
                onChange={handleFilesSelected}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="folder">Upload a folder</Label>
              <FilePicker
                id="folder"
                placeholder="No folder chosen"
                displayText={folderLabel}
                disabled={anyBusy}
                onChange={handleFilesSelected}
                inputProps={folderPickerProps}
              />
            </div>
          </div>

          <form onSubmit={handlePathSubmit} className="flex flex-col gap-2">
            <Label htmlFor="server-path">Or read a folder on the server</Label>
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

          {busy && <p className="text-sm text-muted-foreground">Working...</p>}
          {reviewing && (
            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              {reviewing.action === "review" ? "Reviewing" : "Fixing"} <span className="font-medium">{reviewing.path}</span>
              ... this calls the LLM and can take a moment.
            </p>
          )}
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
          <CardContent className="flex flex-col gap-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">Accepted</h3>
                <AcceptedFileList
                  files={summary.accepted}
                  uploadedContent={uploadedContent}
                  reviewing={reviewing}
                  instructions={instructions}
                  onReview={handleReview}
                  onRemove={removeFile}
                  onInstructionChange={setInstruction}
                />
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
            </div>

            <MultiReview
              fileCount={uploadedContent.size}
              busy={multiBusy}
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

      <Link href="/" className="text-sm text-primary underline-offset-4 hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}
