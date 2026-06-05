import Link from "next/link";
import { Mic } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ShowsList } from "@/components/shows/shows-list";

export default function ShowsPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="page-title">Shows</h1>
          <p className="text-sm text-muted-foreground mt-1.5">
            Your podcast library, scoped to the <code className="font-mono text-xs">shows/</code> prefix in B2.
          </p>
        </div>
        <Button asChild size="sm" className="h-8">
          <Link href="/studio">
            <Mic className="h-3.5 w-3.5" />
            New episode
          </Link>
        </Button>
      </div>
      <div className="animate-fade-in-up stagger-2">
        <ShowsList />
      </div>
    </div>
  );
}
