import pytest

from ptl.commands import show
from ptl.exceptions import InputDirectoryError

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):

    def test_ok(self, capsys: pytest.CaptureFixture[str]) -> None:
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

        show(input_dir=self.input_dir)

        assert capsys.readouterr().out == self.dedent("""
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

    def test_error_no_infiles(self) -> None:
        with pytest.raises(InputDirectoryError, match=r'no \*\.in files'):
            show(input_dir=self.input_dir)
