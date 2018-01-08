from djangofloor.conf.config_values import ExpandIterable

DF_INDEX_VIEW = 'easydemo.views.IndexView'
DEVELOPMENT = False
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.JSMinCompressor'
PIPELINE_CSS_COMPRESSOR = 'djangofloor.templatetags.pipeline.RcssCompressor'
PIPELINE_COMPILERS = [
    'djangofloor.templatetags.pipeline.PyScssCompiler'
    # 'pipeline.compilers.sass.SASSCompiler',
]
DF_CSS = ['scss/easydemo.scss']

PIPELINE_CSS = {
    'django': {
        'source_filenames': ['vendor/font-awesome/css/font-awesome.min.css', 'admin/css/forms.css',
                             'css/djangofloor-django.css', ExpandIterable('DF_CSS')],
        'output_filename': 'css/django-all.css', 'extra_context': {'media': 'all'},
    },
    'bootstrap4': {
        'source_filenames': ['scss/easydemo-bootstrap4.scss'],
        'output_filename': 'css/bootstrap4-all.css', 'extra_context': {'media': 'all'},
    },
    'ie9': {
        'source_filenames': [],
        'output_filename': 'css/ie9.css', 'extra_context': {'media': 'all'},
    },
}
PIPELINE_JS = {
    'django': {
        'source_filenames': [
            'vendor/jquery/dist/jquery.min.js',
            'js/djangofloor-base.js',
            'vendor/bootstrap-notify/bootstrap-notify.js',
            'js/djangofloor-django.js',
            ExpandIterable('DF_JS')
        ],
        'output_filename': 'js/django.js',
    },
    'bootstrap4': {
        'source_filenames': [
            'bootstrap4/js/src/*.js',
            'js/djangofloor-base.js',
            'js/djangofloor-bootstrap3.js',
            ExpandIterable('DF_JS')
        ],
        'output_filename': 'js/bootstrap4.js',
    },
    'ie9': {
        'source_filenames': ['vendor/html5shiv/dist/html5shiv.js', 'vendor/respond.js/dest/respond.src.js', ],
        'output_filename': 'js/ie9.js',
    }
}
