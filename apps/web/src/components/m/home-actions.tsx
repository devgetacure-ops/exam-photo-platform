"use client";

import { ActionBar } from "./action-bar";
import { openPhoneSearch } from "./search-screen";

/**
 * The two ways into search on the phone home. Client islands only because a
 * tap has to open the search from inside its own handler (see
 * `search-screen.tsx`); everything around them is server-rendered.
 */

export function FindButton() {
    return (
        <button type="button" className="euk-mhome-find" onClick={openPhoneSearch}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
                <circle cx="11" cy="11" r="7" />
                <path d="m20.5 20.5-4.2-4.2" />
            </svg>
            <span>
                <strong>Search your examination</strong>
                <span>SSC CGL, NEET UG, IBPS PO…</span>
            </span>
        </button>
    );
}

export function HomeAction() {
    return (
        <div className="euk-m-only">
            <ActionBar
                note={
                    <>
                        <strong>From ₹3</strong>
                        No account needed
                    </>
                }
            >
                <button type="button" className="primary-button" onClick={openPhoneSearch}>
                    Find my examination
                </button>
            </ActionBar>
        </div>
    );
}
