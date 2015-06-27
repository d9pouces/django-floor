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

Now, if you want to call this code in Python:

.. code-block:: python

    from djangofloor.tasks import call, SESSION
    call('demo.my_signal', request, SESSION, arg1='argument', arg2='other value', arg3=42)

And in JavaScript?:

.. code-block:: javascript

    df.call('demo.my_signal', {arg1: 'argument', arg2: 'other value', arg3: 42})


*Any Python or Javascript can call any Python or JavaScript signal, with (almost) the same syntax.*
If more than one code is connected to the same signal, then all codes will be called (both JS and Python).

Notes
-----

    - all signals defined in files `signals.py` of each app listed in INSTALLED_APPS are automatically taken into account,
    - You can prevent specific Python code from being called by JS:

        .. code-block:: python

            @connect(path='demo.my_signal', allow_from_client=False)

    - You can prevent Python code from calling the javascript side of calls `call('demo.my_signal', request, None, \*\*kwargs)`
    - You can propagate Python signals to all sessions of the logged user (use `USER` instead of `SESSION`), any logged user (use `BROADCAST`), or a limited set of users with `{USER: ['username']}`
    - Several functions (either JS or Python) can be connected to the same signal
    - Python calls require a `request`, which can be either a standard `django.http.HttpRequest` or a `djangofloor.decorators.SignalRequest`. `SignalRequest` propagates the username and the session key from call to call and is provided from a JS key.
    - Required JS files (jquery, ws4redis and djangofloor) are defined in `settings.PIPELINE_JS`


Degraded mode
-------------


Maybe you cannot use websockets (Python 3…). You can still use signals through HTTP requests.
Each Python signal return a list of dict `{'signal': 'signal.name', 'options': kwargs}`.
These dictionnaries will act as regular signals. Of course, you can only propagate JS signals at the end of a signal called by the client.

You can also activate a regular polling by setting `WS4REDIS_EMULATION_INTERVAL` to a positive value. This interval is in milliseconds!
Do not set it below 1000 if you do not want to saturate your webserver. Leave it to 0 to desactivate this behaviour.
With this polling, you can emulate a complete websocket behaviour (with celery tasks sending signals to the client).

