from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.decorators import login_required

from carplot.views import Home, AdminHome, get_sms_command,get_device_event_data, IframeAdmin, search, send_smsCommand

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^', include('ikwen.foundation.core.urls', namespace='ikwen')),
    url(r'^tracking/$', login_required(Home.as_view()), name='home'),
    url(r'^laakam/', include(admin.site.urls)),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^dashboard/$', AdminHome.as_view(), name='admin_home'),
    url(r'^full_search$', search, name='search'),
    url(r'^billing/', include('ikwen.foundation.billing.urls', namespace='billing')),

    url(r'^(?P<model_name>[-\w]+)/$', login_required(IframeAdmin.as_view()), name='iframe_admin'),
    url(r'^device_position$', get_device_event_data, name='device_position'),
    url(r'^get_sms_command$', get_sms_command, name='get_sms_command'),
    url(r'^send_sms_command$', send_smsCommand, name='send_sms_command'),
)
