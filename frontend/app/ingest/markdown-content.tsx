"use client";

import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

function CodeBlock({ className, children }: { className?: string; children?: ReactNode }) {
  const match = /language-(\w+)/.exec(className ?? "");
  const text = String(children).replace(/\n$/, "");

  if (match) {
    return (
      <SyntaxHighlighter
        language={match[1]}
        style={oneLight}
        customStyle={{ margin: 0, borderRadius: "0.5rem", fontSize: "0.75rem" }}
      >
        {text}
      </SyntaxHighlighter>
    );
  }
  if (text.includes("\n")) {
    return <pre className="overflow-auto rounded-lg bg-muted p-3 font-mono text-xs">{text}</pre>;
  }
  return <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">{children}</code>;
}

export function ReviewMarkdown({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-2 text-sm [&_ol]:ml-5 [&_ol]:list-decimal [&_ul]:ml-5 [&_ul]:list-disc">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{ code: CodeBlock }}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
