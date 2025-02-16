import os
import time
from typing import Callable, List

class DynamicFileReader:
    def __init__(
        self,
        name: str,
        filename: str,
        line_callback: Callable[[str], None] = None,
        token_callback: Callable[[str, List[str]], None] = None,
        skip_blank_lines_and_comments: bool = False,
        separator: str = None,
    ):
        self.name = name
        self.filename = filename
        self.line_callback = line_callback
        self.token_callback = token_callback
        self.skip_blank_lines_and_comments = skip_blank_lines_and_comments
        self.separator = separator
        self.last_write_time = None

    def read_and_process(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                for line in f:
                    trimmed_line = line.strip()
                    
                    if self.skip_blank_lines_and_comments and self.is_blank_line(trimmed_line):
                        continue
                    
                    print(f"[{self.name}]. Trimmed filtered line [{trimmed_line}]")
                    
                    if self.line_callback:
                        self.line_callback(line.rstrip("\n"))
                    elif self.token_callback and self.separator:
                        tokens = trimmed_line.split(self.separator)
                        self.token_callback(line.rstrip("\n"), tokens)
        except Exception as e:
            raise RuntimeError(f"[{self.name}]. File read error: {e}")

    def has_file_write_time_changed(self) -> bool:
        try:
            current_write_time = os.path.getmtime(self.filename)
            if self.last_write_time != current_write_time:
                self.last_write_time = current_write_time
                print(f"[{self.name}]. last_write_time has changed to [{time.ctime(self.last_write_time)}]")
                return True
        except Exception as e:
            raise RuntimeError(f"[{self.name}]. Cannot read file [{self.filename}]: {e}")
        return False

    @staticmethod
    def is_blank_line(line: str) -> bool:
        return not line or line.startswith("#")
