"use client";

import { useCallback, useSyncExternalStore } from "react";

import { getKit, recordPreparation, type KitEntry } from "../../lib/kit-state";
import type { PrepareRequirementResponse } from "../../lib/types";

/**
 * The kit as React state.
 *
 * `kit-state.ts` owns the data; this subscribes a component tree to it, so the
 * file list on the left updates the moment a file on the right finishes.
 *
 * `useSyncExternalStore` rather than an effect: `localStorage` is an external
 * store, and this is the API built for one. It also settles the server/client
 * split cleanly — `getServerSnapshot` returns the empty map, which is both what
 * the server can know and the correct state for a candidate who has uploaded
 * nothing, so the prerendered markup and the first client paint agree.
 *
 * The snapshot is cached per examination because `useSyncExternalStore`
 * compares snapshots by identity: returning a fresh object each call would
 * re-render forever.
 */

type Entries = Record<string, KitEntry>;

const EMPTY: Entries = {};

const listeners = new Set<() => void>();
const cache = new Map<string, Entries>();

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  // Another tab writing to the same store is a real case — a candidate with
  // the exam open twice — and `storage` is how the browser reports it.
  const onStorage = () => {
    cache.clear();
    listeners.forEach((notify) => notify());
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function snapshotFor(examId: string): Entries {
  const cached = cache.get(examId);
  if (cached) return cached;
  const entries = getKit(examId)?.requirements ?? EMPTY;
  cache.set(examId, entries);
  return entries;
}

export function useKit(examId: string) {
  const entries = useSyncExternalStore(
    subscribe,
    () => snapshotFor(examId),
    () => EMPTY
  );

  const record = useCallback(
    (response: PrepareRequirementResponse, examName?: string) => {
      const kit = recordPreparation(examId, response, examName);
      // A new object identity is what tells `useSyncExternalStore` to re-render.
      cache.set(examId, { ...kit.requirements });
      listeners.forEach((notify) => notify());
    },
    [examId]
  );

  return { entries, record };
}
