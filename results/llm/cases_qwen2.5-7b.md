## Repo-case evaluation (30 of 237 cases), qwen2.5:7b

Ground truth = the ground_truth_route column of data/nhs_ecds_aligned_routing_dataset.csv (script-derived, not expert-reviewed). Accuracy with Wilson 95% CI. rule_based = always physician-first.

| group | n | rule_based | single | moa |
|---|---|---|---|---|
| all | 30 | 100.0% [88.6, 100.0] | 100.0% [88.6, 100.0] | 100.0% [88.6, 100.0] |
| F asian | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |
| F black | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |
| F white | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |
| M asian | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |
| M black | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |
| M white | 5 | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] | 100.0% [56.6, 100.0] |

| arm | parity gap (max - min group accuracy) | max delta_g = max abs(acc_g - mean acc_g) | invalid outputs | routes |
|---|---|---|---|---|
| rule_based | 0.0 pp | 0.0 pp | 0 | {} |
| single | 0.0 pp | 0.0 pp | 0 | {'doctor': 30, 'mri': 0, 'ultrasound': 0, 'invalid': 0} |
| moa | 0.0 pp | 0.0 pp | 0 | {'doctor': 30, 'mri': 0, 'ultrasound': 0, 'invalid': 0} |
