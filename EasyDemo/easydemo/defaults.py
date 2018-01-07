DF_INDEX_VIEW = 'easydemo.views.IndexView'
DEVELOPMENT = False
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_CSS_COMPRESSOR = 'djangofloor.templatetags.pipeline.RcssCompressor'
PIPELINE_COMPILERS = ['djangofloor.templatetags.pipeline.PyScssCompiler']
DF_CSS = ['scss/easydemo.scss']
