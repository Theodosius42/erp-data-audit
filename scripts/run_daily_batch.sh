#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

RUN_ID="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/daily_batch_${RUN_ID}.log"

{
  echo "[$(date --iso-8601=seconds)] Daily batch started"
  cd "${ROOT_DIR}"
  python3 -m pytest -q
  python3 -m pipeline
  python3 -m pam_pipeline
  echo "[$(date --iso-8601=seconds)] Daily batch completed"
} 2>&1 | tee "${LOG_FILE}"
