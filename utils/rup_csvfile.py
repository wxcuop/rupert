import csv
from typing import List, Dict, Callable, Optional, Iterator


class ColumnIndex:
    """
    Manages column indices for a file by mapping column names to their respective indices.
    """

    def __init__(self, header_line: str, separator: str = ";"):
        """
        Initializes the ColumnIndex with a header line.

        :param header_line: The header line containing column names.
        :param separator: The separator used in the file (default is ";").
        """
        self.columns = [col.strip() for col in header_line.split(separator)]  # Split and trim column names
        self.map = {name: idx for idx, name in enumerate(self.columns)}  # Create a mapping from column name to index

    def lookup(self, column_name: str, row: List[str]) -> str:
        """
        Retrieves the value of a specific column in a row. Raises KeyError if the column doesn't exist.

        :param column_name: Name of the column to look up.
        :param row: The row of data as a list of strings.
        :return: The value of the specified column.
        """
        if column_name not in self.map:
            raise KeyError(f"Column '{column_name}' not found.")
        return row[self.map[column_name]]

    def lookup_or_default(self, column_name: str, row: List[str], default: str = "") -> str:
        """
        Retrieves the value of a specific column in a row. Returns a default value if the column doesn't exist.

        :param column_name: Name of the column to look up.
        :param row: The row of data as a list of strings.
        :param default: Default value to return if the column doesn't exist.
        :return: The value of the specified column or the default value.
        """
        return row[self.map.get(column_name, -1)] if column_name in self.map else default

    def has_column(self, column_name: str) -> bool:
        """
        Checks if a specific column exists.
        :param column_name: Name of the column to check.
        :return: True if the column exists, False otherwise.
        """
        return column_name in self.map

    def size(self) -> int:
        """
        Returns the number of columns.
        :return: Number of columns.
        """
        return len(self.columns)

    def __getitem__(self, index: int) -> str:
        """
        Retrieves the name of a column by its index.
        :param index: Index of the column.
        :return: Name of the column.
        """
        return self.columns[index]


class Row:
    """
    Represents a single row in a file, allowing access to columns by name or index.
    """

    def __init__(self, index: ColumnIndex, data: List[str]):
        self.index = index
        self.data = data

    def extract(self, column_name: str) -> str:
        """
        Extracts a value from a specific column. Raises KeyError if the column doesn't exist.
        :param column_name: Name of the column to extract from.
        :return: Value from the specified column.
        """
        return self.index.lookup(column_name, self.data)

    def get(self, column_name: str) -> str:
        """
        Extracts a value from a specific column. Returns an empty string if the column doesn't exist.
        :param column_name: Name of the column to extract from.
        :return: Value from the specified column or an empty string.
        """
        return self.index.lookup_or_default(column_name, self.data)

    def __bool__(self):
        """
        Returns True if the row has data, False otherwise.
        """
        return bool(self.data)


class File:
    """
    Parses and represents an MIT-style file with headers and rows.
    Supports column-based access, filtering, and indexing.
    """

    START_OF_DATA = "START-OF-DATA"
    END_OF_DATA = "END-OF-DATA"

    def __init__(self):
        self.lines = []  # Stores parsed lines as lists of column values
        self.index = None  # Column index object
        self.filters = []  # List of filtering functions

    def initialise(self, filename: str, separator=";", with_start_end_of_data=False):
        """
        Parses the file and initializes column indices.

        :param filename: Path to the file.
        :param separator: Separator used in the file.
        :param with_start_end_of_data: Whether to respect START-OF-DATA/END-OF-DATA markers.
        """
        with open(filename, newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=separator)
            lines = list(reader)

        if not lines:
            return  # Exit if the file is empty

        self.index = ColumnIndex(lines[0], separator)
        self.lines = lines[1:]  # Store data rows, excluding the header

        # Process START-OF-DATA and END-OF-DATA markers if needed
        if with_start_end_of_data:
            start_idx = next((i for i, row in enumerate(self.lines) if row[0] == self.START_OF_DATA), None)
            end_idx = next((i for i, row in enumerate(self.lines) if row[0] == self.END_OF_DATA), None)
            if start_idx is not None:
                self.lines = self.lines[start_idx + 1:]
            if end_idx is not None:
                self.lines = self.lines[:end_idx]

    def filter_rows(self, condition: Callable[[List[str]], bool]):
        """
        Applies a filter function to remove unwanted rows.
        :param condition: A function that returns True for rows to remove.
        """
        self.lines = [row for row in self.lines if not condition(row)]

    def get_rows(self) -> Iterator[Row]:
        """
        Returns an iterator over Row objects.
        """
        for line in self.lines:
            yield Row(self.index, line)

    def has_column(self, column_name: str) -> bool:
        """
        Checks if the file has a given column.
        :param column_name: Column name to check.
        :return: True if the column exists, False otherwise.
        """
        return self.index.has_column(column_name) if self.index else False

    def __bool__(self):
        """
        Returns True if the file contains data, False otherwise.
        """
        return bool(self.lines)
