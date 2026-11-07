# Package provenance

The following source archives were combined without editing their study code
or reported result files:

| Source artifact | SHA-256 | Material |
|---|---|---|
| `CFRI_GitHub_code_v12.zip` | `184783bf8d3ac592282fa2c99b38d573147e958f3f644525ba0d52eb9b6750e2` | Confirmatory Fold D and new-asset holdout directories. |
| `CFRI_GitHub_candle_v1_exploratory.zip` | `7eeebfd15ef0b9dfce60207e208ba3e117a79e39d24a84b15d94540f4230a2e7` | Exploratory candle directory. |
| `ITRI_External_Validation_Public_Code_Stage2.zip` | `b656f6cebc7161f6f6530a4a3da05e8a0a5dc31648af784ba6e9ebebe203beab` | Historical classical external-validation source. |
| `ITRI_BRITS_SAITS_code_package.zip` | `8228c71ce0e98172efab10bbeaf7add0f0e407677bc2f18fd39dd0497e2b3a60` | Historical neural comparator source. |

The historical ITRI baseline was copied from the local
`github_itri_repo` working tree, excluding `.git`, generated Python caches
and the old GitHub workflow. Its original README is preserved under
`itri_baseline/README_original.md`.

For convenience, the neural external-validation folder also carries exact
copies of the classical package's asset-universe manifest, protocol and
snapshot audit, which its historical README references.

`SHA256SUMS.txt` records all public files after packaging. The study archives
retain their own receipts and source digests. This new bundle changes
repository presentation only; it does not alter study outcomes or upgrade
exploratory analyses into independent confirmation.
