"use client";

import type { ChangeEvent } from "react";
import { cn } from "cn";

// Native <input type="file"> renders its "Choose File / No file chosen" text as
// fixed browser/OS chrome — it can't be restyled or replaced via CSS or a
// placeholder. To show the actual selected filename inside the field, the input
// is visually hidden and a styled <label> (wired to it via htmlFor) stands in as
// the clickable box, showing whatever text we want.
export function FilePicker({
  id,
  placeholder,
  displayText,
  disabled,
  multiple,
  onChange,
  inputProps,
}: {
  id: string;
  placeholder: string;
  displayText: string | null;
  disabled?: boolean;
  multiple?: boolean;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  inputProps?: Record<string, string>;
}) {
  return (
    <label
      htmlFor={id}
      className={cn(
        "flex h-8 w-full min-w-0 items-center truncate rounded-lg border border-input bg-transparent px-2.5 py-1 text-base transition-colors outline-none focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 md:text-sm",
        disabled ? "pointer-events-none cursor-not-allowed opacity-50" : "cursor-pointer",
      )}
    >
      <span className={cn("truncate", displayText ? "text-foreground" : "text-muted-foreground")}>
        {displayText ?? placeholder}
      </span>
      <input
        id={id}
        type="file"
        multiple={multiple}
        disabled={disabled}
        onChange={onChange}
        className="sr-only"
        {...inputProps}
      />
    </label>
  );
}
