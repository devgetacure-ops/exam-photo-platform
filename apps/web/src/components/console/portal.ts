"use client";

import { useSyncExternalStore } from "react";

/**
 * Where the console's dialogs and panels render. Radix puts them at the end of
 * <body> by default, outside `.op-root`, where the theme's colour tokens do
 * not reach; rendering them inside it keeps light and dark correct.
 */
const noSubscription = () => () => undefined;

export function useConsoleRoot(): HTMLElement | null {
    return useSyncExternalStore(
        noSubscription,
        () => document.querySelector<HTMLElement>(".op-root"),
        () => null,
    );
}
