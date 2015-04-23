# coding=utf-8
from __future__ import unicode_literals
__author__ = 'flanker'
from celery import shared_task


@shared_task(serializer='json')
def add(x, y):
    result = (x, y)
    print(result)
    return x + y

if __name__ == '__main__':
    import doctest

    doctest.testmod()