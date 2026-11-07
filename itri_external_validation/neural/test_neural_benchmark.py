"""Fast invariants for the neural extension; no expensive model training."""

import hashlib
import io
import json
import unittest
import zipfile

import numpy as np

from run_classical_benchmark import BLOCKS, RATES, SEEDS
from run_neural_benchmark import (
    N_STEPS, fold_windows, training_seed, verified_classical_shard,
    window_starts,
)


class NeuralWindowTests(unittest.TestCase):
    def test_full_coverage_and_partition_end(self):
        for length in (64, 65, 250, 505, 1006):
            with self.subTest(length=length):
                starts = window_starts(length)
                self.assertEqual(starts[0], 0)
                self.assertEqual(starts[-1], length - N_STEPS)
                coverage = np.zeros(length, dtype=int)
                for start in starts:
                    coverage[start:start + N_STEPS] += 1
                self.assertTrue(np.all(coverage > 0))

    def test_overlap_average_and_observed_preservation(self):
        starts = window_starts(80)
        observed = np.full((80, 5), np.nan)
        observed[20, 0] = 7.0
        predictions = np.stack([np.full((N_STEPS, 5), i + 1.0)
                                for i in range(len(starts))])
        result = fold_windows(predictions, starts, observed)
        self.assertEqual(result[20, 0], 7.0)
        self.assertEqual(result[0, 1], 1.0)
        self.assertEqual(result[-1, 1], float(len(starts)))
        self.assertTrue(np.isfinite(result).all())

    def test_short_partition_rejected(self):
        with self.assertRaises(ValueError):
            window_starts(63)

    def test_training_seed_is_method_specific_and_stable(self):
        a = training_seed("abc", "EWC", "A", 1, .1, 11, "brits")
        b = training_seed("abc", "EWC", "A", 1, .1, 11, "saits")
        self.assertEqual(a, training_seed("abc", "EWC", "A", 1, .1, 11, "brits"))
        self.assertNotEqual(a, b)

    def test_classical_rate_round_trip_preserves_point_three_key(self):
        # The frozen CSV uses %.17g, which writes 0.3 as this exact string.
        header = ("block_length,rate,seed,train_mask_seed,test_mask_seed,"
                  "method,feature\n")
        rows = [f"{block},{rate:.17g},{seed},101,202,linear,open\n"
                for block in BLOCKS for rate in RATES for seed in SEEDS]
        blob = (header + "".join(rows)).encode()
        sidecar = {"csv_sha256": hashlib.sha256(blob).hexdigest(),
                   "run_fingerprint": "test"}
        archive_blob = io.BytesIO()
        with zipfile.ZipFile(archive_blob, "w") as archive:
            archive.writestr("results/shards/EWC_A.csv", blob)
            archive.writestr("results/shards/EWC_A.meta.json",
                             json.dumps(sidecar))
        archive_blob.seek(0)
        with zipfile.ZipFile(archive_blob) as archive:
            reference = verified_classical_shard(archive, "EWC", "A", "test")
        self.assertEqual(len(reference), 54)
        self.assertEqual(reference[(1, 0.3, 11)], (101, 202))


if __name__ == "__main__":
    unittest.main()
