/** Short Indian dates for the console (DEC-113): "Today 12:06" or "24 Sep, 12:06". Usable on server and client. */
export function when(stamp?: string | null): string {
    if (!stamp) return "—";
    const date = new Date(stamp);
    if (Number.isNaN(date.getTime())) return stamp;
    const zone = { timeZone: "Asia/Kolkata" } as const;
    const sameDay = date.toLocaleDateString("en-IN", zone) === new Date().toLocaleDateString("en-IN", zone);
    return sameDay
        ? `Today ${date.toLocaleTimeString("en-IN", { ...zone, hour: "2-digit", minute: "2-digit" })}`
        : date.toLocaleString("en-IN", { ...zone, day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}
