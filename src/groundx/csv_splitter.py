import csv, math, os, tempfile, typing
from pathlib import Path


class CSVSplitter:
    def __init__(self, filepath, delimiter=','):
        self.filepath = filepath
        self.delimiter = delimiter
        self.filename = os.path.basename(filepath)
        self.file_size = os.path.getsize(filepath)
        self.rows_count = self.get_row_count()

    def get_row_count(self):
        with open(self.filepath, "r", newline="", encoding="utf-8") as csvfile:
            return sum(1 for _ in csvfile) - 1

    def determine_splits(self):
        row_mod = int(self.rows_count / 1000) + 1
        file_mod = int(self.file_size / 1024 / 1024) + 1

        return max(row_mod, file_mod)

    def split(self):
        splits = self.determine_splits()
        if splits < 2:
            return [Path(self.filepath)]

        rows_per_file = math.ceil(self.rows_count / splits)

        split_files: typing.List[Path] = []
        with open(self.filepath, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.delimiter)
            headers = next(reader)

            temp_dir = tempfile.mkdtemp()

            current_file_number = 1
            current_row = 0
            current_writer = None
            current_output_file = None

            for row in reader:
                if current_row % rows_per_file == 0:
                    if current_output_file:
                        current_output_file.close()
                    output_file_path = os.path.join(
                        temp_dir,
                        f"{os.path.splitext(self.filename)[0]}_{current_file_number}.csv",
                    )
                    split_files.append(Path(output_file_path))
                    current_output_file = open(
                        output_file_path, "w", newline="", encoding="utf-8"
                    )
                    current_writer = csv.writer(current_output_file, delimiter=self.delimiter)
                    current_writer.writerow(headers)
                    current_file_number += 1

                current_writer.writerow(row)
                current_row += 1

            if current_output_file:
                current_output_file.close()

        return split_files
