import csv
import logging
from pathlib import Path

class CsvLoader:
    """
    A class to load CSV files, typically at Start-of-Day (SOD).
    """

    def __init__(self):
        self.line_count = 0

    def process_header(self, header: str):
        """
        Processes the header line. Default behavior is to skip it.

        :param header: The header line from the CSV.
        """
        logging.debug("Header line skipped")

    def is_ignored(self, line: str) -> bool:
        """
        Checks whether a line should be ignored (empty or starts with '##').

        :param line: The line to check.
        :return: True if the line should be ignored, otherwise False.
        """
        line = line.strip()
        return line.startswith("##") or not line

    def load(self, file_path: str) -> bool:
        """
        Loads a CSV file and processes its content.

        :param file_path: Path to the CSV file.
        :return: True if the file was loaded successfully, False otherwise.
        """
        logging.info(f"Loading started for {file_path}")

        file_path = Path(file_path)
        if not file_path.exists():
            logging.error(f"File doesn't exist: {file_path}")
            return False

        try:
            with file_path.open("r", encoding="utf-8") as file:
                reader = csv.reader(file)
                self.line_count = 0
                header_processed = False

                for line in reader:
                    self.line_count += 1
                    try:
                        line_content = ",".join(line).strip()  # Reconstruct if CSV parsing splits it

                        if self.is_ignored(line_content):
                            continue

                        if header_processed:
                            self.process_content(line_content)
                        else:
                            self.process_header(line_content)
                            header_processed = True
                    except Exception as e:
                        logging.error(f"Exception happened while reading file {file_path} at line {self.line_count}: {line}")
                        logging.error(f"Exception: {e}")
                        return False

            logging.info(f"File loading finished. Total lines processed: {self.line_count}")
            return True
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            return False

    def process_content(self, line: str):
        """
        Placeholder for processing content. Should be overridden in subclasses.

        :param line: The content line from the CSV.
        """
        raise NotImplementedError("process_content() must be implemented by subclasses")

# Example Usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loader = CsvLoader()
    loader.load("example.csv")
