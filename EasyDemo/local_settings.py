LOCAL_PATH = 'django_data'
DF_REMOTE_USER_HEADER = 'HTTP-REMOTE-USER'
DEVELOPMENT = True
DEBUG = True
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_CSS_COMPRESSOR = 'djangofloor.templatetags.pipeline.RcssCompressor'
PIPELINE_COMPILERS = ('djangofloor.templatetags.pipeline.PyScssCompiler', )
