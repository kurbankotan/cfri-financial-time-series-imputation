"""Build a readable Colab notebook that requests the private ZIP during Run all."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "ITRI_classical_full_Colab_upload_on_run.ipynb"
EXPECTED_SHA256 = (
    "48dc63654f63db3ef9d6d5db7ab69ad502aa079e9f6deb4b276cf9b1170f324b"
)


def cell(kind: str, source: str, ident: str, collapsed: bool = False) -> dict:
    metadata = {"jupyter": {"source_hidden": True}} if collapsed else {}
    value = {"cell_type": kind, "metadata": metadata,
             "source": source.splitlines(True), "id": ident}
    if kind == "code":
        value.update({"execution_count": None, "outputs": []})
    return value


def source_cell(filename: str, ident: str) -> dict:
    contents = (HERE / filename).read_text(encoding="utf-8")
    return cell("code", f"%%writefile /content/itri_classical/{filename}\n"
                + contents, ident, collapsed=True)


def main() -> None:
    upload_code = """
import hashlib
from google.colab import files

uploaded = files.upload()
if len(uploaded) != 1:
    raise ValueError("Upload exactly one private data ZIP.")
filename, archive_bytes = next(iter(uploaded.items()))
if not filename.lower().endswith(".zip"):
    raise ValueError("The selected file must be a ZIP archive.")
actual_sha256 = hashlib.sha256(archive_bytes).hexdigest()
if actual_sha256 != EXPECTED_SNAPSHOT_SHA256:
    raise ValueError("Archive SHA-256 differs from the audited snapshot. "
                     "Upload the original private ZIP.")
snapshot_path = work_dir / "PRIVATE_vendor_snapshot.zip"
snapshot_path.write_bytes(archive_bytes)
del archive_bytes, uploaded
print("Private snapshot verified:", filename)
""".lstrip().replace("EXPECTED_SNAPSHOT_SHA256", repr(EXPECTED_SHA256))

    run_code = """
import subprocess
import sys

result_dir = work_dir / "full_classical_results"
subprocess.run([
    sys.executable, str(work_dir / "run_classical_benchmark.py"),
    "--snapshot", str(snapshot_path), "--out", str(result_dir),
], check=True)
""".lstrip()

    download_code = """
import json
import zipfile

marker_path = result_dir / "COMPLETE.marker"
if not marker_path.exists():
    raise RuntimeError("The full experiment is incomplete.")
marker = json.loads(marker_path.read_text())
shards = sorted((result_dir / "shards").glob("*.csv"))
row_count = sum(sum(1 for _ in path.open(encoding="utf-8")) - 1
                for path in shards)
if len(shards) != marker["expected_shards"] or row_count != marker["expected_rows"]:
    raise RuntimeError("Result shard count/row count did not reconcile.")
result_zip = Path("/content/ITRI_classical_full_results.zip")
with zipfile.ZipFile(result_zip, "w", compression=zipfile.ZIP_DEFLATED) as out:
    for path in result_dir.rglob("*"):
        if path.is_file():
            out.write(path, "results/" + str(path.relative_to(result_dir)))
    for name in ("masking.py", "run_classical_benchmark.py", "PROTOCOL_v1.md"):
        out.write(work_dir / name, "code_and_protocol/" + name)
    with zipfile.ZipFile(snapshot_path) as private:
        for name in ("asset_universe_v1.json", "acquisition_qc_receipt.json"):
            out.writestr("input_metadata/" + name, private.read(name))
print(f"Complete: {len(shards)} shards, {row_count} feature rows.")
print("Downloading:", result_zip.name)
files.download(str(result_zip))
""".lstrip()

    notebook = {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {
            "colab": {"name": OUTPUT.name, "provenance": []},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
        },
        "cells": [
            cell("markdown",
                 "# ITRI external validation: classical methods\n\n"
                 "Choose Runtime → Run all. The notebook installs dependencies "
                 "and prepares readable Python source. When the upload prompt "
                 "appears, select your ITRI_external_PRIVATE_data_snapshot.zip. "
                 "The archive hash is checked before any experiment. The full "
                 "run then proceeds and automatically downloads the results ZIP.\n\n"
                 "Use a CPU runtime. Keep the input snapshot private. The "
                 "downloaded results contain metrics, code, protocol and "
                 "metadata but no raw OHLCV. Long source cells are collapsed; "
                 "expand them to inspect ordinary Python code. The neural "
                 "BRITS/SAITS stage remains separate.",
                 "overview"),
            cell("code",
                 "%pip -q install numpy==2.1.3 pandas==2.2.3 "
                 "scipy==1.18.1 scikit-learn==1.6.1",
                 "install"),
            cell("code",
                 "from pathlib import Path\n"
                 "work_dir = Path('/content/itri_classical')\n"
                 "work_dir.mkdir(parents=True, exist_ok=True)\n"
                 "print('Working directory ready:', work_dir)",
                 "prepare"),
            source_cell("masking.py", "masking-source"),
            source_cell("run_classical_benchmark.py", "benchmark-source"),
            source_cell("PROTOCOL_v1.md", "protocol-source"),
            cell("markdown",
                 "## Upload the private data archive\n\n"
                 "When the next cell runs, Colab shows Choose Files. Select "
                 "the original private ZIP you sent me. Upload one ZIP only. "
                 "The experiment continues automatically after the upload.",
                 "upload-instructions"),
            cell("code", upload_code, "upload"),
            cell("code", run_code, "run"),
            cell("code", download_code, "download"),
        ],
    }
    OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print(OUTPUT, OUTPUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
