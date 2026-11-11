import { permanentRedirect } from "next/navigation";

/**
 * The refund policy retired with payments (DEC-127): nothing is sold, so
 * nothing is refunded. The address stays alive for old links and emails.
 */
export default function Refunds() {
    permanentRedirect("/terms");
}
