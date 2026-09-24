import { redirect } from "next/navigation";

/** Old address (DEC-109), kept for links in emails already sent: opens the side panel. */
export default async function Legacy({ params }: { params: Promise<{ ticketId: string }> }) {
    const { ticketId } = await params;
    redirect(`/admin/inbox?open=${encodeURIComponent(decodeURIComponent(ticketId))}`);
}
