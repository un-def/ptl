import pytest

from ptl.commands import show
from ptl.exceptions import InputDirectoryError

from tests.testlib import InFileTestSuiteBase


class TestSuite(InFileTestSuiteBase):

    @pytest.fixture(autouse=True)
    def setup(
        self, base_setup: None, capsys: pytest.CaptureFixture[str],
    ) -> None:
        self.capsys = capsys

    def get_output(self) -> str:
        return self.capsys.readouterr().out

    def prepare_files(self) -> None:
        self.create_file('child.in', """
            -c parent.txt
            foo  # comment
        """)
        self.create_file('parent.in', """
            -r grandparent

            bar==0.0.1
            # comment
            baz
        """)
        self.create_file('grandparent.in', """
            qux
        """)

    def test_all(self) -> None:
        self.prepare_files()

        show(input_dir=self.input_dir)

        assert self.get_output() == self.dedent("""
            # grandparent.ptl.in
            qux

            # parent.ptl.in
            -r grandparent.txt
            bar==0.0.1
            baz

            # child.ptl.in
            -c parent.txt
            -c grandparent.txt
            foo

        """)

    def test_specified_layers(self) -> None:
        self.prepare_files()

        show(
            input_dir=self.input_dir,
            layers=['parent'], include_parent_layers=True,
        )

        assert self.get_output() == self.dedent("""
            # grandparent.ptl.in
            qux

            # parent.ptl.in
            -r grandparent.txt
            bar==0.0.1
            baz

        """)

    def test_only_specified_layers(self) -> None:
        self.prepare_files()

        show(
            input_dir=self.input_dir,
            layers=['grandparent', 'child'], include_parent_layers=False,
        )

        # since child has no direct reference to grandparent, sort_infiles()
        # will put then on the same level and sort lexicographically
        assert self.get_output() == self.dedent("""
            # child.ptl.in
            -c parent.txt
            -c grandparent.txt
            foo

            # grandparent.ptl.in
            qux

        """)

    def test_error_no_infiles(self) -> None:
        with pytest.raises(InputDirectoryError, match=r'no \*\.in files'):
            show(input_dir=self.input_dir)
