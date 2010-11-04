from django.conf.urls.defaults import *

urlpatterns = patterns('xep_hq_server.views',
    (r'^initiate/(?P<xform_id>\w+)/', 'initiate'),
    (r'^save/', 'save'),
)