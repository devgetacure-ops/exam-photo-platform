import { redirect } from "next/navigation";

/** Old address (DEC-109), kept for links in emails already sent: opens the side panel. */
export default async function Legacy({ params }: { params: Promise<{ orderId: string }> }) {
    const { orderId } = await params;
    redirect(`/admin/orders?open=${encodeURIComponent(decodeURIComponent(orderId))}`);
}
