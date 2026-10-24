"""Pelican settings for the deployable build at pe502.com."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pelicanconf import *  # noqa: E402,F403

SITEURL = "https://pe502.com"
RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
