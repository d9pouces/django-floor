"""Python shortcuts for JS signals
===============================

This module only defines shortcuts to existing JS signals.
These signals are intended to be called on the JS side from the Python side and allow you to easily modify the
client webpage.

"""
from djangofloor.tasks import WINDOW, scall
from djangofloor.wsgi.window_info import render_to_string

__author__ = "mgallet"


def render_to_client(
    window_info, template_name, context, selector, to=WINDOW, using=None
):
    """ render a template and send the result inside a HTML selector on every selected clients

    :param window_info: a :class:`djangofloor.wsgi.window_info.WindowInfo` object
    :param template_name: name of the Django template
    :param context: template context (a dict)
    :param selector: jQuery selector (like `"#my_div"`)
    :param to: list of signal clients
    :param using: the `using` parameter of Django templates
    """
    html_content = render_to_string(template_name, context=context, using=using)
    return scall(
        window_info, "html.content", to=to, selector=selector, content=html_content
    )


def content(window_info, selector, html_content, to=WINDOW):
    """set the HTML contents of every matched element.

    :param window_info: a :class:`djangofloor.wsgi.window_info.WindowInfo` object
    :param html_content: HTML content sent to the client
    :param selector: jQuery selector (like `"#my_div"`)
    :param to: list of signal clients
    """
    return scall(
        window_info, "html.content", to=to, selector=selector, content=html_content
    )


def add(window_info, selector, html_content, to=WINDOW):
    """Create a new JS object (with jQuery) with elements added to the set of matched elements."""
    return scall(
        window_info, "html.add", to=to, selector=selector, content=html_content
    )


def add_attribute(window_info, selector, attr_name, attr_value, to=WINDOW):
    """Adds the specified attribute(s) to each of the set of matched elements."""
    return scall(
        window_info,
        "html.add_attribute",
        to=to,
        selector=selector,
        attr_name=attr_name,
        attr_value=attr_value,
    )


def add_class(window_info, selector, class_name, to=WINDOW):
    """Adds the specified class(es) to each of the set of matched elements."""
    return scall(
        window_info, "html.add_class", to=to, selector=selector, class_name=class_name
    )


def append(window_info, selector, html_content, to=WINDOW):
    """Insert content, specified by the parameter, to the end of each element in the set of matched elements."""
    return scall(
        window_info, "html.append", to=to, selector=selector, content=html_content
    )


def before(window_info, selector, html_content, to=WINDOW):
    """Insert content, specified by the parameter, before each element in the set of matched elements."""
    return scall(
        window_info, "html.before", to=to, selector=selector, content=html_content
    )


def after(window_info, selector, html_content, to=WINDOW):
    """Insert content, specified by the parameter, before after element in the set of matched elements."""
    return scall(
        window_info, "html.after", to=to, selector=selector, content=html_content
    )


def empty(window_info, selector, to=WINDOW):
    """Remove all child nodes of the set of matched elements from the DOM."""
    return scall(window_info, "html.empty", to=to, selector=selector)


def fade_out(window_info, selector, duration=400, to=WINDOW):
    """Hide the matched elements by fading them to transparent."""
    return scall(
        window_info, "html.fade_out", to=to, selector=selector, duration=duration
    )


def fade_in(window_info, selector, duration=400, to=WINDOW):
    """Display the matched elements by fading them to opaque."""
    return scall(
        window_info, "html.fade_in", to=to, selector=selector, duration=duration
    )


def fade_to(window_info, selector, opacity, duration=400, to=WINDOW):
    """ Adjust the opacity of the matched elements.

    :param window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
    :param selector: jQuery selector
    :param duration: determining how long the animation will run (ms).
    :param opacity: A number between 0 and 1 denoting the target opacity.
    :param to: target of the signal
    """
    return scall(
        window_info,
        "html.fade_to",
        to=to,
        selector=selector,
        duration=duration,
        opacity=opacity,
    )


def fade_toggle(window_info, selector, duration=400, easing="swing", to=WINDOW):
    """ Display or hide the matched elements by animating their opacity.

    :param window_info: :class:`djangofloor.wsgi.window_info.WindowInfo`
    :param selector: jQuery selector
    :param duration: determining how long the animation will run (ms).
    :param easing: A string indicating which easing function to use for the transition.
    :param to: target of the signal
    """
    return scall(
        window_info,
        "html.fade_toggle",
        to=to,
        selector=selector,
        duration=duration,
        easing=easing,
    )


def focus(window_info, selector, to=WINDOW):
    """Set the focus to the matched element."""
    return scall(window_info, "html.focus", to=to, selector=selector)


def hide(window_info, selector, duration=400, easing="swing", to=WINDOW):
    """Hide the matched elements."""
    return scall(
        window_info,
        "html.hide",
        to=to,
        selector=selector,
        duration=duration,
        easing=easing,
    )


def prepend(window_info, selector, html_content, to=WINDOW):
    """Insert content, specified by the parameter, to the beginning of each element in the set of matched elements."""
    return scall(
        window_info, "html.prepend", to=to, selector=selector, content=html_content
    )


def remove(window_info, selector, to=WINDOW):
    """Remove the set of matched elements from the DOM."""
    return scall(window_info, "html.remove", to=to, selector=selector)


def remove_class(window_info, selector, class_name, to=WINDOW):
    """Remove a single class, multiple classes, or all classes from each element in the set of matched elements."""
    return scall(
        window_info,
        "html.remove_class",
        to=to,
        selector=selector,
        class_name=class_name,
    )


def remove_attr(window_info, selector, attr_name, to=WINDOW):
    """Remove an attribute from each element in the set of matched elements."""
    return scall(
        window_info, "html.remove_attr", to=to, selector=selector, attr_name=attr_name
    )


def replace_with(window_info, selector, html_content, to=WINDOW):
    """Replace each element in the set of matched elements with the provided new content."""
    return scall(
        window_info, "html.replace_with", to=to, selector=selector, content=html_content
    )


def show(window_info, selector, duration=400, easing="swing", to=WINDOW):
    """Display the matched elements."""
    return scall(
        window_info,
        "html.show",
        to=to,
        selector=selector,
        duration=duration,
        easing=easing,
    )


def text(window_info, selector, text_content, to=WINDOW):
    """Set the text contents of the matched elements."""
    return scall(
        window_info, "html.text", to=to, selector=selector, content=text_content
    )


def toggle(window_info, selector, duration=400, easing="swing", to=WINDOW):
    """Display or hide the matched elements."""
    return scall(
        window_info,
        "html.toggle",
        to=to,
        selector=selector,
        duration=duration,
        easing=easing,
    )


def trigger(window_info, selector, event, to=WINDOW):
    """Execute all handlers and behaviors attached to the matched elements for the given event type."""
    return scall(
        window_info, "html.replace_with", to=to, selector=selector, event=event
    )


def val(window_info, selector, value, to=WINDOW):
    """Set the value of every matched element."""
    return scall(window_info, "html.val", to=to, selector=selector, value=value)


def download_file(window_info, url, filename=None, to=WINDOW):
    """Force the client to download the given file."""
    return scall(window_info, "html.download_file", to=to, url=url, filename=filename)
