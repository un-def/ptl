import logging
from unittest.mock import Mock

import pytest

from ptl.cli import configure_logging


DEFAULT_FORMAT = '%(message)s'
VERBOSE_FORMAT = '[ %(asctime)s | %(name)s | %(levelname)s ] %(message)s'
QUIET_FORMAT = DEFAULT_FORMAT

DATE_FORMAT = '%d-%m-%Y %H:%M:%S'


@pytest.fixture
def basic_config_mock(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock(spec_set=logging.basicConfig)
    monkeypatch.setattr(logging, 'basicConfig', mock)
    return mock


def test_default(basic_config_mock: Mock):
    configure_logging(0)

    basic_config_mock.assert_called_once_with(
        level=logging.INFO, format=DEFAULT_FORMAT, datefmt=DATE_FORMAT)


@pytest.mark.parametrize('verbosity', [1, 2, 10])
def test_verbose(basic_config_mock: Mock, verbosity: int):
    configure_logging(verbosity)

    basic_config_mock.assert_called_once_with(
        level=logging.DEBUG, format=VERBOSE_FORMAT, datefmt=DATE_FORMAT)


@pytest.mark.parametrize('verbosity', [-1, -2, -10])
def test_quiet(basic_config_mock: Mock, verbosity: int):
    configure_logging(verbosity)

    basic_config_mock.assert_called_once_with(
        level=logging.ERROR, format=QUIET_FORMAT, datefmt=DATE_FORMAT)
