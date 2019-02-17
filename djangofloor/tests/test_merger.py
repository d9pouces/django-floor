from collections import OrderedDict

from django.test import TestCase

from djangofloor.conf.merger import SettingMerger
from djangofloor.conf.providers import DictProvider

__author__ = "Matthieu Gallet"


class TestSettingMerger(TestCase):
    def test_priority(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": 1}), DictProvider({"X": 2})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual({"X": 2, "DF_MODULE_NAME": "test"}, merger.settings)
        self.assertEqual(
            OrderedDict({None: "test"}), merger.raw_settings["DF_MODULE_NAME"]
        )
        self.assertEqual(
            OrderedDict([("{'X': 1}", 1), ("{'X': 2}", 2)]), merger.raw_settings["X"]
        )

    def test_parse(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": 1, "Y": "x{X}"}), DictProvider({"X": 2})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual({"X": 2, "Y": "x2", "DF_MODULE_NAME": "test"}, merger.settings)

    def test_loop(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": "{Y}", "Y": "{Z}", "Z": "{X}"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        self.assertRaises(ValueError, merger.process)
