#!/usr/bin/env python

from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

# Handlers

class RootHandler(webapp.RequestHandler):
    def get(self):
        render_template('about.html', self, locals())

def main():
    application = webapp.WSGIApplication([
        ('/', RootHandler),
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
