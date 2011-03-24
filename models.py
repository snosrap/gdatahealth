#!/usr/bin/env python

from google.appengine.ext import db
import datetime

class Account(db.Model):
    user = db.UserProperty() # Google Account (optional)
    email = db.EmailProperty()
    passwd = db.StringProperty() # sha1
    name = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class AccountToken(db.Model):
    account = db.ReferenceProperty(Account)
    token = db.StringProperty()
    service = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    expires = db.DateTimeProperty(default=datetime.datetime.now() + datetime.timedelta(14))

class Profile(db.Model):
    account = db.ReferenceProperty(Account)
    name = db.StringProperty()
    author = db.EmailProperty()
    gh_token = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
class Health(db.Expando):
    account = db.ReferenceProperty(Account)
    profile = db.ReferenceProperty(Profile)
    gh_identifier = db.StringProperty()
    category_ccr = db.CategoryProperty() # MEDICATION
    category_item = db.CategoryProperty() # Captopril
    category_kind = db.CategoryProperty(default="http://schemas.google.com/health/kinds#profile")
    ccr = db.TextProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class Reference(db.Model):
    category_ccr = db.CategoryProperty() # MEDICATION
    category_item = db.CategoryProperty() # Captopril
    category_item_kwds = db.StringListProperty() # captopril, i.e., lowercase keywords for a search

# TODO:

class HealthNote(db.Model):
    account = db.ReferenceProperty(Account)
    entry = db.ReferenceProperty(Health)
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class ProfileShare(db.Model):
    account = db.ReferenceProperty(Account)
    profile = db.ReferenceProperty(Profile)
    to_account = db.ReferenceProperty(Account, collection_name="profileshare_to_set")
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

class File(db.Model):
    account = db.ReferenceProperty(Account)
    profile = db.ReferenceProperty(Profile)
    file = db.BlobProperty()
    title = db.StringProperty()
    description = db.TextProperty()
    mime = db.StringProperty()
    size = db.IntegerProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
