'''
MIT License

Copyright (c) 2023 White Ribbon Alliance. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

"""This module handles advanced logging. Logging both to a stdout and a centralized 3-rd party DB are supported."""

import os
import gzip
import json
import requests
import logging
from logging import Handler, Formatter
from app import env

# ----------------------------------------------------------------------------------------------------------------------------
# Inits
# ----------------------------------------------------------------------------------------------------------------------------

NEW_RELIC_HEADERS = {
    "Api-Key": os.environ.get("NEWRELIC_API_KEY"),
    "Content-Encoding": "gzip",
    "Content-Type": "application/gzip",
}

PROJECT_NAME = "wra-global-dashboard-api"
NEW_RELIC_URL = "https://log-api.eu.newrelic.com/log/v1"


# ----------------------------------------------------------------------------------------------------------------------------
# Custom loggers
# ----------------------------------------------------------------------------------------------------------------------------


class NewRelicHandler(Handler):
    def emit(self, record):
        log_payload = self.format(record)

        if env.STAGE == "prod":
            requests.post(NEW_RELIC_URL, data=log_payload, headers=NEW_RELIC_HEADERS)


class NewRelicFormatter(Formatter):
    def __init__(self):
        super().__init__()

    def format(self, record):
        message = record.getMessage()
        attributes = {
            key: value
            for key, value in record.__dict__.items()
            if key not in ("args", "message", "msg")
        }
        attributes["projectName"] = PROJECT_NAME
        payload = {
            "message": message,
            "attributes": attributes,
        }
        payload = gzip.compress(json.dumps(payload, default=str).encode("utf-8"))

        return payload


# ----------------------------------------------------------------------------------------------------------------------------
# Global operations on loggers
# ----------------------------------------------------------------------------------------------------------------------------


def init_custom_logger(logger, level: int = logging.INFO):
    # newrelic for centralized logging
    handler = NewRelicHandler()
    formatter = NewRelicFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # streaming for default container logging
    logger.addHandler(logging.StreamHandler())

    logger.setLevel(level)
