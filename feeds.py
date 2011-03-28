#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from time import gmtime, strftime
import re
import urllib

import gdata
import gdata.health
import gdata.health.service
import email.parser
import email

from xml.etree import cElementTree as ElementTree
            
# Profile

class ProfileFeed(webapp.RequestHandler):

    def get(self, profileId, categoryParam=None):

        profile_key = key_from_request(self.request, profileId)
        entries = Health.all().ancestor(profile_key)
        
        if self.request.get('updated-min'):
            entries = entries.filter('updated >=', parse_date(self.request.get('updated-min'))).order('-updated')
        if self.request.get('updated-max'):
            entries = entries.filter('updated <', parse_date(self.request.get('updated-max'))).order('-updated')
        if self.request.get('published-min'):
            entries = entries.filter('created >=', parse_date(self.request.get('published-min'))).order('-created')
        if self.request.get('published-max'):
            entries = entries.filter('created <', parse_date(self.request.get('published-max'))).order('-created')
        if self.request.get('q'):
            entries = entries.filter('category_item >=', self.request.get('q')).filter('category_item <', self.request.get('q') + u'\ufffd')
        if self.request.get('category') or categoryParam:
            categoryParam = self.request.get('category') or urllib.unquote(categoryParam)
            for category in categoryParam.split(','): # AND
                categories = [parse_category(cat) for cat in category.split('|')] # OR
                filter, value = make_filter(categories)
                entries = entries.filter(filter, value)
                
        if self.request.get('max-results'):
            totalResults = entries.count()
        
        entries = entries.fetch(limit=int(self.request.get('max-results', '100')), offset=int(self.request.get('start-index', '1')) - 1)
        render_template('profile_ui.xml', self, locals())
    
    def post(self, profileId):
        healths = handle_health(self.request, profileId)
        if len(healths) == 1:
            entry = healths[0]
            entry.put()
            request = self.request
            render_template('profile_ui_entry.xml', self, locals())
            
    def put(self, profileId):
        self.post(profileId)

class ProfileEntry(webapp.RequestHandler):

    def get(self, profileId, entryId):
        entry = Health.get(key_from_request(self.request, profileId, entryId))
        render_template('profile_ui_entry.xml', self, locals())
        
    def post(self, profileId, entryId):
        entry = handle_health(self.request, profileId)[0]
        entry.__key__ = key_from_request(self.request, profileId, entryId)
        entry.put()
        render_template('profile_ui_entry.xml', self, locals())
        
    def put(self, profileId, entryId):
        self.post(profileId, entryId)
        
    def delete(self, profileId, entryId):
        db.delete(key_from_request(self.request, profileId, entryId))

# Register

class RegisterFeed(ProfileFeed):

    def post(self, profileId):
        entries = handle_health(self.request, profileId)
        for entry in entries:
            entry.put()
        render_template('profile_ui.xml', self, locals())

class RegisterEntry(ProfileEntry):
    pass

# Profile List

class ProfileListFeed(webapp.RequestHandler):

    def get(self):
        account_key = key_from_request(self.request)
        profiles = Profile.all().ancestor(account_key).order('-created').fetch(limit=100)
        if self.request.get('auth'):
            auth = self.request.get('auth')
        render_template('profile_list.xml', self, locals())
    
    def post(self): # NEW
        self.put()
    
    def put(self): # NEW
        if self.request.headers.get('Content-Type').startswith("application/atom+xml"):
            entry = gdata.GDataEntryFromString(self.request.body)
            if entry:
                account = get_auth_account(self.request)
                profile = Profile(key_name=key_name(), parent=account, account=account, name=entry.title.text, author=account.email)
                profile.put()
                render_template('profile_list_entry.xml', self, locals())

class ProfileListEntry(webapp.RequestHandler):

    def get(self, profileId):
        profile = Profile.get(key_from_request(self.request, profileId))
        if self.request.get('auth'):
            auth = self.request.get('auth')
        render_template('profile_list_entry.xml', self, locals())
    
    def post(self, profileId):
        self.put(profileId)
    
    def put(self, profileId):
        if self.request.headers.get('Content-Type').startswith("application/atom+xml"):
            entry = gdata.GDataEntryFromString(self.request.body)
            if entry:
                profile = Profile.get(key_from_request(self.request, profileId))
                profile.name = entry.title.text
                profile.put()
                render_template('profile_list_entry.xml', self, locals())
    
    def delete(self, profileId):
        db.delete(key_from_request(self.request, profileId))

# Helpers

def handle_health(request, profileId):

    profile_key = key_from_request(request, profileId)
    account_key = profile_key.parent()

    healths = []
    
    if request.headers['Content-Type'].startswith("application/atom+xml"):
        entry = gdata.health.ProfileEntryFromString(request.body)            
        tree = entry.ccr._ToElementTree()
    
        category_paths = {'CONDITION':'./Body/Problems','MEDICATION':'./Body/Medications','ALLERGY':'./Body/Alerts','LABTEST':'./Body/Results','PROCEDURE':'./Body/Procedures','IMMUNIZATION':'./Body/Immunizations'}
        category_item_paths = {'CONDITION':'./Description/Text','MEDICATION':'./Product/ProductName/Text','ALLERGY':'./Description/Text','LABTEST':'./Test/Description/Text','PROCEDURE':'./Description/Text','IMMUNIZATION':'./Product/ProductName/Text'}
        
        for category_ccr in category_paths:
            for element in tree.find(category_paths[category_ccr].replace('/', '/{urn:astm-org:CCR}')) or []:
                category_item = element.find(category_item_paths[category_ccr].replace('/', '/{urn:astm-org:CCR}')).text
                parent = category_paths[category_ccr].split('/').pop()
                child = ElementTree.tostring(element).replace('ns0:', '').replace(':ns0', '')
                ccr = "<ContinuityOfCareRecord xmlns='urn:astm-org:CCR'><Body><%s>%s</%s></Body></ContinuityOfCareRecord>" % (parent, child, parent)
                healths.append(Health(key_name=key_name(), parent=profile_key, account=account_key, profile=profile_key, category_ccr=category_ccr, category_item=category_item, ccr=ccr))

    elif request.headers['Content-Type'].startswith("application/x-www-form-urlencoded"):
        category_ccr = request.get('category_ccr') or request.get('category')
        category_item = request.get('category_item') or request.get('description')
        if category_ccr == 'LABTEST':
            description = category_item
            value = request.get('value')
            unit = request.get('unit')
            ccr = return_template('ccr/LABTEST.xml', request, locals())
            healths.append(Health(key_name=key_name(), parent=profile_key, account=account_key, profile=profile_key, category_ccr=category_ccr, category_item=category_item, ccr=ccr))

    return healths

# Routes

def main():
    application = webapp.WSGIApplication([
    
        ('/health/feeds/register/ui/([\w.]+)', RegisterFeed),
        ('/health/feeds/register/ui/([\w.]+)/-/(.+)', RegisterFeed),
        ('/health/feeds/register/ui/([\w.]+)/([\w.]+)', RegisterEntry),
        
        ('/health/feeds/profile/ui/([\w.]+)', ProfileFeed),
        ('/health/feeds/profile/ui/([\w.]+)/-/(.+)', ProfileFeed),
        ('/health/feeds/profile/ui/([\w.]+)/([\w.]+)', ProfileEntry),
        
        ('/health/feeds/profile/list', ProfileListFeed),
        ('/health/feeds/profile/list/([\w.]+)', ProfileListEntry),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
