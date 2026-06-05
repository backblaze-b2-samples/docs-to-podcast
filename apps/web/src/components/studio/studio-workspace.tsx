"use client";

import { useState } from "react";

import { CreateShowCard } from "./create-show-card";
import { SourceIngestCard } from "./source-ingest-card";
import { GenerateCard } from "./generate-card";

// Three-step Studio flow. The active show id is the only piece of shared
// state; each step is a self-contained card that reads/writes B2 through the
// TanStack Query hooks (no bare fetch).
export function StudioWorkspace() {
  const [showId, setShowId] = useState<string | undefined>(undefined);

  return (
    <div className="space-y-6">
      <CreateShowCard activeShowId={showId} onShowSelected={setShowId} />
      {showId && (
        <>
          <SourceIngestCard showId={showId} />
          <GenerateCard showId={showId} />
        </>
      )}
    </div>
  );
}
