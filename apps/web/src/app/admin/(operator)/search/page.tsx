import { redirect } from "next/navigation";

/**
 * The old search page (DEC-109). Search now lives in the console's top bar
 * (Ctrl K); an old link lands on the overview, where it opens.
 */
export default function SearchPage() {
    redirect("/admin");
}
