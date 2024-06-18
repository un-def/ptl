import pytest

from ptl.infile import InFile, InputDirectoryError, get_infiles

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):

    def test_ok(self) -> None:
        self.create_file('child.in', """
            -c parent.txt
            foo
        """)
        self.create_file('parent.in', """
            -r grandparent
            bar
            baz
        """)
        self.create_file('grandparent.in', """
            qux
        """)

        infiles = get_infiles(self.input_dir)

        assert infiles == [
            InFile('grandparent.in'), InFile('parent.in'), InFile('child.in')]
        assert infiles[0].render() == (
            'qux\n'
        )
        assert infiles[1].render() == (
            '-r grandparent.txt\n'
            'bar\n'
            'baz\n'
        )
        assert infiles[2].render() == (
            '-c parent.txt\n'
            '-c grandparent.txt\n'
            'foo\n'
        )

    def test_no_infiles(self) -> None:
        with pytest.raises(InputDirectoryError, match=r'no \*\.in files'):
            get_infiles(self.input_dir)
