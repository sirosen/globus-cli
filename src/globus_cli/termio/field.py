from __future__ import annotations

import typing as t

from . import formatters


class Field:
    """A field which will be shown in record or table output.
    When fields are provided as tuples, they are converted into this.

    :param name: the displayed name for the record field or the column
        name for table output
    :param key: a jmespath expression for indexing into print data
    :param wrap_enabled: in record output, is this field allowed to wrap
    :param conditional: a callable which takes the data and returns true if the field
        should be displayed, false if it should be skipped/omitted (applies to record
        output only)
    """

    def __init__(
        self,
        name: str,
        key: str,
        *,
        wrap_enabled: bool = False,
        conditional: t.Callable[[t.Any], bool] | None = None,
        formatter: formatters.FieldFormatter = formatters.Str,
    ):
        self.name = name
        self.key = key
        self.wrap_enabled = wrap_enabled
        self.conditional = conditional
        self.formatter = formatter

    def get_value(self, data: t.Any) -> t.Any:
        import jmespath

        return jmespath.search(self.key, data)

    def format(self, value: t.Any) -> str:
        return self.formatter.format(value)

    def is_present(self, data: t.Any) -> bool:
        if self.conditional is None:
            return True
        return self.conditional(data)

    def __call__(self, data: t.Any) -> str:
        return self.format(self.get_value(data))


class FilteredField(Field):
    """
    A variant of Field which auto-hides in record-output if the key used is not present
    in the data.
    """

    def __init__(
        self,
        name: str,
        key: str,
        *,
        wrap_enabled: bool = False,
        formatter: formatters.FieldFormatter = formatters.Str,
    ):
        self.name = name
        self.key = key
        self.wrap_enabled = wrap_enabled
        self.conditional = self._conditional_check
        self.formatter = formatter

    def _conditional_check(self, data: t.Any) -> bool:
        return self.get_value(data) is not None
