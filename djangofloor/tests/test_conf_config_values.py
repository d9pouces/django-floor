from unittest import TestCase

from djangofloor.conf.config_values import (
    RawValue,
    SettingReference,
    CallableSetting,
    ExpandIterable,
)
from djangofloor.conf.merger import SettingMerger
from djangofloor.conf.providers import DictProvider

__author__ = "Matthieu Gallet"


class TestSettingMerger(TestCase):
    def test_interpolation(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": "A{Y}C", "Y": "B"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {"X": "ABC", "DF_MODULE_NAME": "test", "Y": "B"}, merger.settings
        )

    def test_no_interpolation(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": "A{{Y}}C", "Y": "B"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {"X": "A{Y}C", "DF_MODULE_NAME": "test", "Y": "B"}, merger.settings
        )


class TestRawValue(TestCase):
    def test_merge(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": RawValue("A{Y}C"), "Y": "B"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {"X": "A{Y}C", "DF_MODULE_NAME": "test", "Y": "B"}, merger.settings
        )


class TestSettingReference(TestCase):
    def test_merge(self):
        merger = SettingMerger(
            None,
            [DictProvider({"X": SettingReference("Y"), "Y": 42, "Z": "{Y}"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {"X": 42, "DF_MODULE_NAME": "test", "Y": 42, "Z": "42"}, merger.settings
        )


class TestCallableSetting(TestCase):
    @staticmethod
    def callable_config(values):
        return values["A"] + values["Z"]

    @staticmethod
    def callable_config_with_required(values):
        return values["A"] + values["Z"]

    callable_config_with_required.required_settings = ["A"]

    def test_merge(self):
        x = CallableSetting(self.callable_config, "A", "Z")
        y = CallableSetting(self.callable_config_with_required)
        merger = SettingMerger(
            None,
            [DictProvider({"A": "a", "X": x, "Y": y, "Z": "z"})],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {"A": "a", "X": "az", "DF_MODULE_NAME": "test", "Y": "az", "Z": "z"},
            merger.settings,
        )


class TestExpandIterable(TestCase):
    def test_merge(self):
        merger = SettingMerger(
            None,
            [
                DictProvider(
                    {
                        "A": [1, ExpandIterable("X"), 4, "{Y}"],
                        "X": [2, 3, "{Y}"],
                        "Y": 32,
                    }
                )
            ],
            extra_values={"DF_MODULE_NAME": "test"},
        )
        merger.process()
        self.assertEqual(
            {
                "A": [1, 2, 3, "32", 4, "32"],
                "X": [2, 3, "32"],
                "Y": 32,
                "DF_MODULE_NAME": "test",
            },
            merger.settings,
        )
