/*"""
JavaScript signals using Bootstrap3
-----------------------------------

Default DjangoFloor templates are based on BootStrap3. These functions allows to display notifications with these templates.
The div used by the modal is also emptied to force the update of its content when a new modal is displayed.

*/

(function(jQ) {
    var onHiddenModal = function () {
        "use strict";
        var baseModal = jQ('#df_modal');
        baseModal.removeData('bs.modal');
        baseModal.find(".modal-content").html('');
        if (jQ.df.__modal_onhide) {
            jQ.df.call(jQ.df.__modal_onhide.signal, jQ.df.__modal_onhide.options);
            jQ.df.__modal_onhide = null;
        }
    };
    jQ.df.__modal_onhide = null;
    var notification = function (style, level, content, title, icon, timeout) {
        var notificationId = "df_messages" + jQ.df._notificationId++;
        if (timeout === undefined) { timeout = 0; }
        if (style === undefined) { style = "notification"; }
        if (level === undefined) { level = "info"; }
        if (style === "banner") {
            var messages = jQ('#df_messages');
            if (messages[0] === undefined) {
                style = "notification";
                console.warn('Please add <div id="df_messages"></div> somewhere in your HTML code.');
            } else {
                content = '<div id="' + notificationId + '" class="alert alert-' + level + ' fade in"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>' + content + '</div>'
                messages.prepend(content);
                messages.slideDown();
                if (timeout > 0) { setTimeout(function () { jQ.df._closeHTMLNotification(notificationId); }, timeout); }
            }
        }
        if (style === "notification") {
            var keepOpen = (timeout === 0);
            if (title) {
                title = '<strong>' + title + '</strong>';
            }
            jQ.notify({message: content, title: title, icon: icon},
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
            jQ.df.call('df.modal.show', {html: htmlContent});
            if (timeout > 0) {
                setTimeout(function () { jQ.df.call('df.modal.hide'); }, timeout);
            }
       }
        else if (style === "system") {
            jQ.df._systemNotification(notificationId, level, content, title, icon, timeout);
        }
    };
    jQ("#df_modal").on('hidden.bs.modal', onHiddenModal);
    jQ.df.connect('df.modal.show', function (options) {
/*"""
.. function:: $.df.modal.show(opts)

    Display a nice Bootstrap 3 modal window (!)

    .. code-block:: javascript

        $.df.call('df.modal.show', {html: "Modal content!", width: "120px",
            onhide: {signal: "signal.name", options: {...}}});

    :param string html: Content of the modal (put inside the "modal-content" div element
    :param string width: Width of the display modal (optional)
    :param object onhide: signal to call when this modal is hidden or closed (optional)


*/
        "use strict";
        var baseModal = jQ('#df_modal');
        if (baseModal[0] === undefined) {
            jQ('body').append('<div class="modal fade" id="df_modal" tabindex="-1" role="dialog" aria-labelledby="df_modal" aria-hidden="true"><div class="modal-dialog"><div class="modal-content "></div></div></div>');
            baseModal = jQ('#df_modal');
            baseModal.on('hidden.bs.modal', onHiddenModal);
        }
        baseModal.find(".modal-content").html(options.html);
        if (options.width) {
            baseModal.find(".modal-dialog").attr("style", "width: " + options.width);
        } else {
            baseModal.find(".modal-dialog").removeAttr("style");
        }
        jQ.df.__modal_onhide = options.onhide;
        baseModal.modal('show');
    });
    jQ.df.connect("df.notify", function (opts, id) {
/*"""
.. function:: $.df.notify(opts)

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
    jQ.df.connect('df.modal.hide', function (opts) {
        "use strict";
        var baseModal = jQ('#df_modal');
        if (opts === undefined) {
            opts = {};
        }
        baseModal.modal('hide');
        baseModal.removeData('bs.modal');
    });
    jQ.df.validateForm = function (form, fn) {
        jQ.dfws[fn]({data: jQ(form).serializeArray()}).then(function(data) {
            var index, formGroup, formInput, key, helpText;
            var errors = data.errors, helpTexts = data.help_texts;
            jQ(form).find('.form-group').each(function (index, formGroup) {
                formInput = jQ(formGroup).find(':input').first()[0];
                if (formInput) {
                    key = formInput ? formInput.name : undefined;
                    if (key) {
                        var addedCls = (errors[key] === undefined) ? 'has-success' : 'has-error';
                        var removedCls = (errors[key] === undefined) ? 'has-error' : 'has-success';
                        helpText = "";
                        if (helpTexts[key] !== undefined) {
                            helpText += helpTexts[key];
                        }
                        if (errors[key] !== undefined) {
                            for(value in errors[key]) {
                                helpText += ' ' + errors[key][value].message;
                            }
                        }
                        jQ(formGroup).addClass(addedCls);
                        jQ(formGroup).removeClass(removedCls);
                        if(jQ(formGroup).find('.help-block').length === 0) {
                            jQ(formGroup).append('<span class="help-block"></span>');
                        }
                        jQ(formGroup).find('.help-block').empty().html(helpText);
                    }
                }
            });
            if(data.valid) {
                jQ(form).find('input[type=submit]').removeAttr("disabled");
            } else {
                jQ(form).find('input[type=submit]').attr("disabled", "disabled");
            }
        });
    };
}(jQuery));
