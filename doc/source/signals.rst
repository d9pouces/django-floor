Websockets and signals
======================

DjangoFloor allows you to define signals in both server (Python) and client (JavaScript) sides.
A signal is just a name (a string) with some code related to it. When a signal is triggered by its name, the code is called somewhere, maybe in another processes.
You can attach multiple JavaScript or Python functions to the same signal name, and you can call it from the server side as well as from the JS side.

Called signals can be processed by the Python side ("SERVER") in a Celery worker, or by one or more client browsers.

All signal-related functions require `window_info` as first argument: this object carries some information to identify the browser window.
It should be forwarded as-is when a signal calls another signal. You can also use a :class:`django.http.request.HttpRequest`, or just `None` if you do not have to identify a specific browser window.

Architecture
------------

In the following graph, the JS side means any JS signal. For obvious security reasons, a browser can only trigger signals on itself or on the server, not on other browser windows.

Here is the complete scenario:

    - your browser open http://localhost:9000/ ,
    - a Django view receives a :class:`django.http.request.HttpRequest` (with a unique ID attached to it) and returns a :class:`django.http.request.HttpResponse`,
    - your browser receives a HTML page as well as some JS and CSS files linked in the HTML page, and this HTML page contains the unique ID,
    - a websocket is open by the JS code and identifies itself with this unique ID, creating a bidirectionnal communication channel,

Python Signal calls are translated into Celery tasks, whatever they are received by the websocket connection (thus triggered by the browser), triggered by the Django view processing a :class:`django.http.request.HttpResponse`,
or triggered by a Celery worker (that is processing a previous signal). Signals that are sent to the browser from Python are written to a Redis queue read by the server that processes the websocket connection.


Defining Python signals
-----------------------

The Python code corresponding to a signal must be a function taking `window_info` as first argument, prefixed by the `djangofloor.decorators.signal` decorator.
Of course, you can attach multiple functions to the same signal. All codes will be run.

.. code-block:: python

    from djangofloor.decorators import signal, everyone
    @signal(is_allowed_to=everyone, path='demo.signal', queue='slow')
    def slow_signal(window_info, content=''):
        pass
        # [perform a (clever) thing]

In this example:
  * `path` is the name of the signal,
  * `queue` is the (optional) name Celery queue. It allows to dispatch signal calls to specialized queues: one for interactive functions (allowing short response times) and one for slow functions (real background tasks).
    `queue` can also be a sub-class of :class:`djangofloor.decorators.DynamicQueueName` to dynamically choose the right Celery queue.
  * `is_allowed_to` must be a `callable` that determine whether if a signal call is allowed to a JS client. Given `is_allowed_to(signal, window_info, kwargs)`, it must return `True` or `False`.
    It can be called in two ways:
    * when the JS client asks for a list of available signals (then kwargs is `None`),
    * when the JS tries to call a signal (then kwargs is of course a dict).

The last two arguments may be different for each Python code connected to the same signal. If all Python functions does not accept the same keyword arguments, then an exception will be raised, so they should accept \*\*kwargs.
In the following example, both functions will be executed. The first one will always be executed by the 'celery' queue, the second one will use a Celery queue dedicated to the user.
When called from the JavaScript, the second code will only be executed if the client is authenticated.


.. code-block:: python

    from djangofloor.decorators import signal, everyone, is_authenticated, DynamicQueueName
    @signal(is_allowed_to=everyone, path='demo.signal.name', queue='celery')
    def slow_signal(window_info, kwarg1="demo", kwarg2: int=32):
       [perform a (clever) thing]

    class UserQueueName(DynamicQueueName):

        def __call__(connection, window_info, kwargs):
           """return the name of the Celery queue (in this case, each user has its own Celery queue)
           """
           return getattr(window_info, 'username', 'celery')

    @signal(is_allowed_to=is_authenticated, path='demo.signal.name', queue=UserQueueName())
    def slow_signal(window_info, kwarg1='demo', kwarg3: bool=True, **kwargs):
       [perform a (clever) thing]


You must define your signals into `yourproject/signals.py`, or in any module that is imported by `yourproject/signals.py`.


Calling signals from Python
---------------------------

Calling signals is quite easy: just provide the `window_info` if the call is destined to a JS client, the name of the called signal, the destination (run on the server or the selected JS clients). If you do not want to immediately run the signal, you can use `countdown`, `expires` and `eta` options (please read the Celery documentation for their respective meanings).

.. code-block:: python

  from djangofloor.tasks import call, SERVER, WINDOW, USER
  from django.contrib.auth.models import User

  def my_view(request):
      u = User.objects.get(id=1)
      call(request, 'demo.signal.name', to=[SERVER, 42, 'test', u], kwargs={'kwarg1': "value", "kwarg2": 10}, countdown=None, expires=None, eta=None)



The destination can be one of the constants `SERVER` (), `WINDOW`, `USER` (all JS browser windows belonging to the connected user), `BROADCAST` (any JS client), or a list of any values.
If `SERVER` is present, then the code will be executed on the server side (if such a signal is defined).
All JS clients featuring the corresponding values will execute the signal, if the corresponding JS signal is defined!.


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
        set_websocket_topics(request)
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


Calling signals on a set of browsers
------------------------------------

You can call signals from Python on any set of browsers: all windows open by a given user, all open windows, only the window that initiated the connection…
If your Django app is a blog, you should have a page per blog post and an index. You can send signals to all users viewing a specific post or the index page.

.. code-block:: python

    # in your Django view
    from djangofloor.tasks import set_websocket_topics
    from djangofloor.tasks import call, SERVER, WINDOW, USER
    def index_view(request):
        set_websocket_topics(request, 'index')  # <- add the "index" property to this page
        return TemplateResponse(request, template='index.html', context={})
    def post_view(request, post_id):
        post = Post.objects.get(id=post_id)
        set_websocket_topics(request, post)  # <- add the "post" property to this page
        return TemplateResponse(request, template='post.html', context={'post': post})

    def display_message(post: Post):
        call(None, 'demo.signal.name', to=[post], kwargs={'kwarg1': "value"})  # 'demo.signal.name' must be defined in JS!
        call(None, 'demo.signal.name', to=["index"], kwargs={'kwarg1': "value"})  # 'demo.signal.name' must be defined in JS!


Built-in signals
----------------

DjangoFloor provides a set of Python and JavaScript signals. Most of them are JavaScript ones, allowing you to dynamically modify your HTML page from your Python code.
All these JavaScript signals have shortcuts to ease their use: you can use autocompletion and easily check their arguments.
Default Python signals are provided in :mod:`djangofloor.signals`.
Shortcuts for many JavaScript signals are defined in :mod:`djangofloor.signal.html` and :mod:`djangofloor.signals.bootstrap3`.
They allow you to call JavaScript code by only writing Python code.

Testing signals
---------------

The signal framework requires a working Redis and a worker process. However, if you only want to check if a signal
has been called in unitary tests, you can use :class:`djangofloor.tests.SignalQueue`.
Both server-side and client-side signals are kept into memory:

  * :attr:`djangofloor.tests.SignalQueue.ws_signals`,

    * keys are the serialized topics
    * values are lists of tuples `(signal name, arguments as dict)`

  * :attr:`djangofloor.tests.SignalQueue.python_signals`

    * keys are the name of the queue
    * values are lists of `(signal_name, window_info_dict, kwargs=None, from_client=False, serialized_client_topics=None, to_server=False, queue=None)`

      * `signal_name` is … the name of the signal
      * `window_info_dict` is a WindowInfo serialized as a dict,
      * `kwargs` is a dict representing the signal arguments,
      * `from_client` is `True` if this signal has been emitted by a web browser,
      * `serialized_client_topics` is not `None` if this signal must be re-emitted to some client topics,
      * `to_server` is `True` if this signal must be processed server-side,
      * `queue` is the name of the selected Celery queue.

.. code-block:: python

  from djangofloor.tasks import scall, SERVER
  from djangofloor.wsgi.window_info import WindowInfo
  from djangofloor.wsgi.topics import serialize_topic
  from djangofloor.decorators import signal
  # noinspection PyUnusedLocal
  @signal(path='test.signal', queue='demo-queue')
  def test_signal(window_info, value=None):
      print(value)

  wi = WindowInfo()
  with SignalQueue() as fd:
      scall(wi, 'test.signal1', to=[SERVER, 1], value="value1")
      scall(wi, 'test.signal2', to=[SERVER, 1], value="value2")

  # fd.python_signals looks like {'demo-queue': [ ['test.signal1', {…}, {'value': 'value1'}, False, None, True, None], ['test.signal2', {…}, {'value': 'value2'}, False, None, True, None]]}
  # fd.ws_signals looks like {'-int.1': [('test.signal1', {'value': 'value1'}), ('test.signal2', {'value': 'value2'})]}


If you do not want to use :class:`djangofloor.tests.SignalQueue` as a context manager, you can just call `activate` and `deactivate` methods.
