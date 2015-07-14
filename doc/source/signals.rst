Signals
=======

Communications between Python world and Javascript one is often awful, with a lot of boilerplate.
The main goal of my implementation of signals is to really limit this code and to easily integrate Celery and websockets.

In a standard web application, you have four kind of codes:

  * JavaScript (can call Django views or communicate with websockets)
  * Python code in Django views (receives a HttpRequest as argument and returns a HttpResponse, can call Celery tasks)
  * Python code in Celery tasks (receives some arguments and often return None, can only call other tasks, cannot communicate with Django, websocket or JS)
  * Python code in the websocket world (can call some Celery tasks but cannot perform any blocking call or call Django views)

In DjangoFloor, a signal is a simple name (a unicode string).
You connect some code (JS or Python) to this name and then you can call this new signal (with some arguments).

Defining a signal
-----------------

We want to create a signal named `demo.my_signal`, and we want to display all the arguments provided when this signal is called.

Python example (create a file called `signals.py` in one of the `INSTALLED_APPS`:

.. code-block:: python

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal')
    def my_signal(request, arg1, arg2, arg3):
        [ some interesting code ]
        print('blablabla', arg1, arg2, arg3)

A lot of computation, and this code must be used through Celery?:

.. code-block:: python

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal', delayed=True)
    def my_signal(request, arg1, arg2, arg3):
        [ some interesting code ]
        print('blablabla', arg1, arg2, arg3)

Do not forget to run a Celery worker!
You can allow non-connected users to trigger the signal:

.. code-block:: python

    from djangofloor.decorators import connect
    @connect(path='demo.my_signal', auth_required=False)
    def my_signal(request, arg1, arg2, arg3):
        [ some interesting code ]
        print('blablabla', arg1, arg2, arg3)

JavaScript example:

.. code-block:: javascript

    df.connect('demo.my_signal', function (options) { alert('blablabla' + options.arg1 + options.arg2 + options.arg3); });


Ok, that is enough to connect any code to a signal. 

Calling a signal
----------------

There are three cases:

  * you can use websockets with `django-websocket-redis` (currently requiring Python 2),
  * you cannot use websockets but you have a Redis server,
  * you cannot use websockets, nor you have a Redis server.

With websockets
~~~~~~~~~~~~~~~

This is the simplest case: if you want to call this code in Python:

.. code-block:: python

    from djangofloor.tasks import call, SESSION
    call('demo.my_signal', request, SESSION, arg1='argument', arg2='other value', arg3=42)

And in Javascript?:

.. code-block:: javascript

    df.call('demo.my_signal', {arg1: 'argument', arg2: 'other value', arg3: 42})


*Any Python or Javascript can call any Python or JavaScript signal, with (almost) the same syntax.*
If more than one code is connected to the same signal, then all codes will be called (both JS and Python).

This mode is activated if `settings.FLOOR_USE_WS4REDIS` is `True`. By default, `djangofloor` tries to import `ws4redis` before setting `FLOOR_USE_WS4REDIS`,
 but you can override this behaviour.

sharing signals
+++++++++++++++

When Javascript calls a signal, it is called on client-side and on server-side (if required).
When Python calls a signal, there are more possibilities to propagate it with the `sharing` argument:

    * only to Python with `sharing=None`,
    * to Python and only to the original Javascript session with `sharing=SESSION`,
    * to Python and to all connected users with `sharing=BROADCAST`,
    * to Python and to the original user with `sharing=USER` (he can receive multiple instances of this signal with multiple browser windows),
    * to Python and to a limited set of users with `sharing={USER: ['username1', 'username2', ]}`.

You can prevent Python code from calling the javascript side of calls `call('demo.my_signal', request, None, \*\*kwargs)`

Without Redis nor websockets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the hardest case. You can still you signals through standard HTTP requests:

  * Javascript can call both Javascript and Python code,
  * Python code called from JS can only return a list of dict `{'signal': 'signal.name', 'options': kwargs}` (see example below), which will be called in JS
  * you cannot use delayed Python signals (because they require Celery),

So, the only valid patterns are:

    * Javascript that calls Javascript
    * Javascript that calls Python that returns several Javascript calls


.. code-block:: python

    @connect(path='demo.test_form')
    def test_form(request, form):
        form = SerializedForm(SimpleForm)(form)
        if form.is_valid() and form.cleaned_data['first_name']:
            return [{'signal': 'df.messages.info', 'options': {'html': 'Your name is %s' % form.cleaned_data['first_name']}}]
        return [{'signal': 'df.messages.error', 'options': {'html': 'Invalid form. You must provide your first name'}}]



Without websockets but with Redis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In addition of the degraded mode without Redis, using a Redis server allows to more things:

    * use delayed (Celery) tasks,
    * call Javascript signals anywhere from Python code (including in delayed tasks) by activating a regular polling from JS.
    However, you can only activate JS signals on a given session (probably the one that sent the first `SignalRequest`).

You activate a regular polling by setting `WS4REDIS_EMULATION_INTERVAL` to a positive value. This interval is in milliseconds!
Do not set it below 1000 if you do not want to flood your webserver. Leave it to 0 to desactivate this behaviour.
With this polling, you can emulate an almost complete websocket behaviour (with celery tasks sending signals to the client).

By default, this polling is also deactivated for anonymous users, even if you set it to a positive value.

If `WS4REDIS_EMULATION_INTERVAL` looks like `my_package.my_module.my_callable` or if it is callable, then it will be called with a `django.http.HttpRequest` as argument, and it must return a non-negative integer (interval in milliseconds).



Notes
-----

    - all signals defined in files `signals.py` of each app listed in INSTALLED_APPS are automatically taken into account (if some signals are defined elsewhere, you must import their modules into a `signals.py`),
    - You can prevent specific Python code from being called by JS:

        .. code-block:: python

            @connect(path='demo.my_signal', allow_from_client=False)

    - Several functions (both JS and Python) can be connected to the same signal,
    - Python calls require a `request`, which can be either a standard `django.http.HttpRequest` or a `djangofloor.decorators.SignalRequest`. `SignalRequest` propagates the username and the session key from call to call and is provided from a JS key.
    - Required JS files (jquery, ws4redis and `js/djangofloor.js`) are defined in `settings.PIPELINE_JS`
