/**
 * Created by flanker on 16/04/15.
 */
df = {};

df.registered_signals = {};
df.default_message_timeout = 5000;
df.__message_count = 0;
df.window_key = null;
df.ws4redis = null;
df.csrf_cookie_value = '';
/**
 * Call an existing signal
 * @param signal
 * @param options
 * @returns boolean always false
 */
df.call = function (signal, options, from_server) {
    "use strict";
    var i;
    if (df.ws4redis === null) {
        df.ws4redis_connect(df.window_key);
    }
    if (this.registered_signals[signal] === undefined) {
        return false;
    }
    for (i = 0; i < this.registered_signals[signal].length; i += 1) {
        this.registered_signals[signal][i](options, from_server);
    }
    return false;
};

/**
 * add the CSRF token to a form as a hidden input. Always returns True so you can use it as onsubmit attribute;
 <form onsubmit="return df.add_csrf_to_form(this);" method="POST" >;
*/

df.add_csrf_to_form = function (form) {
    var input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'csrfmiddlewaretoken';
    input.value = df.csrf_cookie_value;
    form.appendChild(input);
    return true;
};

/**
 * Connect a new slot to a signal (the signal will be automatically created on the first connection).
 *
 * @param signal name of the signal to connect to
 * @param fn JS function
 */
df.connect = function (signal, fn) {
    "use strict";
    if (this.registered_signals[signal] === undefined) {
        this.registered_signals[signal] = [];
    }
    this.registered_signals[signal].push(fn);
};

df.connect_http = function (signal, url) {
    "use strict";
    var wrapper = function (options, from_server) {
        if (from_server) {
            return;
        }
        var jqxhr, completeUrl = url;
        if (df.window_key) {
            completeUrl += '?window_key=' + df.window_key;
        }
        jqxhr = $.post(completeUrl, JSON.stringify(options));
        jqxhr.done(function (calls) {
            for (var i = 0; i < calls.length; i += 1) {
                df.call(calls[i].signal, calls[i].options);
            }
        });
    };
    df.connect(signal, wrapper);
};

df.connect_ws_emulator = function (url) {
    "use strict";
    var jqxhr, completeUrl = url;
    if (df.window_key) {
        completeUrl += '?window_key=' + df.window_key;
    }
    jqxhr = $.get(completeUrl);
    jqxhr.done(function (calls) {
        for (var i = 0; i < calls.length; i += 1) {
            df.call(calls[i].signal, calls[i].options, true);
        }
    });
};

df.connect_ws = function (signal) {
    "use strict";
    var wrapper = function (options, from_server) {
        if (from_server) {
            return;
        }
        df.ws4redis.send_message(JSON.stringify({signal: signal, options: options, window_key: df.window_key}));
    };
    df.connect(signal, wrapper);
};

df.connect('df.messages.hide', function (options) {
    "use strict";
    var obj;
    if (options.id) {
        obj = $('#' + options.id);
        $(obj).slideUp(400, 'swing', function () {
            $(obj).remove();
        });
    } else {
        $('#df_messages').each(function (index, obj) {
            $(obj).slideUp(400, 'swing', function () {
                $(obj).remove();
            });
        });
    }
});

/**
 * {html: 'nice message', level: 'warning', duration: 10000}
 */
df.connect('df.messages.show', function (options) {
    "use strict";
    var durationMs, level, messages = $('#df_messages'), content, mid;
    df.__message_count += 1;
    mid = 'df_message_' + df.__message_count;
    if (options.level === undefined) {
        level = 'warning';
    } else {
        level = options.level;
    }
    content = '<div id="' + mid + '" class="alert alert-' + level + ' fade in"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>' + options.html + '</div>'
    if (options.duration === undefined) {
        durationMs = df.default_message_timeout;
    } else {
        durationMs = options.duration;
    }
    messages.prepend(content);
    messages.slideDown();
    if (durationMs > 0) {
        setTimeout(function () {
            df.call('df.messages.hide', {id: mid})
        }, durationMs);
    }
});

df.connect('df.messages.warning', function (options) {
    options.level = 'warning';
    df.call('df.messages.show', options);
});

df.connect('df.messages.info', function (options) {
    options.level = 'info';
    df.call('df.messages.show', options);
});

df.connect('df.messages.error', function (options) {
    options.level = 'danger';
    df.call('df.messages.show', options);
});

df.connect('df.messages.success', function (options) {
    options.level = 'success';
    df.call('df.messages.show', options);
});

df.connect('df.notify.show', function (options) {
    if (options.title) {
        options.title = '<strong>' + options.title + '</strong>';
    }
    if (options.type === undefined) {
        options.type = 'default';
    }
    var content = {icon: options.icon, title: options.title, message: options.message,
        url: options.url, target: options.target};
    $.notify(content, options);
});

df.connect('df.notify.warning', function (options) {
        options.type = 'warning';
        df.call('df.notify.show', options);
    }
);

df.connect('df.notify.info', function (options) {
        options.type = 'info';
        df.call('df.notify.show', options);
    }
);

df.connect('df.notify.error', function (options) {
        options.type = 'danger';
        df.call('df.notify.show', options);
    }
);

df.connect('df.notify.success', function (options) {
        options.type = 'success';
        df.call('df.notify.show', options);
    }
);

/**
 * {html: 'nice message', width: '1200px'}
 */
df.connect('df.modal.show', function (options) {
    "use strict";
    var baseModal = $('#df_modal');
    if (baseModal.size() == 0) {
        $('body').append('<div class="modal fade" id="df_modal" tabindex="-1" role="dialog" aria-labelledby="df_modal" aria-hidden="true"><div class="modal-dialog"><div class="modal-content"></div></div></div>');
    }
    // TODO : ajouter une option onclose, qui correspond à un appel JS à la fermeture
    // on l'ajoute à une liste d'onclose pour les enchaînements ouverture/fermeture
    baseModal.find(".modal-content").html(options.html);
    if (options.width) {
        baseModal.find(".modal-dialog").attr("style", "width: " + options.width);
    } else {
        baseModal.find(".modal-dialog").removeAttr("style");
    }
    baseModal.modal('show');
});

df.connect('df.modal.hide', function () {
    "use strict";
    var baseModal = $('#df_modal');
    baseModal.modal('hide');
    baseModal.removeData('bs.modal');
});

/**
 * {url: 'http://example.com/'}
 */
df.connect('df.redirect', function (options) {
    "use strict";
    window.location.href = options.url;
});

$(function () {
    $("#body").on('hidden.bs.modal', function () {
        "use strict";
        var baseModal = $('#df_modal');
        baseModal.removeData('bs.modal');
        baseModal.find(".modal-content").html('');
    });
    $('#df_messages div').each(function (index, obj) {
        setTimeout(function () {
            $(obj).slideUp(400, 'swing', function () {
                $(obj).remove();
            });
        }, df.default_message_timeout);
    });

})