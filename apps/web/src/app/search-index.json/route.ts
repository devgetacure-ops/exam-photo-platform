import { loadSearchIndex } from "../../lib/catalogue.server";

/**
 * The picker's index, as one static file.
 *
 * The header carries a search on every page, including 415 statically built
 * examination pages. Shipping the whole index inside each of those documents
 * would put the same tens of kilobytes into every one of them, to be used by
 * the small share of candidates who open the search at all.
 *
 * So it is built once, here, and fetched the first time somebody opens the
 * header search. It is prerendered at build time like every other page, which
 * means no server work per request and no dependency on the engine being up —
 * the same properties the exam pages have.
 */
export const dynamic = "force-static";

export async function GET() {
    const index = await loadSearchIndex();
    return Response.json(index, {
        headers: {
            "cache-control": "public, max-age=0, must-revalidate",
        },
    });
}
