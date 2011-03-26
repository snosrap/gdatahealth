#!/usr/bin/env python

from models import *
from utils import *

import logging, email, hashlib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail

# Handlers

class NewUserHandler(InboundMailHandler):
    def receive(self, mail_message):
        new_account_email = mail_message.subject
        new_password = key_name()
        if new_account_email and Account.all().filter('email =', new_account_email).count() == 0:
            account = Account(email=new_account_email, passwd=hashlib.sha1(new_password).hexdigest(), name=new_account_email)
            account.put()
            Profile(key_name=key_name(), parent=account, account=account, name=account.name, author=account.email).put()

class MailHandler(InboundMailHandler):
    def receive(self, mail_message):
        profile_key = re.findall('\/_ah\/mail\/(.+)%40gdatahealth.appspotmail.com', self.request.path).pop()
        profile = Profile.get(profile_key)
        if hasattr(mail_message, 'attachments'):
            for filename, attachment in mail_message.attachments:
                File(key_name=key_name(), parent=profile, profile=profile, account=profile.parent(), title=filename, description=mail_message.subject, file=db.Blob(attachment.decode()), mime=get_mime_type(filename)).put()

def get_mime_type(filename):
    try:
        return mail._GetMimeType(filename)
    except:
        return 'application/octet-stream'
            
def main():
    application = webapp.WSGIApplication([
        ('/_ah/mail/newuser%40gdatahealth.appspotmail.com', NewUserHandler),
        ('/_ah/mail/.+', MailHandler),
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
