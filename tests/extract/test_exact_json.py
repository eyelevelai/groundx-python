import json
from pathlib import Path

from tests.extract.exact_json import exact_json_report


VECTOR_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "extraction-boundary"
    / "contract"
    / "exact_json.vectors.json"
)


def test_exact_json_comparison_matches_shared_vectors() -> None:
    vectors = json.loads(VECTOR_PATH.read_text())

    for vector in vectors["vectors"]:
        assert exact_json_report(vector["actual"], vector["expected"]) == {
            "differences": vector["differences"],
            "first_path": (
                vector["differences"][0]["path"] if vector["differences"] else None
            ),
        }, vector["name"]
