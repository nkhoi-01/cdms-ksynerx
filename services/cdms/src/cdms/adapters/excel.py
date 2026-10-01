"""Excel workbook adapter that yields source rows without business decisions."""

from collections.abc import Iterable


class ExcelProductReader:
    def read_rows(self, content: bytes) -> Iterable[dict]:
        # TODO: Enforce file-size, sheet, header, row, and cell-type constraints.
        # TODO: Report row-specific validation failures without hiding valid rows.
        raise NotImplementedError

