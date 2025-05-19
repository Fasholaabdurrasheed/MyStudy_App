from .base import *

DEBUG = False

# Email backend for production (SMTP)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Security settings
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Admin email
ADMINS = [('Admin', 'mystudyapp.unilorin@gmail.com')]
