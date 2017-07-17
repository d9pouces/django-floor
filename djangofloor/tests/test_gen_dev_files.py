from django.test import TestCase

from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.scripts import set_env

__author__ = 'Matthieu Gallet'
set_env('djangofloor-django')


class CommandTestCase(TestCase):
    def test_get_filenames(self):
        result = TemplatedBaseCommand.browser_folder('djangofloor', 'djangofloor/test', context={'var': 'my_project'})
        expected = {'subtest/index.html': 'djangofloor/test/subtest/index.html_tpl',
                    'subtest/my_project.txt': 'djangofloor/test/subtest/{var}.txt',
                    'text.txt': 'djangofloor/test/text.txt'}
        self.assertEqual(expected, result)
