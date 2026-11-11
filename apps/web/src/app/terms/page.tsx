import { pageMetadata } from "../../lib/site";
import { PolicyPage } from "../../components/policy-page";
export const metadata = pageMetadata({
    title: "Terms of use",
    description:
        "What ExamUploadKit prepares, its limits, and the terms of using a free service.",
    path: "/terms",
});
export default function Terms() {
    return (
        <PolicyPage
            title="Know what you’re getting."
            intro="ExamUploadKit is free to use. These are the terms that come with it."
            sections={[
                {
                    title: "What it does, and its limits",
                    text: "The examination you choose decides how each file is prepared. Requirements marked partially supported need extra attention, and some steps can only be done by you. The examination authority alone decides whether to accept a file, and we cannot promise that it will.",
                },
                {
                    title: "Check before you submit",
                    text: "Make sure the examination and its cycle are the ones you are applying for, and check each prepared file against your official instructions. Where we estimated a value rather than read it from a notice, the page says so. You must have permission to upload the files you provide.",
                },
                {
                    title: "Save before expiry",
                    text: "Files are available until the deadline shown in your kit. Save them before then. Deleted files cannot be restored.",
                },
                {
                    title: "Use responsibly",
                    text: "Do not use this service to impersonate another person, falsify documents, harm the service or submit files you are not allowed to use.",
                },
                {
                    title: "Your agreement",
                    text: "Before your first file is prepared you tick one box agreeing to these terms and the privacy policy. If the candidate is under 18, it also confirms that a parent or guardian agrees. If you upload a thumb impression, it confirms you agree to it being processed only to prepare that file.",
                },
                {
                    title: "Free, and supported by advertising",
                    text: "There is no charge for any file. The site may show advertising to pay for itself. Advertising never touches your uploads or prepared files.",
                },
                {
                    title: "Our responsibility",
                    text: "The service is provided free and as it is. To the extent the law allows, we are not liable for any loss arising from its use, including a missed deadline or an application an authority rejects. Nothing here limits a right you have under the Consumer Protection Act, 2019.",
                },
                {
                    title: "An independent service",
                    text: "ExamUploadKit is independent. It is not connected with or endorsed by any examination authority named on this site; their names only identify the examination you are applying to.",
                },
                {
                    title: "Law and disputes",
                    text: "These terms are governed by the laws of India. Subject to your rights under consumer protection law, the courts at Baripada, Odisha have jurisdiction over any dispute arising from them.",
                },
                {
                    title: "Changes to these terms",
                    text: "These terms were last updated on 11 November 2026, when the service became free.",
                },
            ]}
        />
    );
}
