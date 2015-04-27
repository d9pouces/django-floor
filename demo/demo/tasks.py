# coding=utf-8
from __future__ import unicode_literals
__author__ = 'flanker'
import celery
# used to avoid strange import bug with Python 3.3
celery.__file__
from celery import shared_task


@shared_task(serializer='json')
def add(x, y):
    result = (x, y)
    print(result)
    return x + y

if __name__ == '__main__':
    import doctest

    doctest.testmod()