from pathlib import Path
from typing import Dict

import pytest

from ptl.infile import InFile, Reference, ReferenceType, filter_infiles
from ptl.layer import Layer

from tests.testlib import InFileTestSuiteBase


class TestSuite(InFileTestSuiteBase):
    infiles: Dict[str, InFile]
    layers: Dict[str, Layer]

    @pytest.fixture(autouse=True)
    def setup(self, base_setup: None) -> None:
        """
        dev

        main ---r---> parent-1 ----r----> grand-1-1
         |              |
         |              +----------c----> grand-1-2
         |
         +------c---> parent-2 ----c----> grand-2-1
                        |
                        +----------r----> grand-2-2
        """
        dev = InFile('dev.in')
        main = InFile('main.in')
        parent_1 = InFile('parent-1.in')
        parent_2 = InFile('parent-2.in')
        grand_1_1 = InFile('grand-1-1.in')
        grand_1_2 = InFile('grand-1-2.in')
        grand_2_1 = InFile('grand-2-1.in')
        grand_2_2 = InFile('grand-2-2.in')
        main.add_reference(Reference('r', parent_1))
        parent_1.add_reference(Reference('r', grand_1_1))
        parent_1.add_reference(Reference('c', grand_1_2))
        main.add_reference(Reference('c', parent_2))
        parent_2.add_reference(Reference('c', grand_2_1))
        parent_2.add_reference(Reference('r', grand_2_2))
        infiles: Dict[str, InFile] = {
            'dev': dev,
            'main': main,
            'parent-1': parent_1,
            'parent-2': parent_2,
            'grand-1-1': grand_1_1,
            'grand-1-2': grand_1_2,
            'grand-2-1': grand_2_1,
            'grand-2-2': grand_2_2,
        }
        for infile in infiles.values():
            self.create_file(infile.original_name)
        self.infiles = infiles
        self.layers = {
            stem: Layer(self.input_dir / infile.original_name)
            for stem, infile in infiles.items()
        }

    def test_not_include_parents(self) -> None:
        layers = [
            self.layers['grand-1-2'], self.layers['main'], self.layers['dev']]

        infiles = filter_infiles(
            self.infiles.values(), layers, include_parent_layers=False)

        assert infiles == [
            self.infiles['dev'], self.infiles['main'],
            self.infiles['grand-1-2'],
        ]

    def test_include_parents_all(self) -> None:
        layers = [self.layers['grand-1-2'], self.layers['main']]

        infiles = filter_infiles(
            self.infiles.values(), layers, include_parent_layers=True)

        assert infiles == [
            self.infiles['main'],
            self.infiles['parent-1'], self.infiles['parent-2'],
            self.infiles['grand-1-1'], self.infiles['grand-1-2'],
            self.infiles['grand-2-1'], self.infiles['grand-2-2'],
        ]

    def test_include_parents_only_requirements(self) -> None:
        layers = [self.layers['parent-2'], self.layers['main']]

        infiles = filter_infiles(
            self.infiles.values(), layers,
            include_parent_layers=ReferenceType.REQUIREMENTS,
        )

        assert infiles == [
            self.infiles['main'],
            self.infiles['parent-1'], self.infiles['parent-2'],
            self.infiles['grand-1-1'], self.infiles['grand-2-2'],
        ]

    def test_only_layer_stem_matters(self, tmp_path: Path) -> None:
        # currently we don't check layer path, type, etc.,
        # we only use its stem to filter infiles
        self.create_file(tmp_path / 'dev.requirements.txt')
        layer = Layer(tmp_path / 'dev.requirements.txt')

        infiles = filter_infiles(self.infiles.values(), [layer])

        assert infiles == [self.infiles['dev']]
