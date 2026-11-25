#!/bin/bash
# v3 held-out evaluation (PREREG_V3.md section 4): seeds 2000-2029, run ONCE at the registration commit.
set -e
cd /Users/raunakburrows/hesta-dev/oss/research/nhs-triage-simulation/
export STUDY=v3 OLLAMA_HOST=http://127.0.0.1:11435 MPLCONFIGDIR=$TMPDIR/mpl
git rev-parse HEAD > results_v3/logs/heldout_commit.txt
git status --porcelain >> results_v3/logs/heldout_commit.txt
for sc in base stress base_review; do
  .venv/bin/python -m v2.run sim --scenario $sc --seeds heldout > results_v3/logs/heldout_${sc}.log 2>&1
done
.venv/bin/python -m v2.run fairness > results_v3/logs/fairness.log 2>&1
.venv/bin/python -m v2.run analyze --seeds heldout > results_v3/logs/analyze_heldout.log 2>&1
.venv/bin/python -m v2.explore heldout > /dev/null
echo done
