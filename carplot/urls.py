from django.conf.urls import patterns, url, include

from django.contrib import admin

from carplot.views import get_device_event_data

admin.autodiscover()

urlpatterns = patterns(
    '',
)