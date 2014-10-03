# coding=utf-8
__author__ = 'flanker'
from celery import shared_task


@shared_task(serializer='json')
def add(x, y):
    print((x, y))
    return x + y

if __name__ == '__main__':
    import doctest

    doctest.testmod()