from pathlib import Path
from typing import Union

import pytest

from ptl.infile import InFile, Reference, ReferenceType


@pytest.mark.parametrize('ref_type', ['c', ReferenceType.CONSTRAINTS])
def test_attributes(ref_type: Union[ReferenceType, str]):
    infile = InFile('main.in')
    ref = Reference(ref_type, infile)

    assert ref.infile == infile
    assert ref.type == ReferenceType(ref_type)


def test_equal():
    infile_1 = InFile('/path/to/main.in')
    infile_2 = InFile(Path('main.in'))
    ref_1 = Reference(ReferenceType.REQUIREMENTS, infile_1)
    ref_2 = Reference('r', infile_2)

    assert ref_1 == ref_2


def test_not_equal_infile():
    infile_1 = InFile('/path/to/main.in')
    infile_2 = InFile('/path/to/base.in')
    ref_1 = Reference('r', infile_1)
    ref_2 = Reference('r', infile_2)

    assert ref_1 != ref_2


def test_not_equal_type():
    infile = InFile('main.in')
    ref_1 = Reference(ReferenceType.CONSTRAINTS, infile)
    ref_2 = Reference(ReferenceType.REQUIREMENTS, infile)

    assert ref_1 != ref_2


def test_copy_as():
    infile = InFile('main.in')
    ref = Reference(ReferenceType.CONSTRAINTS, infile)

    ref_copy = ref.copy_as(ReferenceType.REQUIREMENTS)

    assert ref_copy == Reference(ReferenceType.REQUIREMENTS, infile)