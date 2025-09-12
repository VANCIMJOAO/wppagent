#!/usr/bin/env bash
set -euo pipefail

has(){ command -v "$1" >/dev/null 2>&1; }
hash_if(){ [[ -f "$1" ]] && sha256sum "$1" | awk '{print $1}'; }

BACKEND_COMMIT=$(has git && git rev-parse HEAD 2>/dev/null || echo "unknown")
BACKEND_TREE=$(has git && git rev-parse HEAD:app 2>/dev/null || echo "unknown")
FRONTEND_TREE=$(has git && git rev-parse HEAD:nextjs_dashboard 2>/dev/null || echo "unknown")

if has alembic; then
  ALEMBIC_HEAD=$(alembic current 2>/dev/null | grep -oE '[0-9a-f]{6,}' | tail -n1 || true)
fi
if [[ -z "${ALEMBIC_HEAD:-}" ]]; then
  if ls alembic/versions/*.py >/dev/null 2>&1; then
    ALEMBIC_HEAD=$(ls -1 alembic/versions/*.py | sort | tail -n1 | sed -E 's#.*/([0-9a-f]+)_.*#\1#')
  else
    ALEMBIC_HEAD="unknown"
  fi
fi

REQS_HASH=$(hash_if requirements.txt)
[[ -z "${REQS_HASH}" ]] && REQS_HASH=$(hash_if pyproject.toml)
[[ -z "${REQS_HASH}" ]] && REQS_HASH=$(hash_if poetry.lock)
[[ -z "${REQS_HASH}" ]] && REQS_HASH="unknown"

LOCK_HASH=""
for f in nextjs_dashboard/pnpm-lock.yaml nextjs_dashboard/package-lock.json nextjs_dashboard/yarn.lock; do
  if [[ -f "$f" ]]; then LOCK_HASH=$(sha256sum "$f" | awk '{print $1}'); break; fi
done
[[ -z "${LOCK_HASH}" ]] && LOCK_HASH="unknown"

BACKEND_KEY="${BACKEND_TREE}"
[[ "${BACKEND_KEY}" == "unknown" ]] && BACKEND_KEY="${BACKEND_COMMIT}"
AUDIT_ID="${BACKEND_KEY}-${FRONTEND_TREE}-${ALEMBIC_HEAD}"

echo "SNAPSHOT"
echo "BACKEND_COMMIT=${BACKEND_KEY}"
echo "FRONTEND_COMMIT=${FRONTEND_TREE}"
echo "ALEMBIC_HEAD=${ALEMBIC_HEAD}"
echo "REQS_HASH=${REQS_HASH}"
echo "LOCK_HASH=${LOCK_HASH}"
echo
printf '%s\n' "JSON:"
cat <<JSON
{
  "audit_id": "${AUDIT_ID}",
  "snapshot": {
    "backend_commit": "${BACKEND_KEY}",
    "frontend_commit": "${FRONTEND_TREE}",
    "alembic_head": "${ALEMBIC_HEAD}",
    "reqs_hash": "${REQS_HASH}",
    "lock_hash": "${LOCK_HASH}"
  }
}
JSON
