import subprocess
import sys
from pathlib import Path

import pytest

from ptl.exceptions import Error

from tests.testlib import dedent


def test_error_message_from_args() -> None:
    cause = ValueError('should be ignored')

    with pytest.raises(Error, match=r'^some error$'):
        raise Error('some error') from cause


def test_error_message_from_cause_subprocess(tmp_cwd: Path) -> None:
    script = tmp_cwd / 'boom.py'
    script.write_text(dedent("""
        import sys
        sys.exit(28)
    """))

    with pytest.raises(
        Error, match=r'boom\.py returned non-zero exit status 28$',
    ):
        try:
            subprocess.check_call([sys.executable, './boom.py'])
        except subprocess.CalledProcessError as exc:
            raise Error from exc


@pytest.mark.parametrize('text', [False, True])
def test_error_message_from_cause_subprocess_with_output(
    tmp_cwd: Path, text: bool,
) -> None:
    script = tmp_cwd / 'boom.py'
    script.write_text(dedent("""
        import sys
        print('BOOM')
        sys.exit(29)
    """))

    with pytest.raises(
        Error, match=r'boom\.py returned non-zero exit status 29:\nBOOM\n$',
    ):
        try:
            subprocess.check_output([sys.executable, './boom.py'], text=text)
        except subprocess.CalledProcessError as exc:
            raise Error from exc


def test_error_message_from_cause_other() -> None:
    cause = ValueError('value error')

    with pytest.raises(Error, match=r'^value error$'):
        raise Error from cause


def test_error_message_no_cause_no_args() -> None:
    with pytest.raises(Error, match=r'^$'):
        raise Error()
