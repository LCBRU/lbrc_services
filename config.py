import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig(object):
    DEBUG = os.getenv("DEBUG", "False") == 'True'
    FILE_UPLOAD_DIRECTORY = os.environ["FILE_UPLOAD_DIRECTORY"]
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False") == 'True'
    SMTP_SERVER = os.getenv("SMTP_SERVER", None)
    ADMIN_EMAIL_ADDRESSES = os.environ["ADMIN_EMAIL_ADDRESSES"]
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "lcbruit@leicester.ac.uk")
    SECURITY_EMAIL_SENDER = os.getenv("SECURITY_EMAIL_SENDER", "lcbruit@leicester.ac.uk")
    SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = os.getenv("SECURITY_SEND_PASSWORD_CHANGE_EMAIL", "False") == 'True'

    SECRET_KEY = os.environ["SECRET_KEY"]
    SECURITY_PASSWORD_SALT = os.environ["SECURITY_PASSWORD_SALT"]
    SECURITY_CONFIRM_SALT = os.getenv("SECURITY_CONFIRM_SALT", SECURITY_PASSWORD_SALT)
    SECURITY_RESET_SALT = os.getenv("SECURITY_RESET_SALT", SECURITY_PASSWORD_SALT)
    SECURITY_LOGIN_SALT = os.getenv("SECURITY_LOGIN_SALT", SECURITY_PASSWORD_SALT)
    SECURITY_REMEMBER_SALT = os.getenv("SECURITY_REMEMBER_SALT", SECURITY_PASSWORD_SALT)

    SECURITY_TRACKABLE = "True"
    ERROR_EMAIL_SUBJECT = "LBRC Study Data Upload Error"
    WTF_CSRF_ENABLED = True
    SECURITY_CHANGEABLE = True
    SECURITY_RECOVERABLE = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(BaseConfig):
    """Configuration for general testing"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    FILE_UPLOAD_DIRECTORY = os.getenv("TEST_FILE_UPLOAD_DIRECTORY", BaseConfig.FILE_UPLOAD_DIRECTORY)
    SMTP_SERVER = None
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False


class TestConfigCRSF(TestConfig):
    WTF_CSRF_ENABLED = True
