from .utils import post_multipart
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.importlib import import_module
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import HQSession
import json
from django.core.exceptions import ViewDoesNotExist

def _import_func(full_func_name):
    parts = full_func_name.split('.')
    func_name = parts.pop()
    mod_name = '.'.join(parts)
    mod = import_module(mod_name)
    func = getattr(mod, func_name)
    return func

authorize = _import_func(settings.XEP_AUTHORIZE)
get_xform = _import_func(settings.XEP_GET_XFORM)
put_xform = _import_func(settings.XEP_PUT_XFORM)
try:
    get_url_base = _import_func(settings.GET_URL_BASE)
except ViewDoesNotExist:
    url_base = settings.URL_BASE
    def get_url_base():
        return url_base

@require_POST
@authorize
def initiate(request, xform_id):
    callback = request.POST['callback']
    editor = request.POST['editor']
    
    hqsession = HQSession(xform_id=xform_id, callback=callback)
    hqsession.genkey()
    hqsession.save()
    
    response = post_multipart(editor, {
        'session_key': hqsession.key,
        'callback': "http://%s%s" % (get_url_base(), reverse('xep_hq_server.views.save')),
    }.items(), [
        ('xform', 'xform.xml', get_xform(xform_id))
    ])
    return response

@csrf_exempt
@require_POST
def save(request):
    session_key = request.POST['session_key']
    xform = request.FILES['xform'].read()
    cont = request.POST['continue']
    cont = {'true': True, 'false': False}[cont]
    response = {}
    
    hqsession = HQSession.get_by_key(session_key)
    
    try:
        put_xform(hqsession.xform_id, xform)
        response['status'] = "OK"
    except:
        response['status'] = "failed"
    
    if cont or response['status'] == "failed":
        hqsession.genkey()
        hqsession.save()
        response.update({
            'continue': True,
            'session_key': hqsession.key,
            'callback': None,
        })
    else:
        response.update({
            'continue': False,
            'session_key': None,
            'callback': hqsession.callback,
        })
        hqsession.active = False
        hqsession.save()
    return HttpResponse(json.dumps(response))
    
    