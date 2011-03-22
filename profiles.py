#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
            
# Profile

class ProfilePage(webapp.RequestHandler):

    section_titles = {'CONDITION':'Problems','MEDICATION':'Medications','ALLERGY':'Allergies','LABTEST':'Test results','PROCEDURE':'Procedures','IMMUNIZATION':'Immunizations','PAYER':'Insurance'}
    section_order = ('CONDITION','MEDICATION','ALLERGY','LABTEST','PROCEDURE','IMMUNIZATION','PAYER')

    def get(self):
        account = key_from_request(self.request, get=True)
        profiles = Profile.all().ancestor(account).order('-created').fetch(limit=100)
        profileId = self.request.get('profile') or profiles[0].key().id_or_name()
        profile = [x for x in profiles if x.key().id_or_name() == profileId][0]
        is_editable = profile.parent_key() == account.key()
        entries = Health.all().ancestor(profile).order('-created').fetch(limit=1000)
        files = File.all().ancestor(profile).order('-created').fetch(limit=1000)
        sections = [{'category':x, 'title':self.section_titles[x], 'entries':[y for y in entries if y.category_ccr == x]} for x in self.section_order]
        request = self.request
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
            
        self.redirect(self.request.url)

# Routes

def main():
    application = webapp.WSGIApplication([    
        ('/health/p', ProfilePage),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
