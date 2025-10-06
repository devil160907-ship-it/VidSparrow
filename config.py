import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    GOOGLE_CLIENT_ID = "1060434691975-413tbr8hlps4iqs10elgpht6as2ksrc6.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "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"
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vidsparrow.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)