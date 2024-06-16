import pytest

from ptl.infile import InFile, InputDirectoryError, get_infiles

from .base import BaseTestSuite


class TestSuite(BaseTestSuite):

    def test_ok(self):
        self.create_infile('child.in', """
            -c parent.txt
            foo
        """)
        self.create_infile('parent.in', """
            -r grandparent
            bar
            baz
        """)
        self.create_infile('grandparent.in', """
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

    def test_no_infiles(self):
        with pytest.raises(InputDirectoryError, match=r'no \*\.in files'):
            get_infiles(self.input_dir)
