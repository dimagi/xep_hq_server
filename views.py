from .utils import post_multipart
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.importlib import import_module
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import HQSession
import json

def _import_func(full_func_name):
    parts = full_func_name.split('.')
    func_name = parts.pop()
    mod_name = '.'.join(parts)
    mod = import_module(mod_name)
    func = getattr(mod, func_name)
    return func

try:
    authorize = _import_func(settings.XEP_AUTHORIZE)
except:
    authorize = lambda request, xform_id: None
get_xform = _import_func(settings.XEP_GET_XFORM)
put_xform = _import_func(settings.XEP_PUT_XFORM)

@require_POST
def initiate(request, xform_id):
    authorize(request, xform_id)
    callback = request.POST['callback']
    editor = request.POST['editor']
    
    hqsession = HQSession(xform_id=xform_id, callback=callback)
    hqsession.genkey()
    hqsession.save()
    
    response = post_multipart(editor, {
        'session_key': hqsession.key,
        'callback': "%s%s" % (settings.URL_BASE, reverse('xep_hq_server.views.save')),
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
    
    