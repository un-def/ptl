import logging

import pytest

from ptl.infile import InFile, InputDirectoryError, ReferenceType, get_infiles
from ptl.layer import Layer

from tests.testlib import InFileTestSuiteBase


class TestSuite(InFileTestSuiteBase):

    def prepare_files(self) -> None:
        self.create_file('dev.in')
        self.create_file('main.in', """
            -c parent-1.txt
            -r parent-2
            foo
        """)
        self.create_file('parent-1.in', """
            -r grandparent-1
            bar
            baz
        """)
        self.create_file('grandparent-1.in', """
            qux
        """)
        self.create_file('parent-2.in', """
            -r grandparent-2
        """)
        self.create_file('grandparent-2.in')

    def test_no_filtering(self) -> None:
        self.prepare_files()

        infiles = get_infiles(self.input_dir)

        assert infiles == [
            InFile('dev.in'),   # 0
            InFile('grandparent-1.in'),   # 1
            InFile('grandparent-2.in'),   # 2
            InFile('parent-1.in'),   # 3
            InFile('parent-2.in'),   # 4
            InFile('main.in'),   # 5
        ]
        assert infiles[1].render() == (
            'qux\n'
        )
        assert infiles[3].render() == (
            '-r grandparent-1.txt\n'
            'bar\n'
            'baz\n'
        )
        assert infiles[5].render() == (
            '-c parent-1.txt\n'
            '-c grandparent-1.txt\n'
            '-r parent-2.txt\n'
            '-r grandparent-2.txt\n'
            'foo\n'
        )

    def test_filtering_no_parents(self) -> None:
        self.prepare_files()
        layer = Layer(self.input_dir / 'main.in')

        infiles = get_infiles(
            self.input_dir, layers=[layer], include_parent_layers=False)

        assert infiles == [InFile('main.in')]

    def test_filtering_all_parents(self) -> None:
        self.prepare_files()
        layer = Layer(self.input_dir / 'main.in')

        infiles = get_infiles(
            self.input_dir, layers=[layer], include_parent_layers=True)

        assert infiles == [
            InFile('grandparent-1.in'),
            InFile('grandparent-2.in'),
            InFile('parent-1.in'),
            InFile('parent-2.in'),
            InFile('main.in'),
        ]

    def test_filtering_only_requirements_parents(self) -> None:
        self.prepare_files()
        layer = Layer(self.input_dir / 'main.in')

        infiles = get_infiles(
            self.input_dir, layers=[layer],
            include_parent_layers=ReferenceType.REQUIREMENTS,
        )

        assert infiles == [
            InFile('grandparent-2.in'),
            InFile('parent-2.in'),
            InFile('main.in'),
        ]

    def test_no_infiles(self) -> None:
        with pytest.raises(InputDirectoryError, match=r'no \*\.in files'):
            get_infiles(self.input_dir)

    def test_parameters_consistency_check(
        self, caplog: pytest.LogCaptureFixture,
    ) -> None:
        self.prepare_files()
        caplog.set_level(logging.WARNING)

        infiles = get_infiles(self.input_dir, include_parent_layers=False)

        assert caplog.messages == [
            'include_parent_layers = False ignored when no layers passed']
        assert infiles == [
            InFile('dev.in'),
            InFile('grandparent-1.in'),
            InFile('grandparent-2.in'),
            InFile('parent-1.in'),
            InFile('parent-2.in'),
            InFile('main.in'),
        ]
