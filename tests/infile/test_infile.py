from pathlib import Path
from typing import Dict, Union

import pytest

from ptl.exceptions import InFileNameError
from ptl.infile import InFile, Reference, ReferenceType, ReferenceTypeOrLiteral


@pytest.mark.parametrize(['name_or_path', 'expected_message'], [
    ('base.IN', 'base.IN'),
    ('./.in', '.in'),
    (Path('/path/to/base.notin'), 'base.notin'),
])
def test_name_error_wrong_suffix(
    name_or_path: Union[Path, str], expected_message: str,
) -> None:
    with pytest.raises(InFileNameError) as excinfo:
        InFile(name_or_path)

    assert str(excinfo.value) == expected_message


@pytest.mark.parametrize('name_or_path', [
    'base.in', './base.in', Path('/path/to/base.in')])
def test_attributes_no_suffix(name_or_path: Union[Path, str]) -> None:
    infile = InFile(name_or_path)

    assert infile.stem == 'base'
    assert infile.original_name == 'base.in'
    assert infile.generated_name == 'base.ptl.in'
    assert infile.output_name == 'base.txt'


@pytest.mark.parametrize('name_or_path', [
    'base.requirements.in',
    './base.requirements.in',
    Path('/path/to/base.requirements.in'),
])
def test_attributes_with_suffix(name_or_path: Union[Path, str]) -> None:
    infile = InFile(name_or_path)

    assert infile.stem == 'base'
    assert infile.original_name == 'base.requirements.in'
    assert infile.generated_name == 'base.ptl.requirements.in'
    assert infile.output_name == 'base.requirements.txt'


@pytest.mark.parametrize('path', ['test.in', Path('/path/to/test.in')])
def test_equal_no_suffix(path: Union[Path, str]) -> None:
    infile = InFile(path)

    assert infile == InFile('./test.in')


@pytest.mark.parametrize('path', [
    'test.requirements.in', Path('/path/to/test.requirements.in')])
def test_equal_with_suffix(path: Union[Path, str]) -> None:
    infile = InFile(path)

    assert infile == InFile('./test.requirements.in')


@pytest.mark.parametrize('path', [
    Path('/path/to/Test.in'), 'test.requirements.in'])
def test_not_equal(path: Union[Path, str]) -> None:
    infile = InFile(path)

    assert infile != InFile('./test.in')


def test_add_dependency() -> None:
    infile = InFile('test.in')

    infile.add_dependency('pytest <10\n')
    infile.add_dependency('   tox')
    infile.add_dependency('https://example.com/dep.zip#egg=name')

    assert infile.dependencies == [
        'pytest <10',
        'tox',
        'https://example.com/dep.zip#egg=name',
    ]


def test_add_reference() -> None:
    infile = InFile('test.in')
    ref_1 = Reference('c', InFile('dep-1.in'))
    ref_2 = Reference('r', InFile('dep-2.in'))

    infile.add_reference(ref_1)
    infile.add_reference(ref_2)

    assert infile.references == [ref_1, ref_2]


def build_ref_tree(infile: InFile) -> Dict[str, Reference]:
    """
    grand-1-1      grand-1-2  grand-2-1       grand-2-2
        |___r___     _c_|       |_r_   ____c____|
                |   |               | |
                parent-1        parent-2
                    |_c_    ___r___|
                        |  |
                        infile
    """
    grand_1_1_req = Reference('r', InFile('grand-1-1.in'))
    grand_1_2_constr = Reference('c', InFile('grand-1-2.in'))
    parent_1 = InFile('parent-1.in')
    parent_1.add_reference(grand_1_1_req)
    parent_1.add_reference(grand_1_2_constr)
    grand_2_1_req = Reference('r', InFile('grand-2-1.in'))
    grand_2_2_constr = Reference('c', InFile('grand-2-2.in'))
    parent_2 = InFile('parent-2.in')
    parent_2.add_reference(grand_2_1_req)
    parent_2.add_reference(grand_2_2_constr)
    parent_1_constr = Reference('c', parent_1)
    parent_2_req = Reference('r', parent_2)
    infile.add_reference(parent_1_constr)
    infile.add_reference(parent_2_req)
    return {
        'grand-1-1': grand_1_1_req,
        'grand-1-2': grand_1_2_constr,
        'grand-2-1': grand_2_1_req,
        'grand-2-2': grand_2_2_constr,
        'parent-1': parent_1_constr,
        'parent-2': parent_2_req,
    }


def build_infile_with_refs() -> InFile:
    """
    # main.in
    pytest <7
    -c parent-1.in
    -r parent-2.in
    tox==4.15.0
    """
    infile = InFile('main.in')
    infile.add_dependency('pytest <7')
    build_ref_tree(infile)
    infile.add_dependency('tox==4.15.0')
    return infile


def test_iterate_references_non_recursive() -> None:
    infile = InFile('main.in')
    refs = build_ref_tree(infile)

    references = list(infile.iterate_references(recursive=False))

    assert references == [
        refs['parent-1'].copy_as('c'),
        refs['parent-2'].copy_as('r'),
    ]


@pytest.mark.parametrize('as_', ['r', ReferenceType.CONSTRAINTS])
def test_iterate_references_non_recursive_as(
    as_: ReferenceTypeOrLiteral,
) -> None:
    infile = InFile('main.in')
    refs = build_ref_tree(infile)

    references = list(infile.iterate_references(recursive=False, as_=as_))

    assert references == [
        refs['parent-1'].copy_as(as_),
        refs['parent-2'].copy_as(as_),
    ]


def test_iterate_references_recursive() -> None:
    infile = InFile('main.in')
    refs = build_ref_tree(infile)

    references = list(infile.iterate_references(recursive=True))

    assert references == [
        refs['parent-1'].copy_as('c'),
        refs['grand-1-1'].copy_as('c'),
        refs['grand-1-2'].copy_as('c'),
        refs['parent-2'].copy_as('r'),
        refs['grand-2-1'].copy_as('r'),
        refs['grand-2-2'].copy_as('c'),
    ]


@pytest.mark.parametrize('as_', [ReferenceType.REQUIREMENTS, 'c'])
def test_iterate_references_recursive_as(as_: ReferenceTypeOrLiteral) -> None:
    infile = InFile('main.in')
    refs = build_ref_tree(infile)

    references = list(infile.iterate_references(recursive=True, as_=as_))

    assert references == [
        refs['parent-1'].copy_as(as_),
        refs['grand-1-1'].copy_as(as_),
        refs['grand-1-2'].copy_as(as_),
        refs['parent-2'].copy_as(as_),
        refs['grand-2-1'].copy_as(as_),
        refs['grand-2-2'].copy_as(as_),
    ]


def test_render() -> None:
    infile = build_infile_with_refs()

    rendered = infile.render()

    assert rendered == (
        '-c parent-1.txt\n'
        '-c grand-1-1.txt\n'
        '-c grand-1-2.txt\n'
        '-r parent-2.txt\n'
        '-r grand-2-1.txt\n'
        '-c grand-2-2.txt\n'
        'pytest <7\n'
        'tox==4.15.0\n'
    )


def test_render_as_requirements() -> None:
    infile = build_infile_with_refs()

    rendered = infile.render(references_as=ReferenceType.REQUIREMENTS)

    assert rendered == (
        '-r parent-1.txt\n'
        '-r grand-1-1.txt\n'
        '-r grand-1-2.txt\n'
        '-r parent-2.txt\n'
        '-r grand-2-1.txt\n'
        '-r grand-2-2.txt\n'
        'pytest <7\n'
        'tox==4.15.0\n'
    )


def test_render_as_constraints() -> None:
    infile = build_infile_with_refs()

    rendered = infile.render(references_as=ReferenceType.CONSTRAINTS)

    assert rendered == (
        '-c parent-1.txt\n'
        '-c grand-1-1.txt\n'
        '-c grand-1-2.txt\n'
        '-c parent-2.txt\n'
        '-c grand-2-1.txt\n'
        '-c grand-2-2.txt\n'
        'pytest <7\n'
        'tox==4.15.0\n'
    )


def test_write_to(input_dir: Path) -> None:
    infile = build_infile_with_refs()
    infile_path = input_dir / 'main.ptl.in'

    infile.write_to(input_dir, references_as=ReferenceType.CONSTRAINTS)

    assert infile_path.exists()
    assert infile_path.read_text() == (
        '-c parent-1.txt\n'
        '-c grand-1-1.txt\n'
        '-c grand-1-2.txt\n'
        '-c parent-2.txt\n'
        '-c grand-2-1.txt\n'
        '-c grand-2-2.txt\n'
        'pytest <7\n'
        'tox==4.15.0\n'
    )


def test_temporarily_write_to(input_dir: Path) -> None:
    infile = build_infile_with_refs()

    with infile.temporarily_write_to(input_dir) as infile_path:
        assert infile_path == input_dir / 'main.ptl.in'
        assert infile_path.exists()
        assert infile_path.read_text() == (
            '-c parent-1.txt\n'
            '-c grand-1-1.txt\n'
            '-c grand-1-2.txt\n'
            '-r parent-2.txt\n'
            '-r grand-2-1.txt\n'
            '-c grand-2-2.txt\n'
            'pytest <7\n'
            'tox==4.15.0\n'
        )
    assert not infile_path.exists()
