#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

class ReferenceFeed(webapp.RequestHandler):
    def get(self):
        q = self.request.get('q')
        refs = Reference.all().filter('category_item=', q).order('category_item').fetch(limit=10)
        render_template('ref_feed.xml', self, locals())

def main():
    application = webapp.WSGIApplication([
        ('/health/ref', ReferenceFeed),
        ('/health/ref/(.+)', ReferenceFeed),

    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
