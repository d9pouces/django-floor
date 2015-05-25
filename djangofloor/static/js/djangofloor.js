/**
 * Created by flanker on 16/04/15.
 */
var df = {};

df.registered_signals = {};
df.__message_count = 0;
df.ws_emulation_interval = 1000;

/**
 * Call an existing signal
 * @param signal
 * @param options
 * @returns boolean always false
 */
df.call = function (signal, options, from_server) {
    "use strict";
    var i;
    if (this.registered_signals[signal] === undefined) {
        return false;
    }
    for (i = 0; i < this.registered_signals[signal].length; i += 1) {
        this.registered_signals[signal][i](options, from_server);
    }
    return false;
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
        if(from_server) {
            return;
        }
        var jqxhr;
        jqxhr = $.post(url, JSON.stringify(options));
        jqxhr.done(function (calls) { for (var i = 0; i < calls.length; i += 1) { df.call(calls[i].signal, calls[i].options); } });
    };
    df.connect(signal, wrapper);
};

df.connect_ws_emulator = function (url) {
    "use strict";
    var jqxhr;
    jqxhr = $.get(url);
    jqxhr.done(function (calls) {
        for (var i = 0; i < calls.length; i += 1) {
            df.call(calls[i].signal, calls[i].options, true);
        }
    });
    jqxhr.always(function () { setTimeout(function () { df.connect_ws_emulator(url); }, df.ws_emulation_interval); })
};


df.connect_ws = function (signal) {
    "use strict";
    var wrapper = function (options, from_server) {
        if(from_server) {
            return;
        }
        df.ws4redis.send_message(JSON.stringify({signal: signal, options: options}));
    };
    df.connect(signal, wrapper);
};

df.connect('df.messages.hide', function (options) {
    "use strict";
    var messages;
    if (options.id) {
        messages = $('#' + options.id);
        messages.slideUp();
        messages.remove();
    } else {
        messages = $('#messages');
        messages.slideUp();
        messages.empty();
    }
});

/**
 * {html: 'nice message', level: 'warning', duration: 10000}
 */
df.connect('df.messages.show', function (options) {
    "use strict";
    var durationMs, level, messages = $('#messages'), content, mid;
    df.__message_count += 1;
    mid = 'df_message_' + df.__message_count;
    if (options.level === undefined) {
        level = 'warning';
    } else {
        level = options.level;
    }
    content = '<div id="' + mid + '" class="alert alert-' + level + ' fade in"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>' + options.html + '</div>'
    if (options.duration === undefined) {
        durationMs = 5000;
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

/**
 * {html: 'nice message', width: '1200px'}
 */
df.connect('df.modal.show', function (options) {
    "use strict";
    var baseModal = $('#df_modal');
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


$("#body").on('hidden.bs.modal', function () {
    "use strict";
    var baseModal = $('#df_modal');
    baseModal.removeData('bs.modal');
    baseModal.find(".modal-content").html('');
});