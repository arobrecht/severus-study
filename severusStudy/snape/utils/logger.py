import csv
from os import path
import os
from pathlib import Path
import sys


class Logger:
    """Simple csv logging helper class."""

    header_written: bool
    append_to_file: bool
    disabled: bool
    target_folder: Path
    file_name: Path
    file_path: Path
    header: list[str]
    content: list[list[str]]

    def __init__(self, target_folder: str, file_name: str, header: list[str]):
        self.target_folder = Path(sys.argv[0]).parent / Path(target_folder)
        self.file_name = Path(file_name)
        self.file_path = self.target_folder / self.file_name
        self.header = header
        self.content = []
        self.header_written = False
        self.disabled = False
        self.append_to_file = True

        os.makedirs(self.target_folder, exist_ok=True)

        if path.exists(self.file_path):
            choice = input(
                f"{self.file_path} already exists. overwrite or append? (y/n/[a]ppend)"
            )
            if choice == "y":
                os.remove(self.file_path)
            elif choice == "a":
                self.append_to_file = True
            else:
                self.disabled = True
                print("logger disabled")

    def append(self, line: list[str]):
        self.content.append(line)

    def write_header(self, writer):
        if not self.header_written:
            if self.append_to_file:
                self.header_written = True
                return

            writer.writerow(self.header)
            self.header_written = True

    def flush(self):
        self.save()
        self.content = []

    def save(self):
        if self.disabled:
            return

        with open(self.file_path, "a", encoding="UTF8", newline="") as f:
            writer = csv.writer(f)
            self.write_header(writer)
            writer.writerows(self.content)
