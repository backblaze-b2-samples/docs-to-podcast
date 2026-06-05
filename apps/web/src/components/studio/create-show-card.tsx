"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Check } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateShow, useShows } from "@/lib/queries";

interface Props {
  activeShowId: string | undefined;
  onShowSelected: (id: string) => void;
}

export function CreateShowCard({ activeShowId, onShowSelected }: Props) {
  const [title, setTitle] = useState("");
  const { data: shows = [] } = useShows();
  const createShow = useCreateShow();

  const handleCreate = async () => {
    const trimmed = title.trim();
    if (!trimmed) {
      toast.error("Give your show a title first");
      return;
    }
    try {
      const show = await createShow.mutateAsync(trimmed);
      onShowSelected(show.id);
      setTitle("");
      toast.success(`Show "${show.title}" created`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create show");
    }
  };

  return (
    <Card>
      <CardHeader className="border-b border-border py-4 px-5">
        <CardTitle className="card-title">1. Choose a show</CardTitle>
      </CardHeader>
      <CardContent className="p-5 space-y-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm font-medium">Create a new show</label>
          <div className="flex gap-2">
            <Input
              placeholder="e.g. This Week in Object Storage"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreate();
              }}
            />
            <Button onClick={handleCreate} disabled={createShow.isPending}>
              {createShow.isPending ? "Creating..." : "Create"}
            </Button>
          </div>
        </div>

        {shows.length > 0 && (
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">…or pick an existing one</label>
            <Select value={activeShowId} onValueChange={onShowSelected}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a show" />
              </SelectTrigger>
              <SelectContent>
                {shows.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.title} ({s.source_count} sources, {s.episode_count} episodes)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {activeShowId && (
          <p className="inline-flex items-center gap-1.5 text-xs text-[var(--success)]">
            <Check className="h-3.5 w-3.5" />
            Show selected — add sources below.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
