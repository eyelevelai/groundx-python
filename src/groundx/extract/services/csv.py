import csv, typing
from pathlib import Path


def append_row(
    csv_path: Path,
    headers: typing.List[str],
    row: typing.Dict[str, str],
) -> None:
    with csv_path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writerow(row)


def extraction_row(
    record: typing.Mapping[str, typing.Any], keys_in_order: typing.Sequence[str]
) -> typing.List[typing.Any]:
    return [record.get(k, "") for k in keys_in_order]


def find_rows(
    query: typing.Dict[str, str],
    csv_path: str,
) -> typing.List[typing.Dict[str, str]]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        rows: typing.List[typing.Dict[str, str]] = []
        for row in reader:
            matches: typing.List[str] = []
            for k, v in query.items():
                if str(row.get(k)) == str(v):
                    matches.append(k)

            if len(matches) == len(query):
                rows.append(row)

        return rows


def load_row(
    key: str,
    match: typing.List[str],
    csv_path: typing.Optional[Path] = None,
    rows: typing.Optional[typing.List[typing.Dict[str, str]]] = None,
) -> typing.Optional[typing.Dict[str, str]]:
    if csv_path is None and rows is None:
        raise Exception("csv_path and rows are None")

    if rows is None and csv_path:
        rows = load_rows(csv_path)

    if not rows:
        raise Exception("rows are None")

    return next((r for r in rows if r.get(key) in match), None)


def load_rows(csv_path: Path) -> typing.List[typing.Dict[str, str]]:
    rows: typing.List[typing.Dict[str, str]] = []
    with csv_path.open("r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)

    return rows


def save_rows(
    csv_path: Path, headers: typing.List[str], rows: typing.List[typing.Dict[str, str]]
) -> None:
    with csv_path.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
