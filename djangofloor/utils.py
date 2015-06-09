# coding=utf-8
from __future__ import unicode_literals, absolute_import
# noinspection PyCompatibility
from pathlib import PosixPath

__author__ = 'flanker'


class DirectoryPath(PosixPath):
    def __repr__(self):
        return repr(str(self))


class FilePath(PosixPath):
    def __repr__(self):
        return repr(str(self))
