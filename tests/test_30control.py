# -*- coding: utf-8 -*-

import pytest
import testinfra
import subprocess
import psycopg2
import shutil
import time
import os

@pytest.fixture(scope='module')
def host(docker_compose, request):
    docker_compose_file = request.config.getoption("--docker-compose-file")
    docker_id = subprocess.check_output([
            'docker-compose',
            '-f', docker_compose_file,
            'ps', '-q', 'control'
          ]).decode().strip()
    yield testinfra.get_host("docker://"+docker_id)


def test_exporter_process(host):
    pid = host.process.get(pid=1)
    assert pid.args == ("{pgbouncer-confi} /usr/local/bin/python "
                        "/usr/local/bin/pgbouncer-config-reload -vv")


def test_pgbouncerctl_exists(host):
    assert host.exists("pgbouncerctl")


def test_pgbouncerctl_exec(host):
    result = host.run("pgbouncerctl -h", shell=True)
    print(result)
    assert result.rc == 0
    assert result.stdout != ""
    assert not result.stderr
    result = host.run("pgbouncerctl  \"SHOW HELP;\"", shell=True)
    print(result)
    assert result.rc == 0
    assert result.stdout != ""
    assert result.stderr != ""


def test_config_reload(host):
    # Establish connection to test DB
    test_conn = psycopg2.connect(
                    user='test',
                    password='qwerty',
                    host='127.0.0.1',
                    port=16432,
                    database='testdb'
                )
    test_conn.set_isolation_level(0)
    test_cur = test_conn.cursor()

    # Reload pgbouncer configuration
    host.run("pgbouncerctl \"RELOAD;\"", shell=True)

    test_cur.execute("SELECT 1;")
    test_conn.commit()
    record = test_cur.fetchall()
    test_cur.close()
    test_conn.close()
    assert record[0] == (1,)


def test_config_loaded():
    pass


def test_userlist_reload(host):
    shutil.copy('./tests/userlist/userlist.txt', './tests/userlist/userlist.txt.bkp')
    with open("./tests/userlist/userlist.txt", "a") as f:
        f.write("\"test2\" \"qwerty\"\n")
    with open("./tests/userlist/..data", "w+") as f:
        f.write("Hello word")
    time.sleep(11)

    test_conn = psycopg2.connect(
                    user='test2',
                    password='qwerty',
                    host='127.0.0.1',
                    port=16432,
                    database='testdb'
                )
    test_conn.set_isolation_level(0)
    test_cur = test_conn.cursor()

    test_cur.execute("SELECT 1;")
    test_conn.commit()
    record = test_cur.fetchall()
    test_cur.close()
    test_conn.close()
    shutil.copy('./tests/userlist/userlist.txt.bkp', './tests/userlist/userlist.txt')
    os.remove('./tests/userlist/userlist.txt.bkp')
    os.remove("./tests/userlist/..data")
    assert record[0] == (1,)

    pid = host.process.get(pid=1)
    assert pid.args == ("{pgbouncer-confi} /usr/local/bin/python "
                        "/usr/local/bin/pgbouncer-config-reload -vv")


