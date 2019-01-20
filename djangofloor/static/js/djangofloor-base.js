/*"""
Base API for signals and functions
----------------------------------

Here is the complete JavaScript API provided by DjangoFloor.
*/
(function ($) {
    $.df = {};
    $.dfws = {};
    $.df._wsToken = null;  /* contains the signed window key */
    $.df._wsConnection = null;
    $.df._notificationId = 1;
    $.df._wsFunctionCallId = 1;
    $.df._notificationClosers = {};
    $.df._signalIds = {};
    $.df._functionCallPromises = {};
    $.df._registered_signals = {};
    $.df._wsBuffer = [];
    $.df._closeHTMLNotification = function (id) {
        $("#" + id).fadeOut(400, "swing", function () {
            $("#" + id).remove()
        });
        delete $.df._notificationClosers[id];
    };
    $.df._systemNotification = function (notificationId, level, content, title, icon, timeout) {
        "use strict";
        var createNotification = function (level, content, title, icon, timeout) {
            if ($.df._notificationClosers[notificationId]) {
                return;
            }
            var notification = new Notification(title, {body: content, icon: icon, tag: "DF-" + notificationId});
            $.df._notificationClosers[notificationId] = function () {
                notification.close();
                delete $.df._notificationClosers[notificationId];
            };
            if (timeout && (timeout > 0)) {
                setTimeout(function () {
                    $.df._notificationClosers[notificationId]();
                }, timeout);
            }
        };
        if (!("Notification" in window)) {
            $.df.notification("notification", level, content, title, icon, timeout);
        } else if (Notification.permission === "granted") {
            createNotification(level, content, title, icon, timeout);
        } else if (Notification.permission !== 'denied') {
            Notification.requestPermission(function (permission) {
                if (!('permission' in Notification)) {
                    Notification.permission = permission;
                }
                if (permission === "granted") {
                    createNotification(level, content, title, icon, timeout);
                } else {
                    $.df.notification("notification", level, content, title, icon, timeout);
                }
            });
        }
    };
    $.df._wsConnect = function (dfWsUrl) {
        "use strict";
        var url = dfWsUrl;
        var connection = new WebSocket(dfWsUrl);
        connection.onopen = function () {
            $.df._wsConnection = connection;
            for (var i = 0; i < $.df._wsBuffer.length; i++) {
                connection.send($.df._wsBuffer[i]);
            }
            $.df._wsBuffer = [];
        };
        connection.onmessage = function (e) {
            if (e.data === $.df._heartbeatMessage) {
                $.df._wsConnection.send(e.data);
            } else {
                var msg = JSON.parse(e.data);
                if (msg.signal && msg.signal_id) {
                    if ($.df.debug) {
                        console.debug('received call ' + msg.signal + ' from server.');
                    }
                    $.df.call(msg.signal, msg.opts, msg.signal_id);
                } else if ((msg.result_id) && (msg.exception)) {
                    $.df._functionCallPromises[msg.result_id][1](msg.exception);
                    delete $.df._functionCallPromises[msg.result_id];
                } else if (msg.result_id) {
                    $.df._functionCallPromises[msg.result_id][0](msg.result);
                    delete $.df._functionCallPromises[msg.result_id];
                }
            }
        };
        connection.onerror = function (e) {
            console.error("WS error: " + e);
        };
        connection.onclose = function (e) {
            $.df._wsConnection = null;
            setTimeout(function () {
                $.df._wsConnect(url);
            }, 3000);
        }
    };
    $.df._wsSignalConnect = function (signal) {
        "use strict";
        var wrapper = function (opts, id) {
            if (id) {
                return;
            }
            var msg = JSON.stringify({signal: signal, opts: opts});
            if ($.df.debug) {
                console.debug('WS call "' + signal + '"', opts);
            }
            if ($.df._wsConnection) {
                $.df._wsConnection.send(msg);
            } else {
                $.df._wsBuffer.push(msg);
            }
        };
        $.df.connect(signal, wrapper);
    };
    $.df._wsCallFunction = function (func, opts) {
        "use strict";
        var callId = 'f' + ($.df._wsFunctionCallId++);
        if (opts === undefined) {
            opts = {};
        }
        $.df._wsConnection.send(JSON.stringify({func: func, opts: opts, result_id: callId}));
        return new Promise(function (resolve, reject) {
            $.df._functionCallPromises[callId] = [resolve, reject];
        });
    };
    $.df.call = function (signal, opts, id) {
        "use strict";
        /*"""
        .. function:: $.df.call(signal, opts, id)

            Call a signal.
            If the signal is also defined in the Python server and available to the user, then the Python signal is also triggered.

            :param string signal: Name of the called signal.
            :param object opts: Object with signal arguments.
            :param string id: Unique id of each signal triggered by the server. Do not use it yourself.
            :returns: always `false`.
        */
        var i;
        if ($.df._registered_signals[signal] === undefined) {
            if ($.df.debug) {
                console.debug('unknown call "' + signal + '" (from both client and server).');
            }
            return false;
        } else if ((id !== undefined) && ($.df._signalIds[id] !== undefined)) {
            return false;
        } else if (id !== undefined) {
            $.df._signalIds[id] = true;
        }
        if ($.df.debug) {
            console.debug('call "' + signal + '"', opts);
        }
        for (i = 0; i < $.df._registered_signals[signal].length; i += 1) {
            $.df._registered_signals[signal][i](opts, id);
        }
        return false;
    };
    $.df.connect = function (signal, fn) {
        /*"""
        .. function:: $.df.connect(signal, fn)

            Connect a javascript code to the given signal name.

            :param string signal: Name of the signal.
            :param function fn: Function that takes a single object as argument. The properties of this object are the signal arguments.
            :returns: nothing.
        */
        "use strict";
        if ($.df._registered_signals[signal] === undefined) {
            $.df._registered_signals[signal] = [];
        }
        $.df._registered_signals[signal].push(fn);
    };

    /*"""
    .. function:: $.df.serializeArray(form)

        A customized version of the $.serializeArray that add a value for file input elements (the name of the selected file).
        Can be useful for sending data to SerializedForm and check if a form is valid (without actually sending the file).

    */
    $.df.serializeArray = function (form) {
        var value = $(form).serializeArray();
        $(form).find('input[type="file"]').each(function (index, element) {
            if (element.files.length) {
                value.push({name: element.name, value: element.files[0].name});
            }
        });
        return value;
    };
    /*"""
    .. function:: $.df.uploadFile(url, fileSelector, progressSelector)

        Upload a file to the provided URL and update a progress bar HTML5 element.

        :param string url: the URL to call (often a Django view)
        :param Form form: the form object
        :param string progressSelector: a jQuery selector for the progress element to update (optional)
        :returns: always `false`

    .. code-block:: html

        <form onsubmit="return $.df.uploadFile('/app/upload', this, '#myProgressBar');" method="POST" >
        <input type="text" name="content">
        </form>
        <progress max="100" value="0" id="myProgressBar"></progress>

    */
    $.df.uploadFile = function (url, form, progressSelector) {
        $.ajax({
            url: url, type: 'POST', data: new FormData($(form)[0]), cache: false,
            contentType: false, processData: false,
            xhr: function () {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    myXhr.upload.addEventListener('progress', function (e) {
                        if (e.lengthComputable && progressSelector) {
                            $(progressSelector).attr({value: e.loaded, max: e.total});
                        }
                    }, false);
                }
                return myXhr;
            },
        });
        return false;
    };
    /**

     */
    $.df.CsrfForm = function (form) {
        /*"""
        .. function:: $.df.CsrfForm(form)

            Add the CSRF token to a form as a hidden input. Always returns True so you can use it as the `onsubmit` attribute. Useful when the form has been generated without any CSRF input.

            :param Form form: the form object
            :returns: always `true`

            Here is an example:

        .. code-block:: html

            <form onsubmit="return $.df.CsrfForm(this);" method="POST" >
            <input type="text" name="content">
            </form>;

        */
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrfmiddlewaretoken';
        input.value = $.df.csrfTokenValue;
        form.appendChild(input);
        return true;
    };

    $.df.connect('html.content', function (opts) {
        $(opts.selector).html(opts.content);
    });
    /*"""
    .. function:: html.content(opts)

        set the HTML contents of every matched element.

        .. code-block:: javascript

            $.df.call('html.content', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.add', function (opts) {
        $(opts.selector).add(opts.content);
    });
    /*"""
    .. function:: html.add(opts)

        Create a new jQuery object with elements added to the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.add', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.add_class', function (opts) {
        $(opts.selector).addClass(opts.class_name);
    });
    /*"""
    .. function:: html.add_class(opts)

        Adds the specified class(es) to each of the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.add_class', {selector: "#obj", class_name: "myclass"});

        :param string selector: jQuery selector
        :param string class_name: new class

    */
    $.df.connect('html.add_attribute', function (opts) {
        $(opts.selector).attr(opts.attr_name, opts.attr_value);
    });
    /*"""
    .. function:: html.add_attribute(opts)

        Adds or replace the specified attribute(s) to each of the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.add_attribute', {selector: "#obj", attr_name: "title", attr_value: "value"});

        :param string selector: jQuery selector
        :param string attr_name: attribute name
        :param string attr_value: attribute value

    */
    $.df.connect('html.after', function (opts) {
        $(opts.selector).after(opts.content);
    });
    /*"""
    .. function:: html.after(opts)

        Insert content, specified by the parameter, after each element in the set of matched elements..

        .. code-block:: javascript

            $.df.call('html.after', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.append', function (opts) {
        $(opts.selector).append(opts.content);
    });
    /*"""
    .. function:: html.append(opts)

        Insert content, specified by the parameter, to the end of each element in the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.append', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.before', function (opts) {
        $(opts.selector).before(opts.content);
    });
    /*"""
    .. function:: html.before(opts)

        Insert content, specified by the parameter, before each element in the set of matched elements..

        .. code-block:: javascript

            $.df.call('html.before', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.empty', function (opts) {
        $(opts.selector).empty();
    });
    /*"""
    .. function:: html.empty(opts)

        Remove all child nodes of the set of matched elements from the DOM.

        .. code-block:: javascript

            $.df.call('html.empty', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.fade_out', function (opts) {
        $(opts.selector).fadeOut(opts.duration);
    });
    /*"""
    .. function:: html.fade_out(opts)

        Hide the matched elements by fading them to transparent.

        .. code-block:: javascript

            $.df.call('html.fade_out', {selector: "#obj", duration: 400});

        :param string selector: jQuery selector
        :param int duration: number of milliseconds of the animation

    */
    $.df.connect('html.fade_in', function (opts) {
        $(opts.selector).fadeIn(opts.duration);
    });
    /*"""
    .. function:: html.fade_in(opts)

        Display the matched elements by fading them to opaque.

        .. code-block:: javascript

            $.df.call('html.fade_in', {selector: "#obj", duration: 400});

        :param string selector: jQuery selector
        :param int duration: number of milliseconds of the animation

    */
    $.df.connect('html.fade_to', function (opts) {
        $(opts.selector).fadeTo(opts.duration, opts.opacity);
    });
    /*"""
    .. function:: html.fade_to(opts)

        Adjust the opacity of the matched elements.

        .. code-block:: javascript

            $.df.call('html.fade_to', {selector: "#obj", duration: 400, opacity: 0.5});

        :param string selector: jQuery selector
        :param int duration: number of milliseconds of the animation
        :param float opacity: A number between 0 and 1 denoting the target opacity.

    */
    $.df.connect('html.fade_toggle', function (opts) {
        $(opts.selector).fadeToggle(opts.duration, opts.easing);
    });
    /*"""
    .. function:: html.fade_toggle(opts)

        Display or hide the matched elements by animating their opacity.

        .. code-block:: javascript

            $.df.call('html.fade_toggle', {selector: "#obj", duration: 400});

        :param string selector: jQuery selector
        :param int duration: number of milliseconds of the animation
        :param string easing: A string indicating which easing function to use for the transition.

    */
    $.df.connect('html.focus', function (opts) {
        $(opts.selector).focus();
    });
    /*"""
    .. function:: html.focus(opts)

        Set the focus to the matched element.

        .. code-block:: javascript

            $.df.call('html.focus', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.hide', function (opts) {
        $(opts.selector).hide({duration: opts.duration, easing: opts.easing});
    });
    /*"""
    .. function:: html.hide(opts)

        Hide the matched elements.

        .. code-block:: javascript

            $.df.call('html.hide', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.prepend', function (opts) {
        $(opts.selector).prepend(opts.content);
    });
    /*"""
    .. function:: html.prepend(opts)

        Insert content, specified by the parameter, to the beginning of each element in the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.prepend', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.remove', function (opts) {
        $(opts.selector).remove();
    });
    /*"""
    .. function:: html.remove(opts)

        Remove the set of matched elements from the DOM.

        .. code-block:: javascript

            $.df.call('html.remove', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.remove_class', function (opts) {
        $(opts.selector).removeClass(opts.class_name);
    });
    /*"""
    .. function:: html.remove_class(opts)

        Remove a single class, multiple classes, or all classes from each element in the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.remove_class', {selector: "#obj", class_name: "class"});

        :param string selector: jQuery selector
        :param string class_name: class to remove

    */
    $.df.connect('html.remove_attr', function (opts) {
        $(opts.selector).removeAttr(opts.attr_name);
    });
    /*"""
    .. function:: html.remove_attr(opts)

        Remove an attribute from each element in the set of matched elements.

        .. code-block:: javascript

            $.df.call('html.remove_attr', {selector: "#obj", attr_name: "attr"});

        :param string selector: jQuery selector
        :param string attr_name: attribute to remove

    */
    $.df.connect('html.replace_with', function (opts) {
        $(opts.selector).replaceWith(opts.content);
    });
    /*"""
    .. function:: html.replace_with(opts)

        Replace each element in the set of matched elements with the provided new content.

        .. code-block:: javascript

            $.df.call('html.replace_with', {selector: "#obj", content: "<span>hello</span>"});

        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.show', function (opts) {
        $(opts.selector).show({duration: opts.duration, easing: opts.easing});
    });
    /*"""
    .. function:: html.show(opts)

        Shows the matched elements.

        .. code-block:: javascript

            $.df.call('html.show', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.toggle', function (opts) {
        $(opts.selector).toggle({duration: opts.duration, easing: opts.easing});
    });
    /*"""
    .. function:: html.toggle(opts)

        Display or hide the matched elements.

        .. code-block:: javascript

            $.df.call('html.toggle', {selector: "#obj"});

        :param string selector: jQuery selector

    */
    $.df.connect('html.text', function (opts) {
        $(opts.selector).text(opts.content);
    });
    /*"""
    .. function:: html.text(opts)

        Set the text contents of the matched elements.

        .. code-block:: javascript

            $.df.call('html.text', {selector: "#obj", content: "<span>hello</span>"});


        :param string selector: jQuery selector
        :param string content: new HTML content

    */
    $.df.connect('html.trigger', function (opts) {
        $(opts.selector).trigger(opts.event);
    });
    /*"""
    .. function:: html.trigger(opts)

        Execute all handlers and behaviors attached to the matched elements for the given event type.

        .. code-block:: javascript

            $.df.call('html.trigger', {selector: "#obj", event: "click"});


        :param string selector: jQuery selector
        :param string event: event to trigger

    */
    $.df.connect('html.val', function (opts) {
        $(opts.selector).val(opts.value);
    });
    /*"""
    .. function:: html.val(opts)

        Set the value of every matched element.

        .. code-block:: javascript

            $.df.call('html.val', {selector: "#obj", value: "value"});


        :param string selector: jQuery selector
        :param string value: new value

    */
    $.df.connect('html.download_file', function (opts) {
        /*"""
        .. function:: html.download_file(opts)

            Force the client to download the given file.

            .. code-block:: javascript

                $.df.call('html.download_file', {url: "http://example.org/test.zip", filename: "test.zip"});


            :param string url: URL of the file
            :param string filename: name of the file

        */
        var save = document.createElement('a');
        save.href = opts.url;
        save.target = '_blank';
        save.download = opts.filename || 'unknown';
        var evt = new MouseEvent('click', {view: window, bubbles: true, cancelable: false});
        save.dispatchEvent(evt);
        (window.URL || window.webkitURL).revokeObjectURL(save.href);
    });
    $.df.connect('df.validate.update_csrf', function (opts) {
        /*"""
        .. function:: df.validate.update_csrf(opts)

            Update the CSRF token in all forms.

            .. code-block:: javascript

                $.df.call('df.validate.update_csrf', {});

            :param string value: New CSRF value

        */
        $('input[name=csrfmiddlewaretoken]').value(opts.value);
        $.df.csrfTokenValue = opts.value;
    })
}(jQuery));
