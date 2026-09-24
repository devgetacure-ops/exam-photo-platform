import { redirect } from "next/navigation";

/** Old address (DEC-109), kept for links in emails already sent: opens the side panel. */
export default async function Legacy({ params }: { params: Promise<{ email: string }> }) {
    const { email } = await params;
    redirect(`/admin/customers?open=${encodeURIComponent(decodeURIComponent(email))}`);
}
