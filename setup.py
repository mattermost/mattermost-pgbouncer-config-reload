import os
import sys
from setuptools import setup

if sys.version_info.major < 3:
    raise RuntimeError('Installing requires Python 3 or newer')

# Read the long description from README.md
with open('README.md') as file:
    long_description = file.read()

version = '1.0.0'

setup(
  name             = 'pgbouncer-config-reload',
  packages         = ['pgbouncer_config_reload'],
  version          = version,
  description      = 'Pgbouncer config reloader',
  long_description = long_description,
  author           = 'Konstantin Velichko',
  author_email     = 'kvelichko@wallarm.com',
  url              = 'https://github.com/wallarm/pgbouncer-config-reload',
  keywords         = ['pgbouncer', 'docker'],
  classifiers      = [],
  python_requires  = ' >= 3',
  install_requires = [
        'psycopg2 >= 2.8.3',
        'python-json-logger >= 0.1.5',
        'configargparse >= 0.14.0',
        'pyinotify >= 0.9.6'
      ],
  scripts          = ["bin/pgbouncerctl"],
  entry_points     = {
    'console_scripts': [
        'pgbouncer-config-reload=pgbouncer_config_reload.cli:main'
    ]
  }
)

