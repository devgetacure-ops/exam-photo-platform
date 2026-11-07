#!/usr/bin/env bash
# Daily backup of the operator console's records to Google Cloud Storage.
#
# The console's ledger (visits, orders, coupons, contacts, tickets) and the
# request-form messages live on Docker volumes on one VM. Losing the VM lost
# them once (Vultr, October 2026); this keeps a copy off the machine.
#
# Install (once, on the VM, from ~/euk):
#   BUCKET=gs://<name> deploy/ops/euk-backup.sh          # run it once by hand
#   (crontab -l 2>/dev/null; echo "30 21 * * * BUCKET=gs://<name> $HOME/euk/deploy/ops/euk-backup.sh >> $HOME/euk-backup.log 2>&1") | crontab -
#
# 21:30 UTC is 03:00 IST, the quietest hour. The bucket's lifecycle rule
# deletes copies after 90 days. Candidate photos are NOT backed up: they are
# promised deleted on their TTL, and a backup would break that promise.
set -euo pipefail

: "${BUCKET:?set BUCKET=gs://your-bucket}"
cd "$(dirname "$0")/../.."
COMPOSE="docker compose -f deploy/docker-compose.yml"
STAMP=$(date -u +%Y%m%d-%H%M)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# A consistent copy taken by SQLite itself, safe while the engine is writing.
$COMPOSE exec -T engine python -c "
import sqlite3
src = sqlite3.connect('/app/.tmp/artifacts/_ledger/ledger.sqlite3')
dst = sqlite3.connect('/tmp/ledger-backup.sqlite3')
src.backup(dst); dst.close(); src.close()
"
$COMPOSE cp engine:/tmp/ledger-backup.sqlite3 "$WORK/ledger.sqlite3"
$COMPOSE exec -T engine rm -f /tmp/ledger-backup.sqlite3

# The request form's messages, if any.
$COMPOSE cp web:/data/requests "$WORK/requests" 2>/dev/null || mkdir -p "$WORK/requests"

tar -czf "$WORK/euk-$STAMP.tar.gz" -C "$WORK" ledger.sqlite3 requests
gcloud storage cp --quiet "$WORK/euk-$STAMP.tar.gz" "$BUCKET/euk-$STAMP.tar.gz"
echo "$(date -u +%FT%TZ) backed up euk-$STAMP.tar.gz ($(du -h "$WORK/euk-$STAMP.tar.gz" | cut -f1))"
