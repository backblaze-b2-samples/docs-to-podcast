import { ShowDetail } from "@/components/shows/show-detail";

export default async function ShowDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ShowDetail showId={id} />;
}
