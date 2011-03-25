#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import re
import urllib

class ReferenceFeed(webapp.RequestHandler):
    def get(self, categoryParam=None):
        q = self.request.get('q')

        refs = Reference.all()

        if self.request.get('category') or categoryParam:
            categoryParam = self.request.get('category') or urllib.unquote(categoryParam)
            for category in categoryParam.split(','): # AND
                categories = [parse_category(cat) for cat in category.split('|')] # OR
                filter, value = make_filter(categories)
                refs = refs.filter(filter, value)

        if q:
            refs = refs.filter('category_item_kwds =', q)

        refs = refs.order('category_ccr').order('category_item')
        refs = refs.fetch(limit=int(self.request.get('max-results', '10')), offset=int(self.request.get('start-index', '1')) - 1)

        render_template('ref_feed.xml', self, locals())

def main():
    application = webapp.WSGIApplication([
        ('/health/ref', ReferenceFeed),
        ('/health/ref/-/(.+)', ReferenceFeed),

    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
