import os
from pathlib import Path
import subprocess
import sys
import textwrap


def test_non_image_extract_imports_do_not_require_pillow() -> None:
    src_path = Path(__file__).resolve().parents[2] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env.get('PYTHONPATH', '')}"

    script = textwrap.dedent(
        """
        import importlib.abc
        import sys


        class BlockPillow(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "PIL" or fullname.startswith("PIL."):
                    raise ModuleNotFoundError("No module named 'PIL'")
                return None


        sys.meta_path.insert(0, BlockPillow())

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
