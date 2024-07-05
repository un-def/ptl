import pytest

from ptl.infile import CircularReference, InFile, Reference, sort_infiles


def test_ok() -> None:
    child_1 = InFile('child-1.in')
    child_2 = InFile('child-2.in')
    child_3 = InFile('child-3.in')
    parent_1 = InFile('parent-1.in')
    parent_2 = InFile('parent-2.in')
    parent_3 = InFile('parent-3.in')
    grandparent_1 = InFile('grandparent-1.in')
    grandparent_2 = InFile('grandparent-2.in')
    child_1.add_reference(Reference('c', parent_1))
    child_1.add_reference(Reference('c', parent_2))
    child_2.add_reference(Reference('c', parent_3))
    parent_1.add_reference(Reference('c', grandparent_1))
    parent_2.add_reference(Reference('c', grandparent_2))
    infiles = [
        child_1, child_2, child_3,
        parent_1, parent_2, parent_3,
        grandparent_1, grandparent_2,
    ]

    sorted_infiles = sort_infiles(infiles)

    assert sorted_infiles == [
        child_3, grandparent_1, grandparent_2, parent_3,
        child_2, parent_1, parent_2, child_1,
    ]


def test_circular_reference() -> None:
    child = InFile('child.in')
    parent = InFile('parent.in')
    grandparent_1 = InFile('grandparent-1.in')
    grandparent_2 = InFile('grandparent-2.in')
    child.add_reference(Reference('r', parent))
    parent.add_reference(Reference('c', grandparent_1))
    parent.add_reference(Reference('c', grandparent_2))
    grandparent_1.add_reference(Reference('c', child))

    with pytest.raises(CircularReference) as excinfo:
        sort_infiles([child, parent, grandparent_1])

    assert set(excinfo.value.infiles) == {child, parent, grandparent_1}
    assert 'child.in' in str(excinfo.value)
