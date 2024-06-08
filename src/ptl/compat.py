import enum
import sys


if sys.version_info >= (3, 11):
    StrEnum = enum.StrEnum
else:
    class StrEnum(str, enum.Enum):
        pass
