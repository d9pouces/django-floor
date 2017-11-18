"""Callables settings
==================

Dynamically build smart settings related to django-pipeline, taking into account other settings or installed packages.
"""


def static_storage(settings_dict):
    if settings_dict['PIPELINE_ENABLED']:
        return 'djangofloor.backends.DjangofloorPipelineCachedStorage'
    return 'django.contrib.staticfiles.storage.StaticFilesStorage'


static_storage.required_settings = ['PIPELINE_ENABLED']


def pipeline_enabled(settings_dict):
    return settings_dict['USE_PIPELINE'] and not settings_dict['DEBUG']


pipeline_enabled.required_settings = ['DEBUG', 'USE_PIPELINE']


# 'pipeline.compilers.coffee.CoffeeScriptCompiler'
COFFEE_SCRIPT_BINARY = '/usr/bin/env coffee'
# 'pipeline.compilers.livescript.LiveScriptCompiler'
LIVE_SCRIPT_BINARY = '/usr/bin/env lsc'
# 'pipeline.compilers.less.LessCompiler'
LESS_BINARY = '/usr/bin/env lessc'
# 'pipeline.compilers.sass.SASSCompiler'
SASS_BINARY = '/usr/bin/env sass'
# 'pipeline.compilers.stylus.StylusCompiler'
STYLUS_BINARY = '/usr/bin/env stylus'
# 'pipeline.compilers.es6.ES6Compiler'
BABEL_BINARY = '/usr/bin/env babel'
# 'pipeline.compressors.yuglify.YuglifyCompressor'
YUGLIFY_BINARY = '/usr/bin/env yuglify'
# 'pipeline.compressors.yui.YUICompressor'
YUI_BINARY = '/usr/bin/env yuicompressor'
# 'pipeline.compressors.closure.ClosureCompressor'
CLOSURE_BINARY = '/usr/bin/env closure'
# 'pipeline.compressors.uglifyjs.UglifyJSCompressor'
UGLIFYJS_BINARY = '/usr/bin/env uglifyjs'
# 'pipeline.compressors.jsmin.JSMinCompressor' -> jsmin
# 'pipeline.compressors.slimit.SlimItCompressor' -> slimit
# 'pipeline.compressors.csstidy.CSSTidyCompressor'
CSSTIDY_BINARY = '/usr/bin/env csstidy'
# 'pipeline.compressors.cssmin.CSSMinCompressor'
CSSMIN_BINARY = '/usr/bin/env cssmin'
# 'pipeline.compressors.NoopCompressor'
