# Original ITRI baseline (historical snapshot)

This directory preserves the original Iterative Temporal Regression
Imputation ablation's source code, Colab notebook, derived result tables,
metadata and figures. The source and result files were copied byte-for-byte
from the earlier public-repository working tree. Only this landing page was
written for the CFRI repository. The older README is retained as
`README_original.md`; its links point to the earlier ITRI repository.

Run the verification script from this directory after installing
`requirements.txt`:

```bash
python scripts/verify_published_results.py
```

The original BIST 30/S&P 500 study developed ITRI. It is not a 2026 CFRI
confirmation and its mask protocol differs from the later external studies.
