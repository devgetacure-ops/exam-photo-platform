/**
 * Installing the site to a phone's home screen: the state, kept out of React.
 *
 * A candidate comes back several times — to prepare, to pay, to download, and
 * again for their next examination — and an icon on the home screen saves
 * them finding the site each time. The site is already installable (a
 * manifest, icons, HTTPS); what this adds is being asked at the right moment.
 *
 * The rules, in one place:
 *
 * - Never on arrival. An install request before a candidate has seen the
 *   product do anything is noise, and a dismissed browser prompt may not come
 *   back.
 * - Once, after something useful has happened: a file prepared, a kit
 *   delivered, a PDF converted. Those call `markInstallMoment`.
 * - "Not now" is remembered for thirty days. Installing is remembered for
 *   good.
 * - Android's browser hands over an install event, held from the first
 *   script on the page because it can arrive before React does. Safari hands
 *   over nothing, so an iPhone is told the two steps instead, and is never
 *   shown a button that cannot work.
 * - Nothing here claims the app works offline. It does not.
 */

export interface BeforeInstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform?: string }>;
}

declare global {
    interface Window {
        __eukInstallPrompt?: BeforeInstallPromptEvent | null;
    }
}

/** The install state may have changed: an event arrived, or was used. */
export const INSTALL_READY = "euk:install-ready";
/** Something useful just happened for the candidate. */
export const INSTALL_MOMENT = "euk:install-moment";

const DISMISSED_KEY = "uploadready:install-dismissed-at";
const INSTALLED_KEY = "uploadready:installed";

/** How long "Not now" holds. */
export const DISMISS_FOR_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * Registered from the document head, before any bundle loads, so the event is
 * never missed. It stops the browser's own mini-bar, which would otherwise
 * ask on arrival; the site asks after a useful moment instead, and the menu
 * offers it at any time.
 */
export const INSTALL_LISTENER_SCRIPT =
    "window.__eukInstallPrompt=null;" +
    "window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();window.__eukInstallPrompt=e;window.dispatchEvent(new Event('euk:install-ready'))});" +
    "window.addEventListener('appinstalled',function(){window.__eukInstallPrompt=null;try{localStorage.setItem('uploadready:installed','1')}catch(e){}window.dispatchEvent(new Event('euk:install-ready'))});";

export type InstallMode = "prompt" | "ios" | null;

function read(key: string): string | null {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}

function write(key: string, value: string): void {
    try {
        localStorage.setItem(key, value);
    } catch {
        // Storage blocked: the choice holds for this visit only.
    }
}

export function isStandalone(): boolean {
    if (typeof window === "undefined") return false;
    const nav = navigator as Navigator & { standalone?: boolean };
    if (nav.standalone === true) return true;
    return typeof window.matchMedia === "function"
        ? window.matchMedia("(display-mode: standalone)").matches
        : false;
}

export function isIos(
    userAgent: string = typeof navigator === "undefined" ? "" : navigator.userAgent,
    maxTouchPoints: number = typeof navigator === "undefined" ? 0 : navigator.maxTouchPoints ?? 0,
): boolean {
    if (/iPad|iPhone|iPod/.test(userAgent)) return true;
    // iPadOS reports itself as a Mac, and is the only Mac with a touch screen.
    return /Macintosh/.test(userAgent) && maxTouchPoints > 1;
}

export function wasInstalled(): boolean {
    return read(INSTALLED_KEY) === "1";
}

export function recentlyDismissed(now: number = Date.now()): boolean {
    const at = Number(read(DISMISSED_KEY));
    return Number.isFinite(at) && at > 0 && now - at < DISMISS_FOR_MS;
}

export function rememberDismissal(now: number = Date.now()): void {
    write(DISMISSED_KEY, String(now));
}

/** What installing looks like on this browser, right now, if anything. */
export function installMode(): InstallMode {
    if (typeof window === "undefined") return null;
    if (isStandalone() || wasInstalled()) return null;
    if (window.__eukInstallPrompt) return "prompt";
    if (isIos()) return "ios";
    return null;
}

/** Call when something useful has just happened for the candidate. */
export function markInstallMoment(): void {
    if (typeof window === "undefined") return;
    window.dispatchEvent(new Event(INSTALL_MOMENT));
}

/** Show the browser's own install dialog. An event can be used once. */
export async function promptInstall(): Promise<"accepted" | "dismissed" | "unavailable"> {
    const event = typeof window === "undefined" ? null : window.__eukInstallPrompt;
    if (!event) return "unavailable";
    window.__eukInstallPrompt = null;
    await event.prompt();
    const { outcome } = await event.userChoice;
    if (outcome === "accepted") write(INSTALLED_KEY, "1");
    window.dispatchEvent(new Event(INSTALL_READY));
    return outcome;
}
