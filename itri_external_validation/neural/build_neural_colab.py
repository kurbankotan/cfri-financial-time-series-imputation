"""Build the one-click, resumable BRITS/SAITS Colab notebook."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "ITRI_BRITS_SAITS_full_Colab.ipynb"
PRIVATE_SHA = "48dc63654f63db3ef9d6d5db7ab69ad502aa079e9f6deb4b276cf9b1170f324b"
CLASSICAL_SHA = "83b0c3959bb4d65a3a0ed09c30e50c76635879c69314488b7e768308af3d05f4"


def cell(kind: str, source: str, ident: str, collapsed: bool = False) -> dict:
    metadata = {"jupyter": {"source_hidden": True}} if collapsed else {}
    result = {"cell_type": kind, "metadata": metadata,
              "source": source.splitlines(True), "id": ident}
    if kind == "code":
        result.update({"execution_count": None, "outputs": []})
    return result


def source_cell(filename: str, ident: str) -> dict:
    source = (HERE / filename).read_text(encoding="utf-8")
    return cell("code", f"%%writefile /content/itri_neural/{filename}\n" + source,
                ident, collapsed=True)


def main() -> None:
    private_upload = f"""
import hashlib
from google.colab import files

print('FILE 1/2: Select ITRI_external_PRIVATE_data_snapshot.zip only.', flush=True)
uploaded = files.upload()
if len(uploaded) != 1:
    raise ValueError('Select exactly one file: ITRI_external_PRIVATE_data_snapshot.zip')
filename, content = next(iter(uploaded.items()))
if hashlib.sha256(content).hexdigest() != {PRIVATE_SHA!r}:
    raise ValueError(f'Wrong file selected: {{filename}}. Expected ITRI_external_PRIVATE_data_snapshot.zip')
snapshot_path = work_dir / 'PRIVATE_vendor_snapshot.zip'
snapshot_path.write_bytes(content)
del uploaded, content
print('Private data snapshot verified; raw OHLCV will stay outside Drive output.')
""".lstrip()
    classical_upload = f"""
print('FILE 2/2: Select ITRI_classical_full_results.zip only.', flush=True)
uploaded = files.upload()
if len(uploaded) != 1:
    raise ValueError('Select exactly one file: ITRI_classical_full_results.zip')
filename, content = next(iter(uploaded.items()))
if hashlib.sha256(content).hexdigest() != {CLASSICAL_SHA!r}:
    raise ValueError(f'Wrong file selected: {{filename}}. Expected ITRI_classical_full_results.zip')
classical_path = work_dir / 'ITRI_classical_full_results.zip'
classical_path.write_bytes(content)
del uploaded, content
print('Classical results verified; both input archives are ready.')
""".lstrip()
    run_code = """
import importlib
import sys

sys.path.insert(0, str(work_dir))
importlib.invalidate_caches()
import masking
importlib.reload(masking)
import run_classical_benchmark
importlib.reload(run_classical_benchmark)
import run_neural_benchmark
importlib.reload(run_neural_benchmark)
run_neural_benchmark.run(snapshot_path, classical_path, result_dir)
""".lstrip()
    analysis_code = """
import importlib
import analyze_all_benchmarks
importlib.reload(analyze_all_benchmarks)

analysis_dir = work_dir / 'analysis'
audit = analyze_all_benchmarks.run(classical_path, result_dir, analysis_dir)
print('Combined audit:', audit)
""".lstrip()
    download = """
import zipfile

result_zip = Path('/content/ITRI_all_methods_results.zip')
with zipfile.ZipFile(result_zip, 'w', compression=zipfile.ZIP_DEFLATED) as out:
    for path in result_dir.rglob('*'):
        if path.is_file():
            out.write(path, 'neural_results/' + str(path.relative_to(result_dir)))
    for path in analysis_dir.rglob('*'):
        if path.is_file():
            out.write(path, 'analysis/' + str(path.relative_to(analysis_dir)))
    for name in ('masking.py', 'run_classical_benchmark.py',
                 'run_neural_benchmark.py', 'analyze_all_benchmarks.py',
                 'NEURAL_PROTOCOL_v1.md'):
        out.write(work_dir / name, 'code_and_protocol/' + name)
    out.write(classical_path, 'classical_results/ITRI_classical_full_results.zip')
print('Complete:', result_zip.name, '— downloading now')
files.download(str(result_zip))
""".lstrip()
    notebook = {"nbformat": 4, "nbformat_minor": 5,
                "metadata": {"colab": {"name": OUTPUT.name, "provenance": []},
                             "kernelspec": {"name": "python3",
                                            "display_name": "Python 3"}},
                "cells": [
                    cell("markdown", "# ITRI external validation: BRITS and SAITS\n\n"
                         "Choose an A100 GPU runtime (high RAM optional), then Run all. "
                         "Upload **two files, one at a time**, when prompted: first "
                         "`ITRI_external_PRIVATE_data_snapshot.zip`, then "
                         "`ITRI_classical_full_results.zip`. They can be in different "
                         "folders. SHA-256 verifies both. Authorize Google Drive mount; "
                         "only metric checkpoints go there, not vendor OHLCV.\n\n"
                         "The frozen full grid requires 11,016 neural fits and may exceed "
                         "one Colab session. If disconnected, open the same notebook "
                         "again, Run all, reupload the same two ZIPs, and authorize "
                         "Drive. Verified condition checkpoints are reused. A final "
                         "download is offered only after all neural and combined "
                         "checks pass. Pilot results are not scientific results.",
                         "overview"),
                    cell("code", "%pip -q install pypots==1.5 numpy==2.1.3 "
                         "pandas==2.2.3 scipy==1.18.1 scikit-learn==1.6.1",
                         "install"),
                    cell("code", "from pathlib import Path\n"
                         "work_dir = Path('/content/itri_neural')\n"
                         "work_dir.mkdir(parents=True, exist_ok=True)\n"
                         "print('Working directory:', work_dir)", "prepare"),
                    source_cell("masking.py", "masking-source"),
                    source_cell("run_classical_benchmark.py", "classical-source"),
                    source_cell("run_neural_benchmark.py", "neural-source"),
                    source_cell("analyze_all_benchmarks.py", "analysis-source"),
                    source_cell("NEURAL_PROTOCOL_v1.md", "protocol-source"),
                    cell("markdown", "## File 1/2 — private data snapshot\n\n"
                         "Select **`ITRI_external_PRIVATE_data_snapshot.zip`** "
                         "from your computer. Select this file only. It is the "
                         "original audited data archive, not the QC receipt.",
                         "private-upload-instructions"),
                    cell("code", private_upload, "private-upload"),
                    cell("markdown", "## File 2/2 — completed classical results\n\n"
                         "Select **`ITRI_classical_full_results.zip`** from your "
                         "computer. Select this file only. Do not select an incomplete "
                         "classical run. The two files may be in different folders.",
                         "classical-upload-instructions"),
                    cell("code", classical_upload, "classical-upload"),
                    cell("code", "from google.colab import drive\n"
                         "drive.mount('/content/drive')\n"
                         "result_dir = Path('/content/drive/MyDrive/ITRI_neural_external_validation')\n"
                         "result_dir.mkdir(parents=True, exist_ok=True)\n"
                         "print('Resumable metric checkpoints:', result_dir)",
                         "drive-mount"),
                    cell("code", run_code, "run"),
                    cell("code", analysis_code, "analyze"),
                    cell("code", download, "download"),
                ]}
    OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print(OUTPUT, OUTPUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
