# pgbouncer-config-reload
=======================

This repo is forked from https://github.com/wallarm/pgbouncer-config-reload

How to use it:
--------------

 + Use it with helm chart https://github.com/wallarm/pgbouncer-chart

Basic configuration via environment variables
---------------------------------------------

| Environment variable    | Default     | Description
--------------------------|-------------|-------------
| CONFIG_PATH             | `undef`     | Required. Path for create event monitoring
| PGBOUNCER_HOST          | `undef`     | Required. Pgbouncer hostname
| PGBOUNCER_PORT          | `6432`      | Pgbouncer port.
| PGBOUNCER_USER          | `pgbouncer` | Pgbouncer admin username
| PGBOUNCER_PASSWORD      | `undef`     | Pgbouncer admin password
| PGBOUNCER_DATABASE      | `pgbouncer` | Pgbouncer control database
| PGBOUNCER_RELOAD_TIMEOUT| `10`        | Timeout between create event and pgbouncer reload
| LOG_JSON                | `False`     | Output log format json
