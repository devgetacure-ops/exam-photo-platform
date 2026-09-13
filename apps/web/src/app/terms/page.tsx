import { pageMetadata } from "../../lib/site";
import { PolicyPage } from "../../components/policy-page";
export const metadata = pageMetadata({
    title: "Terms and conditions",
    description:
        "What examuploadkit prepares, how payment and delivery work, and the terms of using the service.",
    path: "/terms",
});
export default function Terms() {
    return (
        <PolicyPage
            title="Know what you’re getting."
            intro="The boundaries of exam upload preparation."
            sections={[
                {
                    title: "Preparation, with clear limits",
                    text: "The selected exam record determines file preparation. Requirements marked partially supported need additional attention; guidance-only, physical-stage and unsupported requirements cannot be completed through our upload controls. Final application acceptance belongs to the examination authority, and we do not guarantee that any authority will accept a prepared file.",
                },
                {
                    title: "Review before payment",
                    text: "Before you pay, make sure the examination and its cycle are the ones you are applying for, and look at each prepared preview against your official instructions. Where we estimated a value rather than read it from a notice, the page says so. PDF previews are not currently available. You must have permission to upload and process the files you provide.",
                },
                {
                    title: "Price and release",
                    text: "The itemized server quote determines your payment. Only confirmed payment releases chargeable files. A payment window closing does not establish whether payment succeeded. Refresh the kit status before trying again.",
                },
                {
                    title: "Save before expiry",
                    text: "Files have a temporary availability window shown before payment and on delivery. Save released downloads before that deadline. Extensions must be requested while a file is still available. Deleted files cannot be restored.",
                },
                {
                    title: "Use responsibly",
                    text: "Do not use this service to impersonate another person, falsify documents, compromise the service or submit files you are not authorized to use. The service prepares existing files; it does not create evidence of eligibility or admission.",
                },
                {
                    title: "Candidates under 18",
                    text: "If the candidate is under 18, a parent or legal guardian must agree to their files being prepared and to these terms. That agreement is given before the first file is uploaded, and the parent or guardian is responsible for the use of the service on the candidate's behalf.",
                },
                {
                    title: "Our responsibility",
                    text: "Our total liability for any claim relating to a kit is limited to the amount paid for that kit. We are not liable for indirect or consequential loss, including a missed application deadline or an application an authority rejects. Nothing in these terms limits a right you have under the Consumer Protection Act, 2019.",
                },
                {
                    title: "An independent service",
                    text: "examuploadkit is an independent service run by a sole proprietor in India. It is not connected with, authorised by or endorsed by any examination authority, board, commission or recruitment body named on this site. Their names are used only to identify the examination you are applying to.",
                },
                {
                    title: "Law and disputes",
                    text: "These terms are governed by the laws of India. Subject to your rights under consumer protection law, the courts at Baripada, Odisha have jurisdiction over any dispute arising from them.",
                },
                {
                    title: "Changes to these terms",
                    text: "These terms were last updated on 13 September 2026. If they change in substance, the upload asks you to agree to them again before your next file.",
                },
            ]}
        />
    );
}
