from couchdbkit.ext.django.schema import *
import random

class HQSession(Document):
    key = StringProperty()
    xform_id = StringProperty()
    callback = StringProperty()
    active = BooleanProperty(default=True)
    
    @classmethod
    def get_by_key(cls, key):
        hqsession = cls.view('xep_hq_server/sessions', key=key).all()[0]
        return hqsession
    
    def genkey(self):
        self.key = hex(random.getrandbits(160))[2:-1]