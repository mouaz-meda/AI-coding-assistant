"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { FolderUp, Upload } from "lucide-react";
import { cn } from "cn";

export type PickedFile = { path: string; file: File };

// React's types don't include this attribute; it turns the file input into a folder picker.
const folderInputProps = { webkitdirectory: "" } as Record<string, string>;

async function readAllEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  const all: FileSystemEntry[] = [];
  // The browser batches ~100 entries per readEntries() call — keep calling until
  // it returns empty, or large folders silently truncate.
  while (true) {
    const batch = await new Promise<FileSystemEntry[]>((resolve, reject) => reader.readEntries(resolve, reject));
    if (batch.length === 0) return all;
    all.push(...batch);
  }
}

async function walkEntry(entry: FileSystemEntry, path: string): Promise<PickedFile[]> {
  if (entry.isFile) {
    const file = await new Promise<File>((resolve, reject) => (entry as FileSystemFileEntry).file(resolve, reject));
    return [{ path, file }];
  }
  const entries = await readAllEntries((entry as FileSystemDirectoryEntry).createReader());
  const nested = await Promise.all(entries.map((e) => walkEntry(e, `${path}/${e.name}`)));
  return nested.flat();
}

// A single drop target replaces separate file/folder inputs: dropping works for
// either, and a click browses files (the common case) with a small fallback link
// for folder selection — a native <input type="file"> can only do one of
// files-or-folder per click, so folder-via-click still needs its own input.
export function Dropzone({
  displayText,
  disabled,
  onFilesPicked,
}: {
  displayText: string | null;
  disabled?: boolean;
  onFilesPicked: (files: PickedFile[]) => void;
}) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? []);
    e.target.value = "";
    if (selected.length === 0) return;
    onFilesPicked(selected.map((file) => ({ path: file.webkitRelativePath || file.name, file })));
  }

  async function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const entries = Array.from(e.dataTransfer.items)
      .map((item) => item.webkitGetAsEntry())
      .filter((entry): entry is FileSystemEntry => entry !== null);
    const picked = (await Promise.all(entries.map((entry) => walkEntry(entry, entry.name)))).flat();
    if (picked.length > 0) onFilesPicked(picked);
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center justify-center gap-1.5 rounded-lg border border-dashed px-4 py-6 text-center transition-colors",
        disabled
          ? "pointer-events-none cursor-not-allowed opacity-50 border-input"
          : "cursor-pointer border-input hover:border-ring/60 hover:bg-accent/40",
        dragOver && "border-ring bg-accent/40",
      )}
    >
      <Upload className="size-4 text-muted-foreground" />
      <span className={cn("text-sm", displayText ? "text-foreground" : "text-muted-foreground")}>
        {displayText ?? "Drag files or a folder here, or click to browse"}
      </span>
      <label
        className="flex items-center gap-1 text-xs text-muted-foreground underline-offset-4 hover:underline"
        onClick={(e) => e.stopPropagation()}
      >
        <FolderUp className="size-3" />
        or choose a folder
        <input
          type="file"
          disabled={disabled}
          onChange={handleInputChange}
          className="sr-only"
          {...folderInputProps}
        />
      </label>
      <input
        ref={inputRef}
        type="file"
        multiple
        disabled={disabled}
        onChange={handleInputChange}
        className="sr-only"
      />
    </div>
  );
}