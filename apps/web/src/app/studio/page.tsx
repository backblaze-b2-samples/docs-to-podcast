import { StudioWorkspace } from "@/components/studio/studio-workspace";

export default function StudioPage() {
  return (
    <div className="space-y-8">
      <div className="animate-fade-in border-b border-border pb-5">
        <h1 className="page-title">Studio</h1>
        <p className="text-sm text-muted-foreground mt-1.5">
          Create a show, add source documents, and generate a 2-host episode.
        </p>
      </div>
      <div className="animate-fade-in-up stagger-2 max-w-3xl">
        <StudioWorkspace />
      </div>
    </div>
  );
}
