from typing import Dict

import pytest

from ptl.providers import Provider, Tool


Registry = Dict[str, Provider]


DUMMY_PROVIDER = Provider(
    tools={
        Tool.COMPILE: 'dummy-compile',
        Tool.SYNC: 'dummy-sync',
    },
)

FAKE_PROVIDER = Provider(
    tools={
        Tool.COMPILE: 'fake tool compile',
        Tool.SYNC: 'fake tool sync',
    },
)


@pytest.fixture
def registry(monkeypatch: pytest.MonkeyPatch) -> Registry:
    registry: Registry = {}
    monkeypatch.setattr(Provider, '_registry', registry)
    return registry


def test_register(registry: Registry):
    Provider.register('DUMMY', DUMMY_PROVIDER)
    Provider.register('FAKE', FAKE_PROVIDER)

    assert registry == {
        'DUMMY': DUMMY_PROVIDER,
        'FAKE': FAKE_PROVIDER,
    }
    assert getattr(Provider, 'DUMMY') == DUMMY_PROVIDER
    assert getattr(Provider, 'FAKE') == FAKE_PROVIDER


@pytest.mark.usefixtures('registry')
def test_get_tool_candidates_tool_enum():
    Provider.register('DUMMY', DUMMY_PROVIDER)
    Provider.register('FAKE', FAKE_PROVIDER)

    candidates = Provider.get_tool_candidates(Tool.SYNC)

    assert candidates == ('dummy-sync', 'fake tool sync')


@pytest.mark.usefixtures('registry')
def test_get_tool_candidates_str():
    Provider.register('FAKE', FAKE_PROVIDER)
    Provider.register('DUMMY', DUMMY_PROVIDER)

    candidates = Provider.get_tool_candidates('compile')

    assert candidates == ('fake tool compile', 'dummy-compile')
