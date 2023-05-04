import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # To try to avoid the Neon errors I sometimes get.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
