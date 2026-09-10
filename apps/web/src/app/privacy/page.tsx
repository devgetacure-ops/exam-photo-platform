import { PolicyPage } from "../../components/policy-page";
export const metadata = { title: "Privacy · UploadReady" };
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
                    title: "Browser and payment records",
                    text: "This browser stores kit references so you can return before expiry, and your theme preference. Clearing browser data can lose those references. Payment is handled through Razorpay. Order and delivery evidence may be kept separately from temporary images to investigate payment and delivery issues.",
                },
                {
                    title: "Email and requests",
                    text: "An email address entered for file delivery is used to send the attachments; the preparation service records a masked address. Exam and support requests contain the contact details and text you explicitly submit. Requests are private, queued for review and assigned a 30-day retention deadline. Do not submit identity numbers, photographs, passwords or card details through the request form.",
                },
                {
                    title: "Questions and removal requests",
                    text: "Use the support form to ask about your information or request removal. Include the relevant request reference, without attaching sensitive identity or payment information.",
                },
            ]}
        />
    );
}
