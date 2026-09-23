/**
 * Saved replies (DEC-109). Each opens in the owner's own mail app, addressed
 * and filled in, so nothing is sent from here and every reply can be edited.
 */

export interface ReplyContext {
    exam?: string | null;
    paymentReference?: string | null;
    amountPaise?: number | null;
    reference?: string | null;
    refundReference?: string | null;
}

export interface Reply {
    id: string;
    label: string;
    subject: string;
    body: string;
}

const SIGN_OFF = "\n\nRegards,\nExamUploadKit support\nhttps://examuploadkit.com";

function payment(context: ReplyContext): string {
    const parts = [
        context.paymentReference ? `payment ${context.paymentReference}` : "",
        context.amountPaise != null ? `Rs ${context.amountPaise / 100}` : "",
    ].filter(Boolean);
    return parts.length ? ` (${parts.join(", ")})` : "";
}

export function replies(context: ReplyContext): Reply[] {
    const about = context.reference ? ` [${context.reference}]` : "";
    const exam = context.exam || "your examination";
    return [
        {
            id: "acknowledge",
            label: "We are looking into it",
            subject: `We have your message${about}`,
            body: `Hello,\n\nThank you for writing. We have received your message and are looking into it. We will reply within 48 hours.${SIGN_OFF}`,
        },
        {
            id: "file-missing",
            label: "Where is my file",
            subject: `Your ${exam} file${about}`,
            body: `Hello,\n\nThank you for writing. We have checked your order${payment(context)}.\n\nFiles are kept for a short time after they are prepared. Please open https://examuploadkit.com, choose ${exam}, and prepare the file again. If you are asked to pay again for the same file, reply to this email and we will sort it out.${SIGN_OFF}`,
        },
        {
            id: "refund-done",
            label: "Refund issued",
            subject: `Refund for your ${exam} order${about}`,
            body: `Hello,\n\nWe have refunded your payment${payment(context)}${context.refundReference ? `. The refund reference is ${context.refundReference}` : ""}. Depending on your bank it can take 5 to 7 working days to appear.\n\nWe are sorry the file did not reach you.${SIGN_OFF}`,
        },
        {
            id: "wrong-size",
            label: "Size or rule rejected",
            subject: `Your ${exam} photo${about}`,
            body: `Hello,\n\nThank you for telling us. Could you send the exact message the application portal showed, and a screenshot if possible? We check every examination's published rule, and if the portal expects something different we will correct it and prepare your file again at no charge.${SIGN_OFF}`,
        },
        {
            id: "charged-twice",
            label: "Charged twice",
            subject: `Your payment${about}`,
            body: `Hello,\n\nWe have checked our records${payment(context)}. Please send the payment ID or UPI reference of each charge from your payment app, and we will refund any payment that did not release a file.${SIGN_OFF}`,
        },
        {
            id: "exam-added",
            label: "Examination added",
            subject: `${exam} is now on ExamUploadKit${about}`,
            body: `Hello,\n\nYou asked us for ${exam}. It is now ready: choose it at https://examuploadkit.com and your photograph and signature are prepared to its published rules.${SIGN_OFF}`,
        },
    ];
}

export function mailto(email: string, reply: Reply): string {
    return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(reply.subject)}&body=${encodeURIComponent(reply.body)}`;
}
