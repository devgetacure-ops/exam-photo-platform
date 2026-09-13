import { PolicyPage } from "../../components/policy-page";
export const metadata = { title: "Payment and refund help · examuploadkit" };
export default function Refunds() {
    return (
        <PolicyPage
            title="Paid, but something went wrong?"
            intro="Start with the payment and delivery record. We’ll help you report what happened."
            sections={[
                {
                    title: "Payment still confirming",
                    text: "Refresh the kit in the same browser. Your files are released after server confirmation, which may arrive after checkout closes. Do not pay again while the outcome is uncertain.",
                },
                {
                    title: "Paid and not delivered",
                    text: "Raise a private support request with your payment reference, the UPI reference or payment ID shown in your payment app, and what happened. Requests concerning payment received without file delivery are reviewed case by case against payment and delivery evidence.",
                },
                {
                    title: "What the review can establish",
                    text: "The service records file download and email-send events to help investigate delivery. Reporting a problem does not itself issue a refund. Once a refund is approved, it is started within 5 to 7 working days, to the payment method you used; your bank may take a few more days to show it.",
                },
                {
                    title: "Expiry and exam outcomes",
                    text: "Download promptly or use email while files are available. Deleted files cannot be recovered. Preparation does not guarantee acceptance by an examination authority. Explain the particular issue in your request so it can be reviewed.",
                },
            ]}
        />
    );
}
