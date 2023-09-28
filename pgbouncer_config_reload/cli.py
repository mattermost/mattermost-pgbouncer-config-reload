#!/usr/bin/env python3
"""
Tools for monitoring changes configuration and reload pgbouncer
"""


import configargparse
import logging
import pyinotify
import psycopg2
import os
import sys
import signal
import time


__author__ = "kvelichko"
__email__ = "kvelichko@wallarm.com"


log = logging.getLogger('configmap-reload')


class ConfigmapHandler(pyinotify.ProcessEvent):

    def __init__(
            self,
            host,
            port,
            user,
            password,
            database='pgbouncer',
            timeout=10
          ):
        """
        :param host - pgbouncer hostname
        :param port - pgbouncer port
        :param user - pgbouncer admin user
        :param password - pgbouncer admin password
        :param database - pgbouncer admin database
        :param timeout - timeout before send reload to pgbouncer
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.timeout = timeout

    def pgbouncer_reload(self):
        """
        Function for reload pgbouncer
        """

        connection = None
        log.debug("Pgbouncer gracefull reload starting...")
        try:
            connection = psycopg2.connect(
                    user=self.user,
                    password=self.password,
                    host=self.host,
                    port=self.port,
                    database=self.database
                )
            connection.set_isolation_level(0)
            cursor = connection.cursor()
            cursor.execute("RELOAD;")
            connection.commit()
        except (Exception, psycopg2.Error) as error:
            log.error("Failed to RELOAD pgbouncer: %s" % (error))
        finally:
            if (connection):
                cursor.close()
                connection.close()
                log.debug("Pgbouncer connection is closed")
                log.info("Pgbouncer gracefull reloaded.")

    def process_IN_CREATE(self, event):
        log.info("CREATE event: '%s'" % (event.pathname))
        if os.path.basename(event.pathname).startswith('..data'):
            time.sleep(self.timeout)
            self.pgbouncer_reload()


def exit_signal_handler(signum, frame):
    """
    Function for logging signals and interrupt program
    """
    log.info("Signal '%s' received. Shutdown..."
             % (signal.Signals(signum).name))
    sys.exit()


def run(args={}):
    """
    main function
    :param args - dict of arguments
    """
    # watch manager
    wm = pyinotify.WatchManager()
    for path in args.config_path.split(";"):
        wm.add_watch(path, pyinotify.IN_CREATE, rec=True)

    # event handler
    eh = ConfigmapHandler(
            args.pgbouncer_host,
            args.pgbouncer_port,
            args.pgbouncer_user,
            args.pgbouncer_password,
            args.pgbouncer_database,
            int(args.pgbouncer_reload_timeout)
        )

    # notifier
    log.info("Entering event loop...")
    notifier = pyinotify.Notifier(wm, eh)
    notifier.loop()


def main():
    p = configargparse.ArgParser(
            description='Tools for monitoring pgbouncer configurations'
                        ' files and gracefull reload it.'
          )
    p.add("-v", "--verbose",
          help='Verbosity (-v -vv -vvv)',
          action='count',
          env_var='VERBOSE',
          default=0)
    p.add("-c", "--config-path",
          help="Semicolons separated configuration path for watching. (Ex: /etc/pgbouncer;/etc/userlist)",
          required=True,
          env_var='CONFIG_PATH')
    p.add("-H", "--pgbouncer-host",
          help="Pgbouncer host",
          required=True,
          env_var='PGBOUNCER_HOST')
    p.add("-p", "--pgbouncer-port",
          help="Pgbouncer port. (default: 6432)",
          default=6432,
          env_var='PGBOUNCER_PORT')
    p.add("-u", "--pgbouncer-user",
          help="Pgbouncer admin user (default: pgbouncer)",
          default='pgbouncer',
          env_var='PGBOUNCER_USER')
    p.add("-P", "--pgbouncer-password",
          help="Pgbouncer admin password",
          required=True,
          env_var='PGBOUNCER_PASSWORD')
    p.add("-d", "--pgbouncer-database",
          help="Pgbouncer admin database (default: pgbouncer)",
          default='pgbouncer',
          env_var='PGBOUNCER_DATABASE')
    p.add("-t", "--pgbouncer-reload-timeout",
          help="Timeout before reload configuration of pgbouncer "
               "(default: 10)",
          default=10,
          env_var='PGBOUNCER_RELOAD_TIMEOUT')
    p.add("-j", "--json-log",
          action='store_true',
          help="Print logs as JSON",
          default=False,
          env_var='LOG_JSON')
    args = p.parse_args()

    # Configure log
    handler = logging.StreamHandler()
    if args.json_log:
        from pythonjsonlogger import jsonlogger
        formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
    else:
        formatter = logging.Formatter(
                fmt='%(asctime)s\t%(levelname)s: %(message)s',
                datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
    log.addHandler(handler)

    loglvl = logging.ERROR
    if args.verbose > 0:
        loglvl = 40 - 10*args.verbose
    log.setLevel(loglvl)

    # Configure interrupt signal handler
    signal.signal(signal.SIGINT, exit_signal_handler)
    signal.signal(signal.SIGTERM, exit_signal_handler)

    log.info("Initialization complete...")

    run(args)


if __name__ == "__main__":
    main()
