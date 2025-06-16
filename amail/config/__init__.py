# This file makes 'amail/config' a Python package.
# The 'config' module within this package (config.py) can be imported using:
# from amail.config import config
# or, if you want to import specific variables from config.py directly into the package namespace:
# from .config import SECRET_KEY, EMAIL_ACCOUNTS # etc.
# For now, app/__init__.py uses `from amail.config import config as app_config`,
# which means app_config refers to the config.py module itself. This is fine.
