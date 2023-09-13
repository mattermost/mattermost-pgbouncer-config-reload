# -*- coding: utf-8 -*-

import pytest
import subprocess


def pytest_addoption(parser):
    parser.addoption(
        "--docker-compose-file", action="store",
        default="tests/docker-compose.yml",
        help="Location of docker-compose.yml file"
      )
    parser.addoption(
        "--docker-compose-without-down", action="store_true",
        default=False,
        help="Do not stop docker-compose after tests"
      )


@pytest.fixture
def docker_compose_file(request):
    return request.config.getoption("--docker-compose-file")


@pytest.fixture(scope='session')
def docker_compose(request):
    docker_compose_file = request.config.getoption("--docker-compose-file")
    docker_compose_without_stop = request.config.getoption(
            "--docker-compose-without-down"
          )
    subprocess.check_call([
            'docker-compose',
            '-f', docker_compose_file,
            'up', '-d'
          ])

    yield

    if not docker_compose_without_stop:
        subprocess.check_call([
            'docker-compose',
            '-f', docker_compose_file,
            'down'
          ])
