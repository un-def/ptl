from typing import Iterable

import pytest

from ptl.exceptions import InputDirectoryError, UnknownReference
from ptl.infile import InFile, Reference, read_infiles

from tests.testlib import InFileTestSuite


class TestSuite(InFileTestSuite):

    def get_main_infile(self, infiles: Iterable[InFile]) -> InFile:
        for infile in infiles:
            if infile.stem == 'main':
                return infile
        raise AssertionError(f'main infile not found: {infiles}')

    def test_empty_input_dir(self) -> None:
        infiles = read_infiles(self.input_dir)

        assert infiles == ()

    def test_parsing_no_suffix(self) -> None:
        self.create_file('parent-1.in')
        self.create_file('parent-2.in')
        self.create_file('parent-3.in')
        self.create_file('main.in', """
            foo  ==3.3.1  #inline comment
            \t bar[extra]   \t\r
                -r parent-1

            baz#notacomment #comment
            -r parent-3.in
            # comment
            -c parent-2.txt
                #comment
            https://example.com#egg=foo
        """)

        infiles = read_infiles(self.input_dir)

        assert len(infiles) == 4
        main = self.get_main_infile(infiles)
        assert main.dependencies == [
            'foo  ==3.3.1',
            'bar[extra]',
            'baz#notacomment',
            'https://example.com#egg=foo',
        ]
        assert main.references == [
            Reference('r', InFile('parent-1.in')),
            Reference('r', InFile('parent-3.in')),
            Reference('c', InFile('parent-2.in')),
        ]

    def test_parsing_with_suffix(self) -> None:
        self.create_file('parent-1.requirements.in')
        self.create_file('parent-2.requirements.in')
        self.create_file('parent-3.requirements.in')
        self.create_file('parent-4.requirements.in')
        self.create_file('parent-5.requirements.in')
        self.create_file('parent-6.requirements.in')
        self.create_file('main.in', """
            foo  ==3.3.1  #inline comment
            \t bar[extra]   \t\r
                -r parent-1

            baz#notacomment #comment
            -r parent-3.in
            # comment
            -c parent-2.txt
                #comment
            -c parent-4.requirements.in
            -r parent-5.requirements.txt
            -r parent-6.requirements
            https://example.com#egg=foo
        """)

        infiles = read_infiles(self.input_dir)

        assert len(infiles) == 7
        main = self.get_main_infile(infiles)
        assert main.dependencies == [
            'foo  ==3.3.1',
            'bar[extra]',
            'baz#notacomment',
            'https://example.com#egg=foo',
        ]
        assert main.references == [
            Reference('r', InFile('parent-1.requirements.in')),
            Reference('r', InFile('parent-3.requirements.in')),
            Reference('c', InFile('parent-2.requirements.in')),
            Reference('c', InFile('parent-4.requirements.in')),
            Reference('r', InFile('parent-5.requirements.in')),
            Reference('r', InFile('parent-6.requirements.in')),
        ]

    def test_unknown_reference(self) -> None:
        self.create_file('main.in', '-r unknown.txt')

        with pytest.raises(UnknownReference, match='main.in: unknown'):
            read_infiles(self.input_dir)

    def test_conflicting_names(self) -> None:
        self.create_file('main.in')
        self.create_file('main.requirements.in')

        with pytest.raises(InputDirectoryError) as excinfo:
            read_infiles(self.input_dir)

        assert str(excinfo.value) in [
            'conflicting names: main.in, main.requirements.in',
            'conflicting names: main.requirements.in, main.in',
        ]
