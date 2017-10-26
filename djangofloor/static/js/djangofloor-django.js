/*"""
JavaScript signals for the Django admin site
--------------------------------------------

You can build entire website based on the Django admin site. These functions allows to display notifications with these templates.
The div used by the modal is also emptied to force the update of its content when a new modal is displayed.

*/

(function(jQ) {
    var notification = function (style, level, content, title, icon, timeout) {
        var notificationId = "df_messages" + jQ.df._notificationId++;
        if (timeout === undefined) { timeout = 0; }
        if (style === undefined) { style = "notification"; }
        if (level === undefined) { level = "info"; }
        if (style === "banner") {
            var messages = jQ('#df_messages');
            if (messages[0] === undefined) {
                style = "notification";
                console.warn('Please add <ul id="df_messages"></ul> somewhere in your HTML code.');
            } else {
                content = '<li id="' + notificationId + '" class="' + level + ' fade in">' + content + '</li>'
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

    jQ.df.connect("df.notify", function (opts, id) {
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

}(jQuery));