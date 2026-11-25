#!/bin/bash
# v3 development runs (seeds 100-119), all arms; outside the sandbox (localhost LLM server)
cd /Users/raunakburrows/hesta-dev/oss/research/nhs-triage-simulation/
export STUDY=v3 OLLAMA_HOST=http://127.0.0.1:11435
for sc in base stress base_review; do
  .venv/bin/python -m v2.run sim --scenario $sc --seeds dev > results_v3/logs/dev_${sc}.log 2>&1
done
echo done
