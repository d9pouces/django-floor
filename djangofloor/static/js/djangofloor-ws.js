/*"""
Base API for signals and functions
----------------------------------

Here is the complete JavaScript API provided by DjangoFloor.
*/
function loadDjangofloor() {
    let df = {};
    let event = new Event('DjangoFloorLoaded');
    window.df = df;
    window.dfws = {};
    df._wsToken = null;  /* contains the signed window key */
    df._heartbeatMessage = null;  /* will be overridden in signals.html */
    df._wsConnection = null;
    df._notificationId = 1;
    df._wsFunctionCallId = 1;
    df._notificationClosers = {};
    df._signalIds = {};
    df._functionCallPromises = {};
    df._registered_signals = {};
    df._wsBuffer = [];
    df._wsConnect = function (dfWsUrl) {
        /* open the websocket connection */
        "use strict";
        const url = dfWsUrl;
        const connection = new WebSocket(dfWsUrl);
        connection.onopen = function () {
            df._wsConnection = connection;
            for (let i = 0; i < df._wsBuffer.length; i++) {
                connection.send(df._wsBuffer[i]);
            }
            df._wsBuffer = [];
        };
        connection.onmessage = function (e) {
            if (e.data === df._heartbeatMessage) {
                df._wsConnection.send(e.data);
            } else {
                const msg = JSON.parse(e.data);
                // noinspection JSUnresolvedVariable
                if (msg.signal && msg.signal_id) {
                    if (df.debug) {
                        console.debug('received call ' + msg.signal + ' from server.');
                    }
                    df.call(msg.signal, msg.opts, msg.signal_id);
                } else if ((msg.result_id) && (msg.exception)) {
                    df._functionCallPromises[msg.result_id][1](msg.exception);
                    delete df._functionCallPromises[msg.result_id];
                } else if (msg.result_id) {
                    df._functionCallPromises[msg.result_id][0](msg.result);
                    delete df._functionCallPromises[msg.result_id];
                }
            }
        };
        connection.onerror = function (e) {
            console.error("WS error: " + e);
        };
        connection.onclose = function () {
            df._wsConnection = null;
            setTimeout(function () {
                df._wsConnect(url);
            }, 3000);
        }
    };
    df._wsSignalConnect = function (signal) {
        /* internally used by signals.html for binding python signals to JS calls */
        "use strict";
        const wrapper = function (opts, id) {
            if (id) {
                return;
            }
            const msg = JSON.stringify({signal: signal, opts: opts});
            if (df.debug) {
                console.debug('WS call "' + signal + '"', opts);
            }
            if (df._wsConnection) {
                df._wsConnection.send(msg);
            } else {
                df._wsBuffer.push(msg);
            }
        };
        df.connect(signal, wrapper);
    };
    df._wsCallFunction = function (func, opts) {
        "use strict";
        const callId = 'f' + (df._wsFunctionCallId++);
        if (opts === undefined) {
            opts = {};
        }
        df._wsConnection.send(JSON.stringify({func: func, opts: opts, result_id: callId}));
        return new Promise(function (resolve, reject) {
            df._functionCallPromises[callId] = [resolve, reject];
        });
    };
    df.call = function (signal, opts, id) {
        "use strict";
        /*"""
        .. function:: window.df.call(signal, opts, id)

            Call a signal.
            If the signal is also defined in the Python server and available to the user, then the Python signal is also triggered.

            :param string signal: Name of the called signal.
            :param object opts: Object with signal arguments.
            :param string id: Unique id of each signal triggered by the server. Do not use it yourself.
            :returns: always `false`.
        */
        let i;
        if (df._registered_signals[signal] === undefined) {
            if (df.debug) {
                console.debug('unknown call "' + signal + '" (from both client and server).');
            }
            return false;
        } else if ((id !== undefined) && (df._signalIds[id] !== undefined)) {
            return false;
        } else if (id !== undefined) {
            df._signalIds[id] = true;
        }
        if (df.debug) {
            console.debug('call "' + signal + '"', opts);
        }
        for (i = 0; i < df._registered_signals[signal].length; i += 1) {
            df._registered_signals[signal][i](opts, id);
        }
        return false;
    };
    df.connect = function (signal, fn) {
        /*"""
        .. function:: window.df.connect(signal, fn)

            Connect a javascript code to the given signal name.

            :param string signal: Name of the signal.
            :param function fn: Function that takes a single object as argument. The properties of this object are the signal arguments.
            :returns: nothing.
        */
        "use strict";
        if (df._registered_signals[signal] === undefined) {
            df._registered_signals[signal] = [];
        }
        df._registered_signals[signal].push(fn);
    };
    df.CsrfForm = function (form) {
        /*"""
        .. function:: df.CsrfForm(form)

            Add the CSRF token to a form as a hidden input. Always returns True so you can use it as the `onsubmit` attribute.
             Useful when the form has been generated without any CSRF input, for example in a websocket signal that presents
             a new form to the user.

            :param Form form: the form object
            :returns: always `true`

            Here is an example:

        .. code-block:: html

            <form onsubmit="return window.df.CsrfForm(this);" method="POST" >
            <input type="text" name="content">
            </form>;

        */
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrfmiddlewaretoken';
        input.value = df.csrfTokenValue;
        form.appendChild(input);
        // noinspection JSConstructorReturnsPrimitive
        return true;
    };
    df.serializeArray = function (form) {
        /*!
         * Serialize all form data into an array
         * (c) 2018 Chris Ferdinandi, MIT License, https://gomakethings.com
         * @param  {Node}   form The form to serialize
         * @return {String}      The serialized form data
         */

        // Setup our serialized data
        const serialized = [];
        let i, n;

        // Loop through each field in the form
        for (i = 0; i < form.elements.length; i++) {

            let field = form.elements[i];

            // Don't serialize fields without a name, submits, buttons, file and reset inputs, and disabled fields
            if (!field.name || field.disabled || field.type === 'file' || field.type === 'reset' || field.type === 'submit' || field.type === 'button') continue;

            // If a multi-select, get all selections
            if (field.type === 'select-multiple') {
                for (n = 0; n < field.options.length; n++) {
                    if (!field.options[n].selected) continue;
                    serialized.push({
                        name: field.name,
                        value: field.options[n].value
                    });
                }
            }

            // Convert field data to a query string
            else if ((field.type !== 'checkbox' && field.type !== 'radio') || field.checked) {
                serialized.push({
                    name: field.name,
                    value: field.value
                });
            }
        }

        return serialized;

    };
    document.dispatchEvent(event);
}

document.addEventListener("DOMContentLoaded", loadDjangofloor);
