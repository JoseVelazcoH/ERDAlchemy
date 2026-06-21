"""Tests for the CLI argument layer (argparse validation and exit paths)."""

from __future__ import annotations

import pytest

from sqlalchemy_erd.cli import main


class TestCliArgumentValidation:
    def test_missing_target_exits(self):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code != 0

    def test_invalid_format_exits(self):
        with pytest.raises(SystemExit) as exc:
            main(["models:Base", "--format", "bogus"])
        assert exc.value.code != 0

    def test_invalid_layout_exits(self):
        with pytest.raises(SystemExit) as exc:
            main(["models:Base", "--layout", "bogus"])
        assert exc.value.code != 0
