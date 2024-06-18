import subprocess
from pathlib import Path
from typing import Optional


class Error(Exception):

    def get_error_message_from_cause(self) -> Optional[str]:
        if not (cause := self.__cause__):
            return None
        if isinstance(cause, subprocess.CalledProcessError):
            cmd = cause.cmd
            if not isinstance(cmd, (str, Path)):
                cmd = ' '.join(map(str, cmd))
            msg = f'{cmd} returned non-zero exit status {cause.returncode}'
            if output := cause.output:
                if isinstance(output, bytes):
                    output = output.decode()
                msg = f'{msg}:\n{output}'
            return msg
        return str(cause)

    def __str__(self) -> str:
        if self.args:
            return super().__str__()
        return self.get_error_message_from_cause() or ''
