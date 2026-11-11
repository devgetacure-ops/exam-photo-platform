"use client";

import { createContext, useCallback, useContext, type ReactNode } from "react";
import type { Locale } from "../lib/i18n";

/**
 * The language the preparation tool speaks (DEC-129). English unless a Hindi
 * page wraps the tool in `<LocaleProvider locale="hi">`. Components keep each
 * English sentence beside its Hindi one, `tr("…", "…")`, so a reviewer reads
 * the pair together and a missing translation cannot pass unnoticed.
 */
const LocaleContext = createContext<Locale>("en");

export function LocaleProvider({ locale, children }: { locale: Locale; children: ReactNode }) {
    return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export function useLocale(): Locale {
    return useContext(LocaleContext);
}

/** `tr(english, hindi)`: the sentence in the tool's language. */
export function useTr(): (english: string, hindi: string) => string {
    const locale = useLocale();
    return useCallback((english: string, hindi: string) => (locale === "hi" ? hindi : english), [locale]);
}
