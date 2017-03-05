Remote functions
================

DjangoFloor allows to call Python functions from your JavaScript code.
A remote function must be a function taking `window_info` as first argument, prefixed by the `djangofloor.decorators.function` decorator.
For each app in `settings.INSTALLED_APPS`, DjangoFloor tries to import `app.functions` for auto-discovering WS functions.
If you want to write your WS functions into other modules, be sure that `app.functions` imports these modules.

Like the signals, the access of the Python functions can be restricted to some clients.


.. code-block:: python

    from djangofloor.decorators import function, everyone
    @function(is_allowed_to=everyone, path='myproject.myfunc', queue='slow')
    def my_function(window_info, arg=None):
       [perform a (clever) thing]
       return 42  # must be JSON-serializable

These functions are automatically exported as JavaScript functions in the `$.dfws` namespace:

.. code-block:: javascript

    $.dfws.myproject.myfunc({arg: 3123}).then(function(result) { alert(result); });

