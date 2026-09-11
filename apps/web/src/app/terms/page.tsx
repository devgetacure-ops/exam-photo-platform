import { PolicyPage } from "../../components/policy-page";
export const metadata = { title: "Service terms · examuploadkit" };
export default function Terms() {
    return (
        <PolicyPage
            title="Know what you’re getting."
            intro="The boundaries of exam upload preparation."
            sections={[
                {
                    title: "Preparation, with clear limits",
                    text: "The selected exam record determines file preparation. Requirements marked partially supported need additional attention; guidance-only, physical-stage and unsupported requirements cannot be completed through our upload controls. Final application acceptance belongs to the examination authority.",
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
            ]}
        />
    );
}
