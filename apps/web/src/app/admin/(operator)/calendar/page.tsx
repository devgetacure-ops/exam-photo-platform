import { redirect } from "next/navigation";

/** The calendar is part of Exams now (DEC-136); old links land there. */
export default function CalendarPage() {
    redirect("/admin/exams?show=dates");
}
