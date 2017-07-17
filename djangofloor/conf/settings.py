"""Classes and functions used for the DjangoFloor settings system
==============================================================

Define several helpers classes and internal functions for the DjangoFloor settings system, allowing to merge
settings from different sources. This file must be importable while Django is not loaded yet.
"""
from djangofloor.scripts import get_merger_from_env

merger = get_merger_from_env()
merger.process()
merger.post_process()

__settings = globals()
__settings.update(merger.settings)
