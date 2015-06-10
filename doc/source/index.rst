.. DjangoFloor documentation master file, created by
   sphinx-quickstart on Wed Feb 13 11:51:12 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to DjangoFloor's documentation!
=======================================

Overview
--------


DjangoFloor helps you to easily create new website with the excellent framework `Django <https://www.djangoproject.com>`_.
However, we think that Django suffer from different drawbacks:

    * websites are complex to deploy,
    * JavaScript is somewhat hard to use for integrating dynamic parts in a webpage,
    * several other libraries are almost required,
    * you need a lot of code which will be common to all your projects.

We try to solve these problems:

    * a system of settings using project settings and local configuration file,
    * an easy-to-use signal system allowing to call Python or Javascript from Python or Javascript,
    * some common libraries are set as dependencies,
    * all common code are in a unique library that will be included into your projects.

Default configuration assume that you use `Redis <http://redis.io>`_ as secondary database, alongside a more classical SQL like PostgreSQL or MySQL.
It allows you to use `Celery <http://celery.readthedocs.org>`_ for background tasks out-of-box.


:doc:`installation`
    Instruction on how to install this package

:doc:`tutorial`
    Start here for a quick overview

:doc:`architecture`
    Explain the global architecture of a production deployment

:doc:`batteries`
    What are all these included dependencies?

:doc:`views`
    How to integrate your own views into a DjangoFloor project

:doc:`signals`
    DjangoFloor Signals, call Python and JS code from Python or JS with the same syntax

:doc:`settings`
    DjangoFloor settings system

:doc:`deployment`
    How to deploy a production website

:doc:`api/index`
    The complete API documentation, organized by modules


Full table of contents
======================

.. toctree::
   :maxdepth: 4

   installation
   tutorial
   architecture
   batteries
   views
   signals
   settings
   deployment
   api/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
