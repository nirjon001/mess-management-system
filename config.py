import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')
DB_NAME = os.environ.get('DB_NAME', 'mess_management_new')

SECRET_KEY = os.environ.get('SECRET_KEY', 'mess-system-secret-key-change-in-production')
