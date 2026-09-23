/**
 * Shapes and sums for the operator page (DEC-108). Pure, so they are tested
 * without an engine; the page fetches and these decide what the numbers are.
 */

export interface OrderDelivery {
    at: string;
    job_id: string;
    method: string;
    succeeded: boolean;
    masked_address?: string | null;
    /** DEC-109: the full address, kept on the owner's decision. */
    address?: string | null;
    error?: string | null;
}

export interface OrderItem {
    job_id: string;
    exam_id?: string | null;
    exam_name?: string | null;
    requirement_name?: string | null;
    requirement_type?: string | null;
}

export interface Order {
    order_id: string;
    kit_id: string;
    job_ids: string[];
    amount_paise: number;
    currency: string;
    created_at: string;
    paid_at?: string | null;
    payment_reference?: string | null;
    delivered_at?: string | null;
    delivery_method?: string | null;
    items?: OrderItem[];
    deliveries?: OrderDelivery[];
}

export interface OperatorJob {
    job_id: string;
    status: string;
    created_at: string;
    updated_at: string;
    expires_at: string;
    kit_id?: string | null;
    exam_id?: string | null;
    exam_name?: string | null;
    requirement_id?: string | null;
    requirement_name?: string | null;
    requirement_type?: string | null;
    outcome?: string | null;
    findings?: string[];
    issue_codes?: string[];
    changes?: string[];
    is_valid?: boolean | null;
    released?: boolean;
    entitlement?: string;
    output_filename?: string | null;
    preview_filename?: string | null;
    output_width?: number | null;
    output_height?: number | null;
    output_byte_size?: number | null;
    output_media_type?: string | null;
    download_count?: number;
    first_downloaded_at?: string | null;
    email_attempts?: { at: string; masked_address: string; succeeded: boolean; error?: string | null }[];
    payment_reference?: string | null;
    released_at?: string | null;
    files?: { name: string; bytes: number }[];
    report?: unknown;
    [key: string]: unknown;
}

export interface UsageSummary {
    kits: number;
    preparations: number;
    kits_that_purchased: number;
    conversion_rate: number | null;
    preparations_per_kit: { median?: number; p90?: number; p99?: number; max?: number };
    heaviest_kits: { kit_id: string; preparations: number; purchases: number }[];
}

export interface Health {
    status: string;
    disk?: { free_bytes: number; total_bytes: number } | null;
    [key: string]: unknown;
}

/** The owner's refund rule: paid, and nothing reached the candidate. */
export function refundDue(order: Order): boolean {
    return Boolean(order.paid_at) && !order.delivered_at;
}

export function orderState(order: Order): "refund-due" | "delivered" | "paid" | "unpaid" {
    if (refundDue(order)) return "refund-due";
    if (order.delivered_at) return "delivered";
    if (order.paid_at) return "paid";
    return "unpaid";
}

export interface Revenue {
    todayPaise: number;
    weekPaise: number;
    monthPaise: number;
    allPaise: number;
    paidOrders: number;
    unpaidOrders: number;
    refundDue: number;
    refundDuePaise: number;
}

const DAY = 86_400_000;

/** Money from paid orders only; "today" is the calendar day in India. */
export function revenue(orders: Order[], now: number = Date.now()): Revenue {
    const istDay = (t: number) => new Date(t + 5.5 * 3600_000).toISOString().slice(0, 10);
    const today = istDay(now);
    const totals: Revenue = {
        todayPaise: 0,
        weekPaise: 0,
        monthPaise: 0,
        allPaise: 0,
        paidOrders: 0,
        unpaidOrders: 0,
        refundDue: 0,
        refundDuePaise: 0,
    };
    for (const order of orders) {
        if (!order.paid_at) {
            totals.unpaidOrders += 1;
            continue;
        }
        const paid = Date.parse(order.paid_at);
        const amount = order.amount_paise;
        totals.paidOrders += 1;
        totals.allPaise += amount;
        if (Number.isFinite(paid)) {
            if (istDay(paid) === today) totals.todayPaise += amount;
            if (now - paid < 7 * DAY) totals.weekPaise += amount;
            if (now - paid < 30 * DAY) totals.monthPaise += amount;
        }
        if (refundDue(order)) {
            totals.refundDue += 1;
            totals.refundDuePaise += amount;
        }
    }
    return totals;
}

export function rupees(paise: number): string {
    const value = paise / 100;
    return `₹${value.toLocaleString("en-IN", {
        minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
        maximumFractionDigits: 2,
    })}`;
}

export function bytes(size: number | null | undefined): string {
    if (size == null) return "—";
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    if (size < 1024 ** 3) return `${(size / 1024 / 1024).toFixed(1)} MB`;
    return `${(size / 1024 ** 3).toFixed(1)} GB`;
}

export function when(stamp: string | null | undefined): string {
    if (!stamp) return "—";
    const parsed = Date.parse(stamp);
    if (!Number.isFinite(parsed)) return stamp;
    return new Date(parsed).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

/** A job's pictures, source first, for the upload detail page. */
export function pictureFiles(job: OperatorJob): string[] {
    const names = (job.files ?? []).map((file) => file.name);
    const pictures = names.filter((name) => /\.(jpe?g|png|webp)$/i.test(name));
    const rank = (name: string) =>
        name.startsWith("input") ? 0 : name === job.output_filename ? 1 : name.includes("preview") ? 3 : 2;
    return pictures.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
}

/** Only a job id and a plain file name may reach the engine's file route. */
export function safeFileRequest(jobId: string, name: string): boolean {
    return /^job_[A-Za-z0-9_-]+$/.test(jobId) && /^[A-Za-z0-9_.-]{1,200}$/.test(name) && !name.includes("..");
}

// --- Release 1 (DEC-109) ------------------------------------------------------

export interface OrderView extends Order {
    state: string;
    emails: string[];
    exam_names: string[];
    refund?: { at: string; actor: string; reference?: string | null; amount_paise?: number | null } | null;
    payer_email?: string | null;
    payer_contact?: string | null;
    payment_method?: string | null;
    failed_payments?: {
        at?: string | null;
        error?: string | null;
        email?: string | null;
        contact?: string | null;
        method?: string | null;
    }[];
}

export interface UploadRow {
    job_id: string;
    kit_id?: string | null;
    exam_id?: string | null;
    exam_name?: string | null;
    requirement_name?: string | null;
    requirement_type?: string | null;
    started_at: string;
    finished_at?: string | null;
    status: string;
    outcome?: string | null;
    findings?: string[] | null;
    issue_codes?: string[] | null;
    input_bytes?: number | null;
    output_width?: number | null;
    output_height?: number | null;
    output_bytes?: number | null;
    processing_seconds?: number | null;
    stage_ms?: Record<string, number> | null;
    error?: string | null;
    live?: boolean;
}

export interface Ticket {
    id: string;
    reference?: string | null;
    kind: string;
    exam?: string | null;
    email?: string | null;
    message?: string | null;
    payment_reference?: string | null;
    order_id?: string | null;
    created_at: string;
    status: string;
    acknowledged_at?: string | null;
    resolved_at?: string | null;
    added_at?: string | null;
    ack_overdue: boolean;
    resolve_overdue: boolean;
}

export interface Note {
    at: string;
    actor: string;
    text: string;
}

export interface OrderDetail extends OrderView {
    uploads: UploadRow[];
    kit_uploads: UploadRow[];
    tickets: Ticket[];
    notes: Note[];
    timeline: { at: string; what: string }[];
}

export interface Customer {
    email: string;
    phone?: string | null;
    first_seen: string;
    last_seen: string;
    sources: string[];
    spent_paise?: number;
    paid_orders?: number;
}

export interface CustomerDetail {
    email: string;
    contact: Customer | null;
    orders: OrderView[];
    tickets: Ticket[];
    uploads: UploadRow[];
    spent_paise: number;
    notes: Note[];
}

export interface ExamStats {
    exam: string;
    uploads: number;
    prepared: number;
    failed: number;
    kits: number;
    kits_paid: number;
    conversion: number | null;
    revenue_paise: number;
    top_reasons: [string, number][];
}

export interface Overview {
    days: number;
    money: {
        all_time_paise: number;
        period_paise: number;
        today_paise: number;
        paid_orders: number;
        refunded_paise: number;
        refunded_orders: number;
        average_order_paise: number;
    };
    series: { day: string; revenue_paise: number; orders: number; uploads: number }[];
    uploads_by_hour_ist: number[];
    preparation_seconds: {
        count: number;
        median: number | null;
        p95: number | null;
        max: number | null;
        stages_median_ms: Record<string, number>;
    };
    uploads: { total: number; prepared: number; failed: number; busy: number };
    exams: ExamStats[];
    customers: { payers: number; repeat_payers: number; contacts: number };
    refund_due: OrderView[];
    refund_review: OrderView[];
    stuck: UploadRow[];
    followups: OrderView[];
    unpaid_kits: number;
    tickets: { open: number; overdue: Ticket[]; exam_requests_open: number };
    health: { at: string; status: string; disk_free_bytes: number | null; busy_refusals: number }[];
}

export function seconds(value: number | null | undefined): string {
    return value == null ? "—" : `${value.toFixed(1)} s`;
}

export function percent(value: number | null | undefined): string {
    return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

/** Only paths inside the operator page may be redirected back to. */
export function safeBack(value: unknown, fallback = "/admin"): string {
    const text = typeof value === "string" ? value : "";
    return /^\/admin(\/|\?|#|$)/.test(text) && !text.startsWith("//") && !text.includes("\\")
        ? text
        : fallback;
}
