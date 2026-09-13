import { serializeJsonLd } from "../lib/site";

/** Structured data for search and answer engines (DEC-087). Renders nothing visible. */
export function JsonLd({ data }: { data: object }) {
    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: serializeJsonLd(data) }}
        />
    );
}
