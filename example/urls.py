from django.urls import path, re_path, include
import views

urlpatterns = [
    path('', views.index),
]


import debug_toolbar
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

url_debug = [path('__debug__/', include(debug_toolbar.urls))]
url_debug += staticfiles_urlpatterns()
urlpatterns = url_debug + urlpatterns
