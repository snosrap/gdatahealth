#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import gdata
import gdata.health
import gdata.health.service
            
# Profile

class ProfilePage(webapp.RequestHandler):

    section_titles = {'CONDITION':'Problems','MEDICATION':'Medications','ALLERGY':'Allergies','LABTEST':'Test results','PROCEDURE':'Procedures','IMMUNIZATION':'Immunizations','PAYER':'Insurance'}
    section_order = ('CONDITION','MEDICATION','ALLERGY','LABTEST','PROCEDURE','IMMUNIZATION','PAYER')

    def get(self):
        account = key_from_request(self.request, get=True)
        if not account:
            self.redirect('/accounts/ServiceLogin?continue=%s' % self.request.path_url)
            return
        profiles = Profile.all().ancestor(account).order('-created').fetch(limit=100)
        profileId = self.request.get('profile') or profiles[0].key().id_or_name()
        profile = [x for x in profiles if x.key().id_or_name() == profileId][0]
        is_editable = profile.parent_key() == account.key()
        entries = Health.all().ancestor(profile).order('-created').fetch(limit=1000)
        files = File.all().ancestor(profile).order('-created').fetch(limit=1000)
        sections = [{'category':x, 'title':self.section_titles[x], 'entries':[y for y in entries if y.category_ccr == x]} for x in self.section_order]
        request = self.request
        auth_sub_url = gdata.service.GenerateAuthSubRequestUrl(next=request.path_url+'/link?profile='+profileId, scopes=['https://www.google.com/h9/feeds'], hd='default', secure=False, session=True, request_url='https://www.google.com/h9/authsub') + '&permission=1'

        render_template('health_p.html', self, locals())
        
    def post(self):
        
        if self.request.get('action') == 'add_health':
            profile_key = key_from_request(self.request, self.request.get('profile_id_or_name'))
            Health(key_name=key_name(), parent=profile_key, account=profile_key.parent(), profile=profile_key, category_ccr=self.request.get('category_ccr'), category_item=self.request.get('category_item'), ccr=self.request.get('ccr')).put()
        
        if self.request.get('action') == 'delete_health':
            db.delete(key_from_request(self.request, self.request.get('profile_id_or_name'), healthId=self.request.get('health_id_or_name')))
        
        if self.request.get('action') == 'add_profile':
            account = key_from_request(self.request, get=True)
            Profile(key_name=key_name(), parent=account, account=account, author=account.email, name=self.request.get('name')).put()
        
        if self.request.get('action') == 'delete_profile':
            profile_key = key_from_request(self.request, self.request.get('profile_id_or_name'))
            db.delete(Health.all(keys_only=True).ancestor(profile_key).fetch(limit=1000))
            db.delete(File.all(keys_only=True).ancestor(profile_key).fetch(limit=1000))
            db.delete(profile_key)
            self.redirect('/health/p')
            return
 
        elif self.request.get('action') == 'delete_file':
            db.delete(key_from_request(self.request, self.request.get('profile_id_or_name'), fileId=self.request.get('file_id_or_name')))
        
        elif self.request.get('action') == 'add_file':
            profile_key = key_from_request(self.request, self.request.get('profile_id_or_name'))
            File(key_name=key_name(), parent=profile_key, account=profile_key.parent(), profile=profile_key, file=db.Blob(self.request.get("file")), title=self.request.POST["file"].filename, mime=self.request.POST["file"].type).put()

        elif self.request.get('action') == 'unlink_profile':
            profile_key = profile_key_from_request(self.request)
            profile = Profile.get(profile_key)
            profile.gh_token = None
            profile.put()
            
        self.redirect(self.request.url)

class LinkHandler(webapp.RequestHandler):
    def get(self):
        profile_key = profile_key_from_request(self.request)
        profile = Profile.get(profile_key)

        if self.request.get('token') or profile.gh_token:
            client = gdata.health.service.HealthService(source='snosrap-gdatahealth-v1', use_h9_sandbox=True)

            if self.request.get('token'):
                client.SetAuthSubToken(self.request.get('token'))
                client.UpgradeToSessionToken()
                profile.gh_token = client.GetAuthSubToken()
                profile.put()

            elif profile.gh_token:
                client.SetAuthSubToken(profile.gh_token)

            feed = client.GetProfileFeed()
            self.save_entries(profile, feed)
            self.redirect('/health/p?profile='+str(profile.key().id_or_name()))

    def save_entries(self, profile, feed):
        entries = Health.all().ancestor(profile).order('-created').fetch(limit=1000)
        for entry in feed.entry:
            category_dict = dict([(x.scheme, x.term) for x in entry.category])
            if not len([x for x in entries if x.gh_identifier == entry.id.text]): # don't re-add
                Health(key_name=key_name(), parent=profile, account=profile.parent(), profile=profile, gh_identifier=entry.id.text, category_ccr=category_dict[None], category_item=category_dict['http://schemas.google.com/health/item'], category_kind=category_dict['http://schemas.google.com/g/2005#kind'], ccr=entry.ccr.ToString().replace('ns0:', '').replace(':ns0', '')).put()

# Routes

def main():
    application = webapp.WSGIApplication([    
        ('/health/p', ProfilePage),
        ('/health/p/link', LinkHandler),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
