import logging.config

import tomli

# Must precede any imports, see https://stackoverflow.com/a/20280587.
with open("logging.toml", "rb") as _file:
    _settings = tomli.load(_file)
    logging.config.dictConfig(_settings)
