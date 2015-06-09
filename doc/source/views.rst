Integrate your settings
=======================

Project name
------------

Ok, this settings is essentially decorative. Set `FLOOR_PROJECT_NAME` to your project name. It will be shown on the default index page.


Other Django applications
-------------------------

To add extra Django apps, just add them to `FLOOR_INSTALLED_APPS` in `myproject.defaults`.
This list will be merged to the standard `INSTALLED_APPS`.

URL configuration
-----------------

DjangoFloor comes with several configured URLs (check `djangofloor.root_urls` to see them).
Add your own URL into a `list`, for example in the file `myproject/urls.py`::

    my_urls = [
        (r'^test.html$', 'myproject.views.test'),
    ]

Then define the setting `FLOOR_URL_CONF` to 'myproject.urls.my_urls'.
Now, you can define all your views, as explained in the doc `doc <https://docs.djangoproject.com/en/1.8/topics/http/urls/#example>`_.


Index view
----------

The website index can be defined with the `FLOOR_INDEX` setting.

