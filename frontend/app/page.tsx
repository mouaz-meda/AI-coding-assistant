"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FolderCode, Loader2 } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { getCurrentUser, type User } from "@/lib/api";
import { getToken, clearToken } from "@/lib/auth";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    getCurrentUser(token)
      .then(setUser)
      .catch(() => {
        clearToken();
        router.push("/login");
      });
  }, [router]);

  if (!user) {
    return (
      <div className="flex flex-1 items-center justify-center gap-2 p-6 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading...
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <SiteHeader email={user.email} />
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="flex w-full max-w-md flex-col gap-4">
          <div className="flex flex-col gap-1">
            <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground">
              Ingest a project, then ask the assistant to review or fix it.
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Account</CardTitle>
              <CardDescription>Your session details.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex flex-col gap-1">
                <span className="text-xs text-muted-foreground">Email</span>
                <span className="truncate font-medium">{user.email}</span>
              </div>
              <div className="flex flex-col gap-1">
                <span className="text-xs text-muted-foreground">Member since</span>
                <span className="font-medium">
                  {new Date(user.created_at).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </span>
              </div>
            </CardContent>
          </Card>

          <Link
            href="/ingest"
            className={buttonVariants({ className: "w-full gap-2", size: "lg" })}
          >
            <FolderCode className="size-4" />
            Ingest project files
          </Link>
        </div>
      </div>
    </div>
  );
}
