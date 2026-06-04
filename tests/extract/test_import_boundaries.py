import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_non_optional_extract_imports_do_not_require_image_or_google_deps() -> None:
    src_path = Path(__file__).resolve().parents[2] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

    script = textwrap.dedent(
        """
        import importlib.abc
        import sys


        class BlockOptionalDeps(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                blocked_roots = ("PIL", "google", "googleapiclient", "gspread")
                if fullname in blocked_roots or fullname.startswith(
                    tuple(f"{root}." for root in blocked_roots)
                ):
                    root = fullname.split(".", 1)[0]
                    raise ModuleNotFoundError(f"No module named '{root}'")
                return None


        sys.meta_path.insert(0, BlockOptionalDeps())

        from groundx.extract import (
            FinalFieldPath,
            PreparedExtractionYaml,
            prepare_extraction_yaml,
        )
        from groundx.extract.classes.field import ExtractedField
        from groundx.extract.classes.group import Group
        from groundx.extract.classes import ExtractedField as NamespaceField
        from groundx.extract.classes import Group as NamespaceGroup
        from groundx.extract.prompt.source import Source

        assert FinalFieldPath
        assert PreparedExtractionYaml
        assert prepare_extraction_yaml
        assert ExtractedField
        assert Group
        assert NamespaceField is ExtractedField
        assert NamespaceGroup is Group
        assert Source
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
