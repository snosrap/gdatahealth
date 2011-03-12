#!/usr/bin/env python

from utils import *
from models import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import gdata
import gdata.health
import gdata.health.service
import email.parser
import email
        
class FileFeed(webapp.RequestHandler):
    def get(self, profileId):
        profile_key = key_from_request(self.request, profileId)
        files = File.all().ancestor(profile_key).order('-created').fetch(limit=1000)
        render_template('files_feed.xml', self, locals())

    def post(self, profileId):
        profile_key = key_from_request(self.request, profileId)
        file = File(key_name=key_name(), parent=profile_key, profile=profile_key, account=profile_key.parent())
        file = populate_file_from_request(file, self.request)
        file.put()
        render_template('files_entry.xml', self, locals())
    
    def put(self, profileId):
        self.post(profileId)

class FileEntry(webapp.RequestHandler):
    def get(self, profileId, fileId):
        file = File.get(key_from_request(self.request, profileId, fileId=fileId))
        render_template('files_entry.xml', self, locals())
    
    def post(self, profileId, fileId):
        profile_key = key_from_request(self.request, profileId)
        file = File.get(key_from_request(self.request, profileId, fileId=fileId))
        file = populate_file_from_request(file, self.request)
        file.put()
        render_template('files_entry.xml', self, locals())

    def put(self, profileId, fileId):
        self.post(profileId, fileId)
                
    def delete(self, profileId, fileId):
        db.delete(key_from_request(self.request, profileId, fileId=fileId))

class FileContent(webapp.RequestHandler):
    def get(self, profileId, fileId):
        file = File.get(key_from_request(self.request, profileId, fileId=fileId))
        if file:
            self.response.headers['Content-Type'] = file.mime
            self.response.out.write(file.file)

# Helpers

def populate_file_from_request(file, request):
    content_type = request.headers.get('Content-Type')
    payload = request.body
    
    if content_type.startswith("multipart/related"):
        payload = "\n".join(["%s: %s" % (h, request.headers[h]) for h in request.headers]) + "\n\n" + payload
        
    if request.headers.get('Slug'):
        file.title = request.headers.get('Slug')

    return populate_file(file=file, content_type=content_type, payload=payload)

def populate_file(file, content_type, payload):
    if content_type.startswith("multipart/related"):
        fp = email.parser.FeedParser()
        fp.feed(payload)
        msg = fp.close()
        for x in msg.walk():
            if not x.get_content_type().startswith("multipart/related"):
                file = populate_file(file, x.get_content_type(), x.get_payload())
    elif content_type.startswith("application/atom+xml"):
        entry = gdata.GDataEntryFromString(payload)
        if entry:
            file.title = entry.title.text
            file.description = entry.content.text
    elif content_type:
        file.file = db.Blob(payload)
        file.mime = content_type
    
    return file

def main():
    application = webapp.WSGIApplication([
        ('/health/feeds/profile/ui/([\w.]+)/files', FileFeed),
        ('/health/feeds/profile/ui/([\w.]+)/files/([\w.]+)', FileEntry),
        ('/health/feeds/profile/ui/([\w.]+)/files/([\w.]+)/content', FileContent),
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
