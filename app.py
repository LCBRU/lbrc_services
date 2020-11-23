#!/usr/bin/env python3

from lbrc_requests import create_app

application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000)
