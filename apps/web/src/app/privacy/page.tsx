import { PolicyPage } from "../../components/policy-page";
export const metadata = { title: "Privacy · examuploadkit" };
export default function Privacy() {
    return (
        <PolicyPage
            title="Your files. Your privacy."
            intro="How the preparation service handles your uploads and requests."
            sections={[
                {
                    title: "Temporary preparation",
                    text: "Your uploads are processed to prepare the files you request. Access ends at the deadline shown in your kit, normally 30 minutes from preparation. An extension requested before expiry is bounded at one hour from creation. Payment does not extend storage. Downloaded files and email attachments remain with their recipients.",
                },
                {
                    title: "Your identity stays yours",
                    text: "Uploads are not used to train models. Photographic corrections are limited to preparation and identity-preserving adjustments; no cosmetic reshaping or whitening is offered.",
                },
                {
                    title: "Thumbprints and photographs",
                    text: "A thumb impression and a photograph of your face are biometric information. They are processed only to prepare the file you asked for, after you agree to it at upload, and they follow the same deadline as the rest of your kit. They are not used to identify you, and they are not shared except in the files delivered to you.",
                },
                {
                    title: "Candidates under 18",
                    text: "Where the candidate is, or can be, under 18, files are prepared only after a parent or guardian agrees, before the first upload. A child's files are never used for tracking, profiling or advertising.",
                },
                {
                    title: "Browser and payment records",
                    text: "This browser stores kit references so you can return before expiry, your theme preference and the agreements you gave at upload. Clearing browser data can lose those references. Payment is handled through Razorpay. Order and delivery evidence may be kept separately from temporary images to investigate payment and delivery issues.",
                },
                {
                    title: "Email and requests",
                    text: "An email address entered for file delivery is used to send the attachments; the preparation service records a masked address. Exam and support requests contain the contact details and text you explicitly submit. Requests are private, queued for review and assigned a 30-day retention deadline. Do not submit identity numbers, photographs, passwords or card details through the request form.",
                },
                {
                    title: "Your rights",
                    text: "You can ask what personal data we hold about you, have it corrected or erased, withdraw an agreement you gave, and nominate someone to act for you if you cannot. Use the support form and include the relevant request reference, without attaching identity or payment information. Withdrawing an agreement stops further preparation; it does not recall files already delivered to you.",
                },
                {
                    title: "Grievances",
                    text: "A complaint about how your data or an order was handled goes to our Grievance Officer. Raise it through the support form and begin the message with the word Grievance. It is acknowledged within 48 hours and resolved within one month.",
                },
            ]}
        />
    );
}
