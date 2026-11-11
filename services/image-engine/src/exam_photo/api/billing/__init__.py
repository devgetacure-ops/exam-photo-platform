"""Everything the site needs to charge for its files, kept under one roof.

DEC-127 made ExamUploadKit free and paid for by advertising. Nothing that
took money was deleted: it lives here, switched off, so going back to paid is
a configuration change rather than a rebuild.

What is in this package
-----------------------
- ``pricing``          the price ladder, coupons as discounts, the A/B price test
- ``orders``           the order register (one order per payment attempt)
- ``razorpay_orders``  creating orders at Razorpay, at a price computed here
- ``payments``         verifying Razorpay's signed webhook and reading it
- ``routes``           every HTTP route that quotes, charges, refunds, issues
                       or redeems a coupon, or takes a review of a paid order

What stays outside, deliberately
--------------------------------
- The purchase gate itself (``ApiProcessingService.output_is_released``) and
  the watermark (``exam_photo.preview``). They read the switch below.
- Read-only console views of past orders and coupons, so the history stays
  visible while billing is off.

Turning paid back on
--------------------
Engine: set ``EXAM_PHOTO_BILLING=on`` with the Razorpay variables
(``EXAM_PHOTO_RAZORPAY_KEY_ID``, ``..._KEY_SECRET``, ``..._WEBHOOK_SECRET``).
Site: set ``NEXT_PUBLIC_BILLING=on`` and rebuild; the site's own half is in
``apps/web/src/billing/``. Restore Razorpay in the Caddy CSP
(``deploy/Caddyfile``). Then restore the refund policy and the paid wording in
the terms, both kept in git history at the DEC-127 commit.

With billing off every route in ``routes`` answers 404, files are released as
soon as they are prepared, and previews carry no mark.
"""
