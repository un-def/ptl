from unittest.mock import Mock

import pytest

from ptl.exceptions import ToolNotFound
from ptl.providers import Provider, Tool, find_tool

from .base import BaseTestSuite


class TestSuite(BaseTestSuite):

    def set_candidates(self, *candidates: str) -> None:
        mock = Mock(spec_set=Provider.get_tool_candidates)
        mock.return_value = candidates
        self.monkeypatch.setattr(Provider, 'get_tool_candidates', mock)

    def test_ok(self) -> None:
        bin_dir = self.override_path_variable()
        exec_path = bin_dir / 'dummy'
        self.create_executable(exec_path)
        self.set_candidates('fake-sync', 'dummy sync')

        command_line, version = find_tool('sync')

        assert command_line == [str(exec_path), 'sync']
        assert version == 'dummy sync version 0.0.1'

    def test_not_found(self) -> None:
        self.override_path_variable()
        self.set_candidates('fake-compile', 'dummy compile')

        with pytest.raises(
            ToolNotFound,
            match='candidates tried: `fake-compile`, `dummy compile`',
        ):
            find_tool(Tool.COMPILE)
