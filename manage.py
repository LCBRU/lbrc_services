#!/usr/bin/env python
from migrate.versioning.shell import main
from config import BaseConfig

if __name__ == "__main__":
    main(repository="migrations", url=BaseConfig.SQLALCHEMY_DATABASE_URI, debug="True")
