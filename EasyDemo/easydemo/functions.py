# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

import random
# noinspection PyUnresolvedReferences
import easydemo.forms
from djangofloor.decorators import function, everyone


# noinspection PyUnusedLocal
@function(path='test_function', is_allowed_to=everyone)
def test_function(window_info):
    return 'This is a random string returned by the server [%d]' % random.randint(0, 100)
