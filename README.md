# Turbofan Near-Anomaly Detection with CANARI

Label-free detection of *near-anomalies* (engines that still work but are drifting toward failure) on the NASA C-MAPSS turbofan dataset, using CANARI (Christoffel-function-based detection) and 12 baseline models.

Author: Prisha, VES. Mini project, Research Methodology.

## Problem
Can a detector trained only on healthy data warn about near-failure, and how close does it get to supervised models?

Each engine cycle is labelled from its remaining useful life (RUL):
- **normal**: RUL > 60
- **near_anomaly**: 15 < RUL <= 60
- **anomaly**: RUL <= 15

## Dataset
NASA C-MAPSS, subsets FD001 to FD004. The raw data is **not included**. Download it from the NASA Prognostics Data Repository (search "C-MAPSS") and set `DATA_DIR` in the preprocessing notebook.

## What is in this repo
- Preprocessing: per-condition standardization, KMeans operating conditions, engine-level 70/30 split, rolling-mean trend features (v2: 28 features).
- Label-free models: CANARI, One-Class SVM, Isolation Forest, LOF, Mahalanobis, Autoencoder, Hebbian (Sanger).
- Supervised references: Random Forest, MLP, Gradient Boosting, Logistic Regression, random floor.
- Paper-faithful variants (after Billet et al., DX 2026, arXiv 2607.26704):
  - **CANARI-paper**: PCA to 8 dims, growth-ratio score, the paper's threshold.
  - **CANARI-growth**: same score, quantile thresholds.
- Evaluation: macro-F1, near-anomaly F1, false alarm rate, PR-AUC, ROC-AUC, lead time, cutoff sensitivity, bootstrap confidence intervals.

## Files
| File | Purpose |
|---|---|
| `data preprocessing/preprocess.ipynb` | Loads data, labels, standardizes, builds features, saves a `run_*` folder |
| `models/common.py` | Shared models, tuning and metrics. Loads the newest run folder |
| `models/unsupervised.ipynb` | Trains and tunes label-free models |
| `models/supervised.ipynb` | Trains supervised models |
| `models/canari_paper.py` | CANARI-paper and CANARI-growth |
| `models/canari_paper.ipynb` | Runs the paper-faithful variants |
| `models/evaluation.ipynb` | Merges results, tables, plots, lead time, CIs |

## How to run
1. `pip install -r requirements.txt`
2. Set `DATA_DIR` and the output path in the preprocessing notebook, then run it.
3. Run `unsupervised`, `supervised`, `canari_paper`, then `evaluation`. Restart the kernel before each one so the newest run folder is used.
4. Check that `print(RUN.name, len(feats))` shows 28 features.

## Results (test engines, one run)
| Model | macro-F1 |
|---|---|
| MLP (supervised) | 0.839 |
| Random Forest (supervised) | 0.836 |
| **CANARI-growth** | **0.724** |
| One-Class SVM | 0.716 |
| CANARI (v2) | 0.651 |
| CANARI-paper | 0.564 |

95% CIs come from resampling engines. CANARI-growth beats CANARI by +0.075 [0.053, 0.098]. Versus One-Class SVM the gap is +0.010 [-0.006, 0.024], which is a tie.

**Takeaways**
- The growth-ratio score clearly improves on plain CANARI.
- It ties the best classic label-free baseline.
- The paper's own threshold is too cautious on RUL-based labels.
- Supervised models stay about 0.11 ahead.

## Limitations
- PCA stands in for the paper's CLOE autoencoder.
- The three-zone rule is our adaptation of the paper's two-zone rule.
- C-MAPSS is simulated data, with one split and one seed.
- Near-anomaly F1 here is not comparable with the paper's, because the tasks differ.

## Future work
Real CLOE autoencoder, higher-dimensional Christoffel approximations, sequence encoders, generative models for synthetic near-anomalies, few-label learning and real engine data.

## Citation
- Billet et al., DX 2026 (arXiv 2607.26704), the CANARI method.
- Saxena et al., 2008, the C-MAPSS dataset.

## Licence
MIT. See `LICENSE`.