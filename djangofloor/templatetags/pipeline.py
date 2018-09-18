"""Emulate django-pipeline templatetags
====================================

Allows you to use the same `javascript` and `stylesheet` template tags if `django-pipeline` is not installed.
If you add `django-pipeline` to your `settings.INSTALLED_APPS`, these versions are ignored, using the original ones.
If you keep the default settings, `django-pipeline` is automatically detected and added, so you have nothing to do.

"""
import os
import subprocess
import warnings
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from djangofloor.utils import RemovedInDjangoFloor200Warning

if settings.USE_PIPELINE:
    # noinspection PyPackageRequirements
    import pipeline.templatetags.pipeline as pipe

    # noinspection PyPackageRequirements
    from pipeline.compressors import CompressorBase

    # noinspection PyPackageRequirements
    from pipeline.compilers import CompilerBase
else:
    pipe = None
    CompressorBase = object
    CompilerBase = object

__author__ = "Matthieu Gallet"

register = template.Library()
_deprecated_files = {
    "bootstrap3/css/bootstrap.css",
    "bootstrap3/css/bootstrap.css.map",
    "bootstrap3/css/bootstrap.min.css",
    "bootstrap3/css/bootstrap.min.css.map",
    "bootstrap3/css/bootswatch.less",
    "bootstrap3/css/variables.less",
    "bootstrap3/fonts/glyphicons-halflings-regular.eot",
    "bootstrap3/fonts/glyphicons-halflings-regular.svg",
    "bootstrap3/fonts/glyphicons-halflings-regular.ttf",
    "bootstrap3/fonts/glyphicons-halflings-regular.woff",
    "bootstrap3/fonts/glyphicons-halflings-regular.woff2",
    "bootstrap3/js/bootstrap.js",
    "bootstrap3/js/bootstrap.min.js",
    "css/bootstrap-select.css",
    "css/bootstrap-select.min.css",
    "css/djangofloor.css",
    "css/font-awesome.css",
    "css/font-awesome.min.css",
    "fonts/FontAwesome.otf",
    "fonts/fontawesome-webfont.eot",
    "fonts/fontawesome-webfont.svg",
    "fonts/fontawesome-webfont.ttf",
    "fonts/fontawesome-webfont.woff",
    "fonts/glyphicons-halflings-regular.eot",
    "fonts/glyphicons-halflings-regular.svg",
    "fonts/glyphicons-halflings-regular.ttf",
    "fonts/glyphicons-halflings-regular.woff",
    "fonts/glyphicons-halflings-regular.woff2",
    "images/favicon.ico",
    "images/favicon.png",
    "js/bootstrap-notify.js",
    "js/bootstrap-notify.min.js",
    "js/bootstrap-select.js",
    "js/bootstrap-select.min.js",
    "js/djangofloor.js",
    "js/html5shiv.js",
    "js/jquery-1.10.2.js",
    "js/jquery-1.10.2.min.map",
    "js/jquery.min.js",
    "js/respond.min.js",
}
_warned_files = set()


@register.simple_tag
def javascript(key):
    """insert all javascript files corresponding to the given key"""
    if pipe and settings.PIPELINE["PIPELINE_ENABLED"] and not settings.DEBUG:
        node = pipe.JavascriptNode(key)
        return node.render({key: key})
    filenames = settings.PIPELINE["JAVASCRIPT"][key]["source_filenames"]
    context = {}  # The type attribute is unnecessary for JavaScript resources.
    context.update(settings.PIPELINE["JAVASCRIPT"][key].get("extra_context", {}))
    extra = " ".join('%s="%s"' % x for x in context.items())

    def fmt(filename):
        if filename in _deprecated_files and filename not in _warned_files:
            warnings.warn(
                "%s is deprecated" % filename,
                RemovedInDjangoFloor200Warning,
                stacklevel=2,
            )
            _warned_files.add(filename)
        return '<script src="%s%s" %s></script>' % (
            settings.STATIC_URL,
            filename,
            extra,
        )

    node = "\n".join([fmt(x) for x in filenames])
    return mark_safe(node)


@register.simple_tag
def stylesheet(key):
    """insert all javascript files corresponding to the given key"""
    if pipe and settings.PIPELINE["PIPELINE_ENABLED"]:
        node = pipe.StylesheetNode(key)
        return node.render({key: key})
    filenames = settings.PIPELINE["STYLESHEETS"][key]["source_filenames"]
    context = {"type": "text/css", "rel": "stylesheet"}
    context.update(settings.PIPELINE["STYLESHEETS"][key].get("extra_context", {}))
    extra = " ".join('%s="%s"' % x for x in context.items())

    def fmt(filename):
        return '<link href="%s%s" %s/>' % (settings.STATIC_URL, filename, extra)

    result = "\n".join([fmt(x) for x in filenames])
    return mark_safe(result)


# noinspection PyClassHasNoInit,PyAbstractClass
class RcssCompressor(CompressorBase):
    """
    JS compressor based on the Python library slimit
    (http://pypi.python.org/pypi/slimit/ ).
    """

    # noinspection PyMethodMayBeStatic
    def compress_css(self, css):
        # noinspection PyUnresolvedReferences,PyPackageRequirements
        from rcssmin import cssmin

        return cssmin(css)


# noinspection PyClassHasNoInit
class PyScssCompiler(CompilerBase):
    """ SASS (.scss) compiler based on the Python library pyScss.
    (http://pyscss.readthedocs.io/en/latest/ ).
    However, this compiler is limited to SASS 3.2 and cannot compile modern projets like Bootstrap 4.
    Please use :class:`pipeline.compilers.sass.SASSCompiler` if you use modern SCSS files.

    """

    output_extension = "css"

    def match_file(self, filename):
        return filename.endswith(".scss") or filename.endswith(".sass")

    def compile_file(self, infile, outfile, outdated=False, force=False):
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyPackageRequirements
        from scss import Compiler

        root = Path(os.path.abspath(settings.STATIC_ROOT))
        compiler = Compiler(root=root, search_path=("./",))
        css_content = compiler.compile(infile)
        with open(outfile, "w") as fd:
            fd.write(css_content)
        if self.verbose:
            print(css_content)


# noinspection PyClassHasNoInit
class TypescriptCompiler(CompilerBase):
    """ TypeScript (.ts) compiler using "tsc".
    (https://www.typescriptlang.org ).

    """

    output_extension = "js"

    def match_file(self, filename):
        return filename.endswith(".ts")

    def compile_file(self, infile, outfile, outdated=False, force=False):
        # noinspection PyPackageRequirements
        from pipeline.exceptions import CompilerError

        command = (
            [settings.TYPESCRIPT_BINARY]
            + settings.TYPESCRIPT_ARGUMENTS
            + ["-out", outfile, infile]
        )
        try:
            p = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, __ = p.communicate(b"")
            if p.returncode != 0:
                raise CompilerError(
                    "Unable to execute TypeScript",
                    command=command,
                    error_output=stdout.decode(),
                )
        except Exception as e:
            raise CompilerError(e, command=command, error_output=str(e))
