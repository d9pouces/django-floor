Javascript and HTML code
========================

Prerequisites
-------------

First, you must include the following JavaScript files:

    * `jquery.min.js`,
    * `bootstrap.min.js` (ok, it is only required if you use Bootstrap3),
    * `djangofloor.js`,
    * `ws4redis.js` (required for using websockets).

You HTML also requires some code, just before the closing body tag::


    <div class="modal fade" id="df_modal" tabindex="-1" role="dialog" aria-labelledby="df_modal" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content"></div>
        </div>
    </div>

And probably on the top of your page::

    <div id="messages"></div>


Javascript API
--------------

DjangoFloor offers an object `df` with basically two methods:

    * `df.connect('signal_name', function)`, where `function` is a function taking an object as argument.
    * `df.call('signal_name', options)`, where `options` is an object whose attributes are the arguments.


Connected signals
-----------------

df.messages.warning
*******************

Display a message to the user in a warning box (call "df.messages.show" with `level` ="warning").

    * `html`: HTML content of a message to display
    * `duration` (optional): default to 10000 ms: duration for which the message must be displayed. Set it to 0 to keep it.

    JavaScript example::

        df.call('df.messages.warning', {html: "This is a message"});

    Python example::

        from djangofloor.tasks import call
        def my_view(request):
            call('df.messages.warning', request, html="This is a message")


df.messages.info
****************

Display a message to the user in an info box (call "df.messages.show" with `level` ="info").

    * `html`: HTML content of a message to display
    * `duration` (optional): default to 10000 ms: duration for which the message must be displayed. Set it to 0 to keep it.

df.messages.error
*****************

Display a message to the user in an error box (call "df.messages.show" with `level` ="danger").

    * `html`: HTML content of a message to display
    * `duration` (optional): default to 10000 ms: duration for which the message must be displayed. Set it to 0 to keep it.

df.messages.success
*******************

Display a message to the user in a success box (call "df.messages.show" with `level` ="success").

    * `html`: HTML content of a message to display
    * `duration` (optional): default to 10000 ms: duration for which the message must be displayed. Set it to 0 to keep it.

df.messages.show
****************

Display a message to the user.

    * `html`: HTML content of a message to display
    * `level` (optional): default to "warning". Can be "default", "warning", "info", "success" or "danger"
    * `duration` (optional): default to 10000 ms: duration for which the message must be displayed. Set it to 0 to keep it.


df.modal.show
*************

Display a modal window. Successive calls replace the content of the modal by the last content.


    * `html`: HTML content
    * `width` (optional): width (example: "1200px")


df.modal.hide
*************

Hide the modal window (no argument).

df.redirect
***********

Redirect the browser URL to the URL.

    * `url`: URL


df.messages.hide
****************

Remove displayed messages.

    * `id` (optional): id of the message to remove. If not provided, all messages are removed.


