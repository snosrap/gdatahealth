#!/usr/bin/env python

import logging, email

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail

# Handlers

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
        MailHandler.mapping(),
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
