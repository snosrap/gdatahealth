#!/usr/bin/env python

from models import *
from google.appengine.api import users
from google.appengine.ext.webapp import template
import functools
import re
import uuid
import base64
from feed.date.rfc3339 import tf_from_timestamp
from time import gmtime, strftime

# Decorators

def administrator(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        elif not users.is_current_user_admin():
            self.redirect(users.create_logout_url(self.request.uri))
        else:
            return method(self, *args, **kwargs)
    return wrapper

# Helpers

def minimize(s):
    return s#re.sub(">[\s]+<", "><", s)

def render_template(template_path, handler, values, content_type=None):
    if not content_type:
        if template_path.endswith(".xml"):
            content_type = "application/atom+xml"
        if template_path.endswith(".atom"):
            content_type = "application/atom+xml"
    if content_type:
        handler.response.headers['Content-Type'] = content_type
    values['updated'] = strftime("%Y-%m-%dT%H:%M:%S", gmtime())
    values['request'] = handler.request
    handler.response.out.write(minimize(template.render('templates/' + template_path, values)))

def key_name():
    return base64.b64encode(uuid.uuid4().bytes[8:], "._")[0:11]
    
def parse_date(datestr):
    return datetime.datetime.fromtimestamp(tf_from_timestamp(datestr))

def key_from_request(request, profileId=None, healthId=None, fileId=None):
    account = get_auth_account(request)
    if profileId:
        profile_id_or_name = int(profileId) if profileId.isdigit() else profileId
        if healthId:
            health_id_or_name = int(healthId) if healthId.isdigit() else healthId
            health_key = db.Key.from_path('Account', account.key().id_or_name(), 'Profile', profile_id_or_name, 'Health', health_id_or_name)
            return health_key
        elif fileId:
            file_id_or_name = int(fileId) if fileId.isdigit() else fileId
            file_key = db.Key.from_path('Account', account.key().id_or_name(), 'Profile', profile_id_or_name, 'File', file_id_or_name)
            return file_key
        else:
            profile_key = db.Key.from_path('Account', account.key().id_or_name(), 'Profile', profile_id_or_name)
            return profile_key
    else:
        return account.key()

# Internal Helpers

def get_auth_account(request):
    token = None
    
    if request.headers.has_key('Authorization'):
        token = request.headers['Authorization'].split('auth=').pop()
    elif request.get('auth'):
        token = request.get('auth')
    elif request.cookies.has_key('SSID') and request.scheme == "https":
        token = request.cookies['SSID']
    elif request.cookies.has_key('HSID') and request.scheme == "http":
        token = request.cookies['HSID']
        
    if token:
        return AccountToken.all().filter('token =', token).filter('expires >', datetime.datetime.now()).get().account