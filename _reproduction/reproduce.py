from __future__ import annotations

import html
from pathlib import Path

from tqec import BlockGraph

ROOT = Path(__file__).resolve().parent
DAE_DIR = ROOT / "inputs" / "dae"
BGS_DIR = ROOT / "inputs" / "bgs"
OUT_DIR = ROOT / "outputs"


def _gadget_name(path: Path) -> str:
    return path.stem


def _clean_out() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.iterdir():
        if old.is_file():
            old.unlink()


def _render_dae(path: Path) -> Path | None:
    name = _gadget_name(path)
    try:
        graph = BlockGraph.from_dae_file(path, graph_name=name)
        out = OUT_DIR / f"{name}.dae.html"
        graph.view_as_html(out)
        return out
    except Exception as exc:
        print(f"{name} DAE: {type(exc).__name__}: {exc}")
        return None


def _render_bgraph(path: Path) -> Path | None:
    name = _gadget_name(path)
    try:
        graph = BlockGraph.from_bgraph(path, graph_name=name)
        out = OUT_DIR / f"{name}.bgraph.html"
        graph.view_as_html(out)
        return out
    except Exception as exc:
        print(f"{name} BGRAPH: {type(exc).__name__}: {exc}")
        return None


def _write_index(outputs: list[Path]) -> None:
    links = "\n".join(
        f'<li><a href="{html.escape(path.name)}">{html.escape(path.name)}</a></li>'
        for path in outputs
    )
    (OUT_DIR / "index.html").write_text(f"<!doctype html><ul>\n{links}\n</ul>\n")


def main() -> None:
    _clean_out()
    outputs: list[Path] = []
    for path in sorted(DAE_DIR.glob("*.dae")):
        rendered = _render_dae(path)
        if rendered is not None:
            outputs.append(rendered)
    for path in sorted(BGS_DIR.glob("*.bgraph")):
        rendered = _render_bgraph(path)
        if rendered is not None:
            outputs.append(rendered)
    _write_index(outputs)
    print(f"Wrote {len(outputs)} HTML files to {OUT_DIR}")


if __name__ == "__main__":
    main()
