Integrate your settings
=======================

In a standard Django project, you add your own settings in a single `settings.py` file.
With DjangoFloor, you rather use a `defaults.py` file, which is merged with defaults settings offered by DjangoFloor.
You can use it exactly as the traditionnal `settings.py` file.

The only difference stands for the `INSTALLED_APPS` setting (see below).


Project name
------------

This settings is essentially decorative. Set `FLOOR_PROJECT_NAME` to your project name. It will be shown on the default index page.


Other Django applications
-------------------------

Since DjangoFloor comes with several applications, you should rather use `FLOOR_INSTALLED_APPS` in :mod:`myproject.defaults` to add your extra applications.
The actual `INSTALLED_APPS` will be equal to :attr:`djangofloor.defaults.INSTALLED_APPS` + :attr:`myproject.defaults.FLOOR_INSTALLED_APPS` + :attr:`djangofloor.defaults.INSTALLED_APPS_SUFFIX`.

URL configuration
-----------------

DjangoFloor comes with several configured URLs (check :mod:`djangofloor.root_urls` to see them).
Add your own URL into a :class:`list`, for example in file `myproject/urls.py`:

.. code-block:: python

    my_urls = [
        (r'^test.html$', 'myproject.views.test'),
    ]

Then define the setting `FLOOR_URL_CONF` to :attr:`myproject.urls.my_urls`.
Now, you can define all your views, as explained in the `doc <https://docs.djangoproject.com/en/1.8/topics/http/urls/#example>`_.


Index view
----------

The website index can be defined with the `FLOOR_INDEX` setting.

