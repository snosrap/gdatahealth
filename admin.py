#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import hashlib
import uuid

class Admin(webapp.RequestHandler):
    def get(self):
        accounts = Account.all()
        tokens = AccountToken.all()
        profiles = Profile.all()
        entries = Health.all()
        shares = ProfileShare.all()
        notes = HealthNote.all()
        files = File.all()
        render_template('admin.html', self, locals())

    def post(self):
        if self.request.get('model') == 'Account':
            if self.request.get('key'):
                account_key = db.Key(encoded=self.request.get('key'))
                db.delete(AccountToken.all(keys_only=True).ancestor(account_key).fetch(limit=1000))
                db.delete(Profile.all(keys_only=True).ancestor(account_key).fetch(limit=1000))
                db.delete(Health.all(keys_only=True).ancestor(account_key).fetch(limit=1000))
                db.delete(File.all(keys_only=True).ancestor(account_key).fetch(limit=1000))
                db.delete(account_key)
            else:
                Account(email=self.request.get('email'), passwd=hashlib.sha1(self.request.get('passwd')).hexdigest(), name=self.request.get('name', self.request.get('email'))).put()

        elif self.request.get('model') == 'AccountToken':
            if self.request.get('key'):
                db.delete(db.Key(encoded=self.request.get('key')))
            else:
                account_key = db.Key(encoded=self.request.get('account_key'))
                AccountToken(parent=account_key, account=account_key, token=hashlib.sha512(uuid.uuid1().hex).hexdigest(), service=self.request.get('service')).put()

        elif self.request.get('model') == 'Profile':
            if self.request.get('key'):
                profile_key = db.Key(encoded=self.request.get('key'))
                db.delete(Health.all(keys_only=True).ancestor(profile_key).fetch(limit=1000))
                db.delete(File.all(keys_only=True).ancestor(profile_key).fetch(limit=1000))
                db.delete(profile_key)
            else:
                account_key = db.Key(encoded=self.request.get('account_key'))
                Profile(key_name=key_name(), parent=account_key, account=account_key, name=self.request.get('name')).put()

        elif self.request.get('model') == 'Health':
            if self.request.get('key'):
                db.delete(db.Key(encoded=self.request.get('key')))
            else:
                profile = Profile.get(self.request.get('profile_key'))
                Health(key_name=key_name(), parent=profile, account=profile.account, profile=profile, category_ccr=self.request.get('category_ccr'), category_item=self.request.get('category_item')).put()

        elif self.request.get('model') == 'File':
            if self.request.get('key'):
                db.delete(db.Key(encoded=self.request.get('key')))
            else:
                profile = Profile.get(self.request.get('profile_key'))
                File(key_name=key_name(), parent=profile, account=profile.account, profile=profile, title=self.request.get('title'), file='x', mime='text/plain').put()

#         elif self.request.get('model') == 'ProfileShare':
#             if self.request.get('key'):
#                 db.delete(db.Key(encoded=self.request.get('key')))
#             else:
#                 profile = Profile.get(self.request.get('profile_key'))
#                 account = Account.get(self.request.get('account_key'))
#                 ProfileShare(parent=profile, account=profile.account, profile=profile, to_account=account).put()
# 
#         elif self.request.get('model') == 'HealthNote':
#             if self.request.get('key'):
#                 db.delete(db.Key(encoded=self.request.get('key')))
#             else:
#                 entry = Health.get(self.request.get('health_key'))
#                 HealthNote(parent=entry, account=entry.account, entry=entry, text=self.request.get('text')).put()
                    
        self.redirect('/admin')

def main():
    application = webapp.WSGIApplication([
        ('/admin', Admin),
    ], debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
