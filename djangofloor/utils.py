# coding=utf-8
from pathlib import PosixPath

__author__ = 'flanker'


class DirectoryPath(PosixPath):
    def __repr__(self):
        return repr(str(self))


class FilePath(PosixPath):
    def __repr__(self):
        return repr(str(self))
