# Package provenance

This CFRI repository package combines two public artifact archives without modifying their study source or result bytes.

| Input archive | SHA-256 | Role |
|---|---|---|
| `itri-financial-time-series-imputation-5059f6010d6f660e1744e1bb2710b18f4dbb4999.zip` | `05a40072429dd1c709941a602f2293aeaf801591ff33c89e5ea1c462d240dcad` | Complete public ITRI/CFRI commit `5059f6010d6f660e1744e1bb2710b18f4dbb4999`, including the fold D notebook, original frozen protocol, external neural materials, and derived results. |
| `CFRI_GitHub_candle_v1_exploratory.zip` | `7eeebfd15ef0b9dfce60207e208ba3e117a79e39d24a84b15d94540f4230a2e7` | Exploratory candle-coordinate source, notebook, results, and its own SHA manifest. |

The merger adds `cfri_candle_v1_exploratory/` and the root `NUMBERING_MAP.md`, `.gitattributes`, this provenance note, and `SHA256SUMS.txt`. It updates root `README.md`, `CITATION.cff`, `.gitignore`, and `.github/workflows/verify-results.yml`; the workflow now checks the candle package. Three presentation files accidentally nested in `paper_figures/` (`README.md`, `CITATION.cff`, `.gitignore`) were removed in favor of the authoritative root files. Every other historical file and every candle file is byte-identical to its source archive.

The public commit followed fold D data acquisition, as explained in `cfri_confirmatory/DEVIATIONS.md`. Publication of this combined package does not create a public pre-run timestamp for any historical study.

After the initial merger, only root `README.md`, `NUMBERING_MAP.md`, and the workflow step labels were revised to match the CFRI-first manuscript draft: main Tables 1–2, no main figures, and Supplementary Tables S1–S28 and Figures S1–S7. The study code, protocols, notebooks, scores, receipts, and figures remain byte-identical to their input archives; the root SHA manifest was regenerated for these documentation changes.
