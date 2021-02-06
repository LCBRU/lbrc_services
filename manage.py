#!/usr/bin/env python
from dotenv import load_dotenv

# UoL LAMP servers (python 3.6?) seem to need me to load dotenv here

load_dotenv()

from migrate.versioning.shell import main
from lbrc_flask.config import BaseConfig

if __name__ == "__main__":
    main(repository="migrations", url=BaseConfig.SQLALCHEMY_DATABASE_URI, debug="True")
