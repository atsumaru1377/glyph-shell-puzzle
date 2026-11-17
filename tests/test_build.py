import sys

import pytest

from glyphshell import build
from glyphshell.layout import save_layout


def test_接触が足りる字が1つも残らなければ理由を示して止まる(tmp_path, monkeypatch):
    save_layout(tmp_path / "layout.npz", [])
    monkeypatch.setattr(sys, "argv", ["build", "--out", str(tmp_path), "--reuse"])
    with pytest.raises(SystemExit, match="接触が 3 か所に届く字が1つも残らなかった"):
        build.main()
