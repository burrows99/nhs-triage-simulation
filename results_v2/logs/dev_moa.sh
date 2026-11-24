#!/bin/bash
cd /Users/raunakburrows/hesta-dev/oss/research/nhs-triage-simulation/
until grep -q "^158 " results_v2/logs/specialists.log; do sleep 15; done
export MPLCONFIGDIR=$TMPDIR/mpl
.venv/bin/python -m v2.run sim --scenario base --seeds dev --arms moa_static,moa_load > results_v2/logs/dev_base_moa.log 2>&1
.venv/bin/python -m v2.run sim --scenario stress --seeds dev --arms moa_static,moa_load > results_v2/logs/dev_stress_moa.log 2>&1
echo done
