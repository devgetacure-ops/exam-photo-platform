import { redirect } from "next/navigation";

/** Old address (DEC-109), kept for links in emails already sent: opens the side panel. */
export default async function Legacy({ params }: { params: Promise<{ jobId: string }> }) {
    const { jobId } = await params;
    redirect(`/admin/uploads?open=${encodeURIComponent(decodeURIComponent(jobId))}`);
}
