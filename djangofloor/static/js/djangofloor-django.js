/*"""
JavaScript signals for the Django admin site
--------------------------------------------

You can build entire website based on the Django admin site. These functions allows to display notifications with these templates.
The div used by the modal is also emptied to force the update of its content when a new modal is displayed.

*/

(function($) {
    var notification = function (style, level, content, title, icon, timeout) {
        var notificationId = "df_messages" + $.df._notificationId++;
        if (timeout === undefined) { timeout = 0; }
        if (style === undefined) { style = "notification"; }
        if (level === undefined) { level = "info"; }
        if (style === "banner") {
            var messages = $('#df_messages');
            if (messages[0] === undefined) {
                style = "notification";
                console.warn('Please add <ul id="df_messages"></ul> somewhere in your HTML code.');
            } else {
                content = '<li id="' + notificationId + '" class="' + level + ' fade in">' + content + '</li>'
                messages.prepend(content);
                messages.slideDown();
                if (timeout > 0) { setTimeout(function () { $.df._closeHTMLNotification(notificationId); }, timeout); }
            }
        }
        if (style === "notification") {
            var keepOpen = (timeout === 0);
            if (title) {
                title = '<strong>' + title + '</strong>';
            }
            $.notify({message: content, title: title, icon: icon},
                {type: level, delay: timeout});
        }
        else if (style === "modal") {
            var htmlContent = '<div class="modal-header btn-' + level + '" style="border-top-left-radius: inherit; border-top-right-radius: inherit;"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>';
            if (title) {
                htmlContent += '<h4 class="modal-title">' + title + '</h4>';
            }
            htmlContent += '</div>';
            if (content) {
                htmlContent += '<div class="modal-body"><p>' + content + '</p></div>';
            }
            $.df.call('df.modal.show', {html: htmlContent});
            if (timeout > 0) {
                setTimeout(function () { $.df.call('df.modal.hide'); }, timeout);
            }
       }
        else if (style === "system") {
            $.df._systemNotification(notificationId, level, content, title, icon, timeout);
        }
    };
    $.df.validateForm = function (form, fn) {
        $.dfws[fn]({data: $.df.serializeArray(form)}).then(function(data) {
            var index, formGroup, formInput, key, helpText;
            var errors = data.errors, helpTexts = data.help_texts;
            $(form).find('input').each(function (index, formInput) {
                key = formInput ? formInput.name : undefined;
                if (key) {
                    $(formInput).addClass((errors[key] === undefined) ? 'has-success' : 'has-error');
                    $(formInput).removeClass((errors[key] === undefined) ? 'has-error' : 'has-success');
                }
            });
            $(form).find('select').each(function (index, formInput) {
                key = formInput ? formInput.name : undefined;
                if (key) {
                    $(formInput).addClass((errors[key] === undefined) ? 'has-success' : 'has-error');
                    $(formInput).removeClass((errors[key] === undefined) ? 'has-error' : 'has-success');
                }
            });
            if(data.valid) {
                $(form).find('input[type=submit]').removeAttr("disabled");
            } else {
                $(form).find('input[type=submit]').attr("disabled", "disabled");
            }
        });
    };

    $.df.connect("df.notify", function (opts, id) {
/*"""
.. function:: df.notify(opts)

    Display a notification to the user. Multiple styles are available: modal windows, Growl-like notifications,
    page-wide banners or system notification (out of the browser).


    .. code-block:: javascript

        $.df.call('df.notify', {content: "Hello, world!", level: "danger", style: "modal"});

    :param string content: Message of the notification
    :param string title: Title (displayed in bold) of the notification
    :param int timeout: Number of milliseconds before the notification is hidden
    :param string style: Method to use for displaying the notification (`'notification'`, `'banner'`, `'modal'`, or `'system'`)
    :param string level: Color of the notification: `'info'`, `'default'`, `'success'`, `'danger'`, `'warning'`.

*/
        notification(opts.style, opts.level, opts.content, opts.title, opts.icon, opts.timeout);
    });
    $.df.connect('df.modal.show', function (options) {
/*"""
.. function:: df.modal.show(opts)

    Display a nice Bootstrap 3 modal window (!)

    .. code-block:: javascript

        $.df.call('df.modal.show', {html: "Modal content!", width: "120px",
                                    onhide: {signal: "signal.name", options: {...}}});

    :param string html: Content of the modal (put inside the "modal-content" div element
    :param string width: Width of the display modal (optional)
    :param object onhide: signal to call when this modal is hidden or closed (optional)


*/
        "use strict";
        var baseModal = $('#df_modal');

        if (baseModal[0] === undefined) {
            $('body').append('<div class="modal" id="df_modal" tabindex="-1"><div class="modal-dialog"><span class="modal-close" onclick="return $.df.call(\'df.modal.hide\');">&times;</span><div class="modal-content"></div></div></div>');
            baseModal = $('#df_modal');
            window.onclick = function(event) {
                if (event.target == baseModal[0]) {$.df.call('df.modal.hide'); }
            }
            $(document).keydown(function(event) {
                if (event.keyCode == 27) {$.df.call('df.modal.hide'); }
            });
        }
        baseModal.find(".modal-content").html(options.html);
        if (options.width) {
            baseModal.find(".modal-dialog").attr("style", "width: " + options.width);
        } else {
            baseModal.find(".modal-dialog").removeAttr("style");
        }
        $.df.__modal_onhide = options.onhide;
        baseModal.css('display', 'block');
    });
    $.df.connect('df.modal.hide', function (opts) {
        "use strict";
        var baseModal = $('#df_modal');
        if (opts === undefined) {
            opts = {};
        }
        baseModal.css('display', 'none');
        if ($.df.__modal_onhide) {
            $.df.call($.df.__modal_onhide.signal, $.df.__modal_onhide.options);
            $.df.__modal_onhide = null;
        }
    });

}(jQuery));
