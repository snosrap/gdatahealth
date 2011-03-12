#!/usr/bin/env python

from models import *
from utils import *

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import hashlib
import uuid

# Handlers

class ClientLogin(webapp.RequestHandler):
    def get(self):
        email = self.request.get('Email')
        passwd = hashlib.sha1(self.request.get('Passwd')).hexdigest()
        service = self.request.get('service')
        account = Account.all().filter('email =', email).filter('passwd =', passwd).get()

        self.response.headers['Content-Type'] = "text/plain"

        if account:
            db.delete(AccountToken.all(keys_only=True).ancestor(account).fetch(limit=1000))
            token = hashlib.sha512(uuid.uuid1().hex).hexdigest()
            AccountToken(parent=account, account=account, token=token, service=service).put()
            self.response.out.write("Auth=%s" % token)
        else:
            self.response.out.write('Error=BadAuthentication')
            
    def post(self):
        self.get()

class ServiceLogin(webapp.RequestHandler):
    def get(self):
        render_template('ServiceLogin.html', self, locals())

class ServiceLoginAuth(webapp.RequestHandler):
    def post(self):
        email = self.request.get('Email')
        passwd = hashlib.sha1(self.request.get('Passwd')).hexdigest()
        service = self.request.get('service')
        account = Account.all().filter('email =', email).filter('passwd =', passwd).get()

        if account:
            db.delete(AccountToken.all(keys_only=True).ancestor(account).fetch(limit=1000))
            token = hashlib.sha512(uuid.uuid1().hex).hexdigest()
            AccountToken(parent=account, account=account, token=token, service=service).put()
            if self.request.scheme == "https":
                self.response.headers['Set-Cookie'] = "SSID=%s; Path=/; Secure; HttpOnly" % token
            elif self.request.scheme == "http":
                self.response.headers['Set-Cookie'] = "HSID=%s; Path=/; HttpOnly" % token
            self.redirect('/health/feeds/profile/list')

class Logout(webapp.RequestHandler):
    def get(self):
        self.response.headers['Set-Cookie'] = "SSID=X; Expires=Thu, 01-Jan-1970 00:00:01 GMT; Path=/; HttpOnly"
        self.response.headers['Set-Cookie'] = "HSID=X; Expires=Thu, 01-Jan-1970 00:00:01 GMT; Path=/; HttpOnly"
        self.redirect('/')

class NewAccount(webapp.RequestHandler):
    def get(self):
        render_template('NewAccount.html', self, locals())

class CreateAccount(webapp.RequestHandler):
    def get(self):
        render_template('CreateAccount.html', self, locals())
    
    def post(self):
        if len(self.request.get('Email')) and len(self.request.get('Passwd')) and len(self.request.get('PasswdAgain')) and self.request.get('Passwd') == self.request.get('PasswdAgain') and Account.all().filter('email =', self.request.get('Email')).count() == 0:
            account = Account(email=self.request.get('Email'), passwd=hashlib.sha1(self.request.get('Passwd')).hexdigest(), name=self.request.get('Email'))
            account.put()
            profile = Profile(key_name=key_name(), parent=account, account=account, name=account.name, author=account.email).put()
            render_template('CreateAccount.html', self, locals())
        else:
            self.response.out.write('<p>Account creation failed.</p>')

def main():
    application = webapp.WSGIApplication([
        # http://code.google.com/apis/health/docs/2.0/reference.html#Authentication
        ('/accounts/ClientLogin', ClientLogin),
        ('/accounts/ServiceLogin', ServiceLogin),
        ('/accounts/ServiceLoginAuth', ServiceLoginAuth),
        ('/accounts/Logout', Logout),
        ('/accounts/NewAccount', NewAccount),
        ('/accounts/CreateAccount', CreateAccount),
    ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()