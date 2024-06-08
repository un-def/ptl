import enum
import sys


if sys.version_info >= (3, 11):
    StrEnum = enum.StrEnum
else:
    StrEnum = type('StrEnum', (str, enum.Enum), {})
