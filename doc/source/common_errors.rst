Common errors
=============

Here is a short description of the most common errors about the DjangoFloor features.

the page is downloaded instead of being displayed
-------------------------------------------------

Check if you use :class:`django.template.response.TemplateResponse`  instead of :meth:`django.shortcuts import render_to_response`.

JS and CSS files are missing
----------------------------

Did you use the `collectstatic` command?

invalid setting configuration
-----------------------------

If something is wrong in your configuration, you can display the loaded configuration, the used config files and the missing ones.
This command also shows which settings are defined in each config file.

.. code-block:: bash

    myproject-ctl check -v 3
    myproject-ctl config python -v 2


signals are not working
-----------------------

  * first, check the monitoring view: if it works, then your configuration is valid,
  * check if some Celery workers are working for the right Celery queue (only the `"celery"` is used by default, and queues can be dynamic!),
  * :meth:`djangofloor.tasks.set_websocket_topics` is not used in the Django view,
  * if you just added a signal, you must reload the web page (since the JS looks for exported Python signals in a .js file),
  * the signal is not allowed to JavaScript calls (that is the default).

forms and signals
-----------------

Assume that one of your signals expect a HTML form as argument. Your Python code should look like:

.. code-block:: python

    @signal(path='my.signal', is_allowed_to=is_authenticated)
    def my_signal(window_info, extra_info=None, form: SerializedForm(MySpecialForm)=None):
        form is None
        form.is_bound
        form.is_valid()

There are multiple ways to call to call this signal:

.. code-block:: html

    <button onclick="return $.df.call('my.signal', {extra_info: 42});">
    <button onclick="return $.df.call('my.signal', {form: null, extra_info: 42});">
    <button onclick="return $.df.call('my.signal', {form: [], extra_info: 42});">
    <form onsubmit="return $.df.call('my.signal', {form: $(this).serializeArray(), extra_info: 42});">

In the first case, the Python `form` variable is `None`. In the second one, the Python `form` variable is an unbound `MySpecialForm`. In the two last cases, the `form` variable is a bound `MySpecialForm`.
