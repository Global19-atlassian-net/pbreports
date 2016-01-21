
"""
Tests for end-to-end tool contract support in pbreports.report.modifications
"""

import unittest
import os.path

import pbcommand.testkit

from base_test_case import LOCAL_DATA

EXPECTED_FILES = [
    'kinetic_histogram_thumb.png',
    'kinetic_detections.png',
    'kinetic_detections_thumb.png',
    'kinetic_histogram.png',
]

class TestPbreportModifications(pbcommand.testkit.PbTestApp):
    DATA = os.path.join(LOCAL_DATA, "modifications")
    DRIVER_BASE = "python -m pbreports.report.modifications "
    DRIVER_EMIT = DRIVER_BASE + " --emit-tool-contract "
    DRIVER_RESOLVE = DRIVER_BASE + " --resolved-tool-contract "
    REQUIRES_PBCORE = True
    INPUT_FILES = [os.path.join(DATA, "modifications.csv.gz")]
    TASK_OPTIONS = {
        "pbreports.task_options.dpi": 60,
        "pbreports.task_options.dumpdata": True,
    }

    def run_after(self, rtc, output_dir):
        # XXX check for images not defined in the tool contract
        file_names = set(os.listdir(output_dir))
        for file_name in EXPECTED_FILES:
            self.assertTrue(file_name in file_names, "Missing %s" % file_name)

if __name__ == "__main__":
    unittest.main()
