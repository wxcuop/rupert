import csv
from typing import List, Dict, Callable, Optional, Iterator


class ColumnIndex:
    """
    Class to manage column indices for a file.
    Maps column names to their respective indices.
    """

    def __init__(self, header_line: str, separator: str = ";"):
        """
        Initialize the ColumnIndex with a header line.

        :param header_line: The header line containing column names.
        :param separator: The separator used in the file.
        """
        self.columns = [col.strip() for col in header_line.split(separator)]
        self.map = {name: idx for idx, name in enumerate(self.columns)}

    def lookup(self, column_name: str, row: List[str]) -> str:
        """
        Get the value of a specific column in a row. Raises KeyError if the column doesn't exist.

        :param column_name: Name of the column to look up.
        :param row: The row of data as a list of strings.
        :return: The value of the specified column.
        """
        if column_name not in self.map:
            raise KeyError(f"Column '{column_name}' not found.")
        return row[self.map[column_name]]

    def lookup_or_default(self, column_name: str, row: List[str], default: str = "") -> str:
        """
        Get the value of a specific column in a row. Returns a default value if the column doesn't exist.

        :param column_name: Name of the column to look up.
        :param row: The row of data as a list of strings.
        :param default: Default value to return if the column doesn't exist.
        :return: The value of the specified column or the default value.
        """
        return row[self.map.get(column_name, -1)] if column_name in self.map else default

    def has_column(self, column_name: str) -> bool:
        """
        Check if a specific column exists.

        :param column_name: Name of the column to check.
        :return: True if the column exists, False otherwise.
        """
        return column_name in self.map

    def size(self) -> int:
        """
        Get the number of columns.

        :return: Number of columns.
        """
        return len(self.columns)

    def __getitem__(self, index: int) -> str:
        """
        Get the name of a column by its index.

        :param index: Index of the column.
        :return: Name of the column.
        """
        return self.columns[index]


class Row:
    """
    Class representing a single row in a file. Provides access to columns by name or index.
    """

    def __init__(self, index: ColumnIndex, data: List[str]):
        self.index = index
        self.data = data

    def extract(self, column_name: str) -> str:
        """
        Extract a value from a specific column. Raises KeyError if the column doesn't exist.

        :param column_name: Name of the column to extract from.
        :return: Value from the specified column.
        """
        return self.index.lookup(column_name, self.data)

    def get(self, column_name: str) -> str:
        """
        Extract a value from a specific column. Returns an empty string if the column doesn't exist.

        :param column_name: Name of the column to extract from.
        :return: Value from the specified column or an empty string.
        """
        return self.index.lookup_or_default(column_name, self.data)

    def __bool__(self):
        return bool(self.data)


class File:
    """
    Class to represent and parse an MIT-style file with headers and rows.
    Allows accessing rows by columns and defining custom filters or indices.
    """

    START_OF_DATA = "START-OF-DATA"
    END_OF_DATA = "END-OF-DATA"

    def __init__(self):
        self.lines = []
        self.index = None
        self.filters = []

    def initialise(self, filename: str, separator=";", with_start_end_of_data=False):
        """
        Initialize and parse a file.

        :param filename: Path to the file to parse.
        :param separator: Separator used in the file (default is ";").
        :param with_start_end_of_data: Whether to respect START-OF-DATA/END-OF-DATA markers.
        """
