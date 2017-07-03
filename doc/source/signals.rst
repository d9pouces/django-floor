Working with signals
====================

DjangoFloor allows you to define signals in both server (Python) and client (JavaScript) sides.
Signals are just a name (a string) with some code related to it. When a signal is triggered (by its name), each function is called elsewhere (in another process).
You can attach JavaScript or Python code to your signal name, and you can call this can from the server side as well as from the JS side.

However, Python and JavaScript sides are not symmetrical:

  * there is a single Python side for executing signals (even if there are multiple processes or threads executing it) that is called “SERVER”,
  * there are multiple JavaScript clients. Each of them has a unique identifier and some other properties (any Python object, like "property1" or User("username")). Two-way communications are based on websockets.

Architecture
------------

In the following graph, the JS side means any JS signal: it can be triggered to `WINDOW`, `BROADCAST`, `USER`, any topic or any list of topics.
For obvious security reasons, a browser can only trigger signals on itself or on the server, but never on other browser windows.

.. graphviz::

   digraph websockets {
      bgcolor="transparent";
      browser [label="Browser window(s)\n(JS side)"];
      aiohttp_http [label="HTTP server\nDjango view\n(SERVER side)"];
      aiohttp_ws [label="WS server"];
      redis_celery [label="Celery \nRedis DB"];
      redis_ws [label="Websocket \nRedis DB"];
      celery [label="Celery worker(s)\n(SERVER side)"];
      browser -> browser [label="signal to JS\nfrom the same window"];
      browser -> aiohttp_http [label="HTTP request"];
      aiohttp_http -> browser [label="HTTP response"];
      browser -> aiohttp_ws [label="signal to SERVER\nfrom JS"];
      aiohttp_ws -> redis_celery [label="signal to SERVER\nfrom JS"];
      aiohttp_http -> redis_celery [label="signal to SERVER\nfrom SERVER"];
      aiohttp_http -> redis_ws [label="signal to JS\nfrom SERVER"];
      redis_celery -> celery [label="send signals \nto SERVER to \nCelery workers"];
      celery -> redis_celery [label="new signal\n to SERVER\nfrom SERVER"];
      celery -> redis_ws [label="signal to JS\nfrom SERVER"];
      redis_ws -> aiohttp_ws [label="signal to JS\nfrom SERVER\n(pubsub)"];
      aiohttp_ws -> browser [label="signal to JS\nfrom SERVER"];
   }

As you know, almost all webpages are made of several files (the main HTML page with several annex files like style sheets or javascript files).
Each file corresponds to one HTTP request (and a Django view), each request having its own `window_key`.
The websocket connection is made with the `window_key` provided by the main HTML request: other `window_key` are useless.
Only this view can call JS signals (since other views do not know the right `window_key`), even if all views can call server-side signals.


Defining Python signals
-----------------------

The Python code corresponding to a signal must be a function taking `window_info` as first argument, prefixed by the `djangofloor.decorators.signal` decorator.
Of course, you can attach multiple functions to the same signal. All codes will be run.

.. code-block:: python

    from djangofloor.decorators import signal, everyone
    @signal(is_allowed_to=everyone, path='demo.signal', queue='slow')
    def slow_signal(window_info, content=''):
       [perform a (clever) thing]

In this example:
  * `path` is the name of the signal,
  * `queue` is the (optional) name Celery queue. It allows to dispatch signal calls to specialized queues: one for interactive functions (allowing short response times) and one for slow functions (real background tasks).
    `queue` can be a `callable` for dynamically choose the Celery queue.
    Given `queue(signal, window_info, kwargs)`, it should return a string (corresponding to the Celery queue).
  * `is_allowed_to` must be a `callable` that determine whether if a signal call is allowed to a JS client. Given `is_allowed_to(signal, window_info, kwargs)`, it must return `True` or `False`. When the list of signals allowed to a client is built, kwargs is `None`.


The last two arguments may be different for each Python code connected to the same signal. If all Python functions does not accept the same keyword arguments, then an exception will be raised, so they should accept \*\*kwargs.
In the following example, both functions will be executed. The first one will always be executed by the 'celery' queue, the second one will use a Celery queue dedicated to the user. When called from the JavaScript, the second code will only be executed if the client is authenticated.


.. code-block:: python

    from djangofloor.decorators import signal, everyone, is_authenticated
    @signal(is_allowed_to=everyone, path='demo.signal.name', queue='celery')
    def slow_signal(window_info, kwarg1="demo", kwarg2: int=32):
       [perform a (clever) thing]

    def get_queue_identifier(connection, window_info, kwargs):
       """return the name of the Celery queue (in this case, each user has its own Celery queue)
       """
       return getattr(window_info, 'username', 'celery')

    @signal(is_allowed_to=is_authenticated, path='demo.signal.name', queue=get_queue_identifier)
    def slow_signal(window_info, kwarg1='demo', kwarg3: bool=True, **kwargs):
       [perform a (clever) thing]


You must define your signals into `yourproject/signals.py`, or in any module that is imported by `yourproject/signals.py`.


Calling signals from Python
---------------------------

Calling signals is quite easy: just provide the `window_info` if the call is destined to a JS client, the name of the called signal, the destination (run on the server or the selected JS clients). If you do not want to immediately run the signal, you can use `countdown`, `expires` and `eta` options (please read the Celery documentation for their respective meanings).

.. code-block:: python

  from djangofloor.tasks import call, SERVER, WINDOW, USER
  from django.contrib.auth.models import User

  u = User.objects.get(id=1)
  call(window_info, 'demo.signal.name', to=[SERVER, 42, 'test', u], kwargs={'kwarg1': "value", "kwarg2": 10}, countdown=None, expires=None, eta=None)



The destination can be one of the constants `SERVER` (), `WINDOW`, `USER` (all JS browser windows belonging to the connected user), `BROADCAST` (any JS client), or a list of any value.
If `SERVER` is present, then the code will be executed on the server side.
All JS clients featuring the corresponding values will execute the signal (if the corresponding JS signal is defined!).


Defining JS signals
-------------------

For using signals with JavaScript, you need to

  * add '/static/js/djangofloor-base.js' to the list of loaded scripts,
  * use the `df_init_websocket` (for the djangofloor template library) tag anywhere in your HTML template,
  * use the `set_websocket_topics(request, *topics)` in the Django view -- USER, WINDOW and BROADCAST are always added,
  * define some JS signal with `$.df.connect('signal.name', function(opts))`.


.. code-block:: python

    # in your Django view
    from djangofloor.tasks import set_websocket_topics
    def my_view(request):
        [...]
        context = {...}
        set_websocket_topics(request, topic1, topic2)
        return TemplateResponse(request, template='template_name', context=context)


.. code-block:: html

    /* in your template */
    {% load djangofloor staticfiles %}
    {% static 'vendor/jquery/dist/jquery.min.js' %}
    {% static 'js/djangofloor-base.js' %}
    <script type="application/javascript">
        /* can be in a JS file */
        window.onload = function () {
            $.df.connect('signal.name', function (opts) {
                // opts is the JS equivalent of the Pythonic `**kwargs`
            });
        };
    </script>
    {% df_init_websocket %}


The first two steps are handled by the default template. A topic can be any Python value, serialized to a `string` by `settings.WEBSOCKET_TOPIC_SERIALIZER` (by default `djangofloor.wsgi.topics.serialize_topic`). When a signal is sent to a given topic, all JS clients featuring this topics receive this signal.

Under the hood, each HTTP request has a unique ID, which is associated to the list of topics stored in Redis via `set_websocket_topics`. The HTTP response is sent to the client and the actual websocket connection can be made with this unique ID and subscribed to its topic list (via Redis pub/sub).


Using signals from JS
---------------------

Calling signals is simpler that creating a new one. Once the steps enumerated before are made, you just have to call it with `$.df.call` and to provide its name and its arguments. JS and allowed Python codes are all executed.

.. code-block:: javascript

    $.df.call('signal.name', {kwarg1: "value1", kwarg2: "value2"});


Built-in signals
----------------

DjangoFloor provides a set of Python and JavaScript signals. Most of them are JavaScript ones, allowing you to dynamically modify your HTML page from your Python code.
All these JavaScript signals have shortcuts to ease their use: you can use autocompletion and easily check their arguments.
Default Python signals are provided in :mod:`djangofloor.signals`. The shortcuts of the JavaScript signals are defined in :mod:`djangofloor.signal.html` and :mod:`djangofloor.signals.bootstrap3`.
