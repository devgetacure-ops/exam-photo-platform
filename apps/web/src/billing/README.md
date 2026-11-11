# Billing (switched off)

ExamUploadKit is free and paid for by advertising (DEC-127). Everything the
site used to charge for files lives in this folder, untouched, so going back
to paid is a configuration change rather than a rebuild.

| File | What it did |
|---|---|
| `config.ts` | `BILLING_ENABLED`, the one switch. Read from `NEXT_PUBLIC_BILLING`. |
| `kit-checkout.tsx` | Review, total, coupon, Razorpay checkout, failure and paid-delivery screens. |
| `payment-scene.tsx` | The screen shown while Razorpay's window is open. |
| `simulated-checkout.tsx` | The test payment sheet for machines running the engine's simulator. |
| `review-panel.tsx` | The review box on a paid order, with the free-files reward. |
| `kit-pricing.ts` | The price ladder the kit card and the phone bar display. |

Outside this folder, the only places that still read billing are guarded by
`BILLING_ENABLED`: the kit workspace and the phone flow (they render
`KitCheckout` instead of `KitDownloads`), the price card and bar, preview
captions, the feedback page, and the console's coupon page.

## Turning paid back on

1. Site: set `NEXT_PUBLIC_BILLING=on` in `deploy/.env` and rebuild
   (`docker compose up -d --build`).
2. Engine: set `EXAM_PHOTO_BILLING=on` with the Razorpay keys and webhook
   secret. The engine's half is `services/image-engine/src/exam_photo/api/billing/`.
3. Put Razorpay's hosts back in the CSP in `deploy/Caddyfile`.
4. Restore the paid copy that was rewritten rather than switched: the landing
   page's pricing section, the WE vs AI price cards, the terms' payment
   sections, the refund policy page, the support page's payment answers and
   `llms.txt`. All of it is in git history at the DEC-127 commit.
