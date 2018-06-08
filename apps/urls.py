from django.conf.urls import include, url
from django.contrib import admin
from .backs.views import text
from django.http import Http404
import xadmin

handler404 = text.NotFoundPage.as_view()

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^xadmin/', xadmin.site.urls),
    url(r'', include('apps.app.urls')),
    url(r'^manager/', include('apps.backs.urls')),
    url(r'^api/', include('apps.api.urls')),
    url(r'^xcx/', include('apps.xcx.urls')),
    url(r'^404$', text.NotFoundPage.as_view()),
]

from django.conf import settings

if settings.DEBUG is False:
    urlpatterns += [
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', { 'document_root': settings.STATIC_ROOT, })
    ]
