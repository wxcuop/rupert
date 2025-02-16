import csv
import logging

class MappingLoader:
    def __init__(self, mapping: dict):
        self.mapping = mapping

    def process_content(self, content: str):
        row = content.split(',')
        if len(row) != 2:
            logging.error(f"Invalid mapping entry {content} - must contain exactly 2 columns")
        elif row[0] not in self.mapping:
            self.mapping[row[0]] = row[1]
            logging.debug(f"Added mapping from {row[0]} to {self.mapping[row[0]]}")

    def load_from_csv(self, file_path: str):
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.process_content(','.join(row))
