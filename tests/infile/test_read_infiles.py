import pytest

from ptl.exceptions import UnknownReference
from ptl.infile import InFile, Reference, read_infiles

from .base import BaseTestSuite


class TestSuite(BaseTestSuite):

    def test_empty_input_dir(self):
        infiles = read_infiles(self.input_dir)

        assert infiles == ()

    def test_parsing(self):
        self.create_infile('parent-1.in')
        self.create_infile('parent-2.in')
        self.create_infile('parent-3.in')
        self.create_infile('main.in', """
            foo  ==3.3.1  #inline comment
            \t bar[extra]   \t\r
                -r parent-1

            baz#notacomment #comment
            -r parent-3.in
            # comment
            -c parent-2.txt
                #comment
            https://example.com#egg=foo
        """.rstrip())

        infiles = read_infiles(self.input_dir)

        assert len(infiles) == 4
        main = next(filter(lambda infile: infile.stem == 'main', infiles))
        assert main.dependencies == [
            'foo  ==3.3.1',
            'bar[extra]',
            'baz#notacomment',
            'https://example.com#egg=foo',
        ]
        assert main.references == {
            Reference('r', InFile('parent-1.in')),
            Reference('c', InFile('parent-2.in')),
            Reference('r', InFile('parent-3.in')),
        }

    def test_unknown_reference(self):
        self.create_infile('main.in', '-r unknown.txt')

        with pytest.raises(UnknownReference, match='main.in: unknown'):
            read_infiles(self.input_dir)
