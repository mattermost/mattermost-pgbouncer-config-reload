#!/usr/bin/env python3
"""
Tools for monitoring changes to configuration and reloading pgbouncer.
"""

import configargparse
import logging
import psycopg2
import os
import sys
import signal
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

__author__ = "kvelichko"
__email__ = "kvelichko@wallarm.com"


log = logging.getLogger('configmap-reload')


class ConfigmapHandler(FileSystemEventHandler):
    """
    A watchdog event handler to reload pgbouncer when relevant files change.
    """
    def __init__(self, host, port, user, password, database='pgbouncer', timeout=10):
        """
        :param host: pgbouncer hostname
        :param port: pgbouncer port
        :param user: pgbouncer admin user
        :param password: pgbouncer admin password
        :param database: pgbouncer admin database
        :param timeout: wait time (seconds) before sending reload to pgbouncer
        """
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.timeout = timeout

    def on_created(self, event):
        """
        Triggered when a file/directory is created.
        If the created file's name starts with "..data",
        wait and then reload pgbouncer.
        """
        if not event.is_directory:
            log.info(f"CREATE event: '{event.src_path}'")
            if os.path.basename(event.src_path).startswith('..data'):
                time.sleep(self.timeout)
                self.pgbouncer_reload()

    def pgbouncer_reload(self):
        """
        Execute pgbouncer RELOAD.
        """
        log.debug("Pgbouncer graceful reload starting...")
        connection = None
        cursor = None
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
            log.error(f"Failed to RELOAD pgbouncer: {error}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                log.debug("Pgbouncer connection is closed")
                log.info("Pgbouncer gracefully reloaded.")


def exit_signal_handler(signum, frame):
    """
    Handle termination signals to ensure clean shutdown.
    """
    log.info(f"Signal '{signal.Signals(signum).name}' received. Shutting down...")
    sys.exit()


def run(args):
    """
    Main function that sets up the file observers and starts the watchdog loop.
    """
    observer = Observer()

    event_handler = ConfigmapHandler(
        host=args.pgbouncer_host,
        port=args.pgbouncer_port,
        user=args.pgbouncer_user,
        password=args.pgbouncer_password,
        database=args.pgbouncer_database,
        timeout=int(args.pgbouncer_reload_timeout)
    )

    for path in args.config_path.split(";"):
        if os.path.isdir(path):
            log.info(f"Watching path: {path}")
            observer.schedule(event_handler, path, recursive=True)
        else:
            log.warning(f"Path '{path}' is not a directory or does not exist. Skipping...")

    observer.start()
    log.info("Entering event loop...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


def main():
    p = configargparse.ArgParser(
        description='Tool for monitoring pgbouncer configuration files and gracefully reloading them.'
    )
    p.add("-v", "--verbose",
          help='Verbosity (-v -vv -vvv)',
          action='count',
          env_var='VERBOSE',
          default=0)
    p.add("-c", "--config-path",
          help="Semicolon-separated paths to watch. (e.g. /etc/pgbouncer;/etc/userlist)",
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
          help="Timeout before reloading pgbouncer (default: 10)",
          default=10,
          env_var='PGBOUNCER_RELOAD_TIMEOUT')
    p.add("-j", "--json-log",
          action='store_true',
          help="Enable JSON-formatted logs",
          default=False,
          env_var='LOG_JSON')

    args = p.parse_args()

    # Configure log
    handler = logging.StreamHandler()
    if args.json_log:
        # Adjusted import for python-json-logger change
        from pythonjsonlogger.json import JsonFormatter
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s\t%(levelname)s: %(message)s',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

    log.addHandler(handler)
    loglvl = logging.ERROR
    if args.verbose > 0:
        loglvl = max(logging.ERROR - 10 * args.verbose, logging.DEBUG)
    log.setLevel(loglvl)

    # Configure interrupt signal handlers
    signal.signal(signal.SIGINT, exit_signal_handler)
    signal.signal(signal.SIGTERM, exit_signal_handler)

    log.info("Initialization complete...")
    run(args)


if __name__ == "__main__":
    main()
