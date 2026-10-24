"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Sparkles } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { clearToken } from "@/lib/auth";
import { cn } from "cn";

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/ingest", label: "Ingest" },
] as const;

export function SiteHeader({ email }: { email?: string }) {
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-10 border-b border-border/60 bg-background/70 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-4xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="flex items-center gap-2 text-sm font-semibold tracking-tight">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Sparkles className="size-4" />
          </span>
          AI Coding Assistant
        </Link>
        <nav className="flex items-center gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                buttonVariants({ variant: pathname === link.href ? "secondary" : "ghost", size: "sm" }),
              )}
            >
              {link.label}
            </Link>
          ))}
          {email && (
            <span className="ml-1 hidden max-w-40 truncate text-xs text-muted-foreground md:inline">{email}</span>
          )}
          <button
            onClick={handleLogout}
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "ml-1 text-muted-foreground")}
          >
            <LogOut className="size-3.5" />
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
