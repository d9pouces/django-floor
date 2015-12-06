# -*- coding: utf-8 -*-
from django.test.testcases import TestCase
from djangofloor.decorators import RE, Choice, RedisCallWrapper
from djangofloor.exceptions import InvalidRequest

__author__ = 'Matthieu Gallet'


class TestRE(TestCase):
    def test_re_valid(self):
        regexp = RE('^\d$')
        self.assertEqual('1', regexp('1'))

    def test_re_invalid(self):
        regexp = RE('^\d$')
        self.assertRaises(ValueError, lambda: regexp('13'))

    def test_re_caster(self):
        regexp = RE('^\d$', caster=int)
        self.assertEqual(1, regexp('1'))


class TestChoice(TestCase):
    def test_choice_valid(self):
        choices = Choice(['1', '2'])
        self.assertEqual('1', choices('1'))

    def test_choice_invalid(self):
        choices = Choice(['1', '2'])
        self.assertRaises(ValueError, lambda: choices('13'))

    def test_choice_caster(self):
        choices = Choice([1, 2, '3'], caster=int)
        self.assertRaises(ValueError, lambda: choices('3'))
        self.assertEqual(1, choices('1'))


class TestSignature(TestCase):
    def test_1(self):

        def func(request, a, b, c=0):
            return request, a, b, c

        wrapper = RedisCallWrapper(func, path='test')
        self.assertFalse(wrapper.accept_kwargs)
        self.assertEqual({'a', 'b'}, wrapper.required_arguments)
        self.assertEqual({'c'}, wrapper.optional_arguments)

        self.assertRaises(InvalidRequest, lambda: wrapper.prepare_kwargs({'a': None, 'b': None, 'c': None, 'd': None}))
        self.assertRaises(InvalidRequest, lambda: wrapper.prepare_kwargs({'a': None}))
        self.assertEqual({'a': None, 'b': None, 'c': None, },
                         wrapper.prepare_kwargs({'a': None, 'b': None, 'c': None, }))
