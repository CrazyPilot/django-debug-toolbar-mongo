import os

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'example.db',
    }
}

SECRET_KEY = 'u=0tir)ob&3%uw3h4&&$%!!kffw$h*!_ia46f)qz%2rxnkhak&'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)

INSTALLED_APPS = (
    'debug_toolbar',
    'debug_toolbar_mongo',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar_mongo.panel.MongoDebugPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
)

ROOT_URLCONF = 'example.urls'

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
}

INTERNAL_IPS = ('127.0.0.1',)
