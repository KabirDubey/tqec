from __future__ import annotations

import argparse
import copy
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path
from typing import cast

import collada
import numpy as np

from tqec import BlockGraph
from tqec.interop.collada.read_write import _CORRELATION_SUFFIX

ROOT = Path(__file__).resolve().parent


def _block_nodes(sketchup: collada.scene.Node) -> list[collada.scene.Node]:
    nodes = []
    for node in sketchup.children:
        if not (
            isinstance(node, collada.scene.Node)
            and node.matrix is not None
            and node.children
            and isinstance(node.children[0], collada.scene.NodeNode)
        ):
            continue
        library_node = cast(collada.scene.NodeNode, node.children[0]).node
        if not library_node.name.endswith(_CORRELATION_SUFFIX):
            nodes.append(node)
    return nodes


def _world_bounds(node: collada.scene.Node) -> tuple[np.ndarray, np.ndarray]:
    library_node = cast(collada.scene.NodeNode, node.children[0]).node
    points = []
    for child in library_node.children:
        geometry = getattr(child, "geometry", None)
        if geometry is None:
            continue
        for primitive in geometry.primitives:
            vertices = getattr(primitive, "vertex", None)
            if vertices is not None:
                vertices = np.asarray(vertices)
                homogeneous = np.hstack([vertices, np.ones((len(vertices), 1))])
                points.append((node.matrix @ homogeneous.T).T[:, :3])
    if not points:
        raise ValueError(f"Could not read geometry vertices for DAE node {node.id}.")
    all_points = np.vstack(points)
    return all_points.min(axis=0), all_points.max(axis=0)


def _touches(a: tuple[np.ndarray, np.ndarray], b: tuple[np.ndarray, np.ndarray]) -> bool:
    # TQEC DAE blocks are adjacent when their rendered geometry touches.
    eps = 1e-6
    return bool(np.all(a[1] + eps >= b[0]) and np.all(b[1] + eps >= a[0]))


def _components(nodes: list[collada.scene.Node]) -> list[set[str]]:
    bounds = [_world_bounds(node) for node in nodes]
    adjacency = [set() for _ in nodes]
    for i, a in enumerate(bounds):
        for j in range(i + 1, len(bounds)):
            if _touches(a, bounds[j]):
                adjacency[i].add(j)
                adjacency[j].add(i)

    unseen = set(range(len(nodes)))
    components = []
    while unseen:
        start = unseen.pop()
        queue = deque([start])
        component = {nodes[start].id}
        while queue:
            index = queue.popleft()
            for other in adjacency[index]:
                if other in unseen:
                    unseen.remove(other)
                    queue.append(other)
                    component.add(nodes[other].id)
        components.append(component)
    return components


def _source_ordered_components(
    components: list[set[str]], nodes: list[collada.scene.Node]
) -> list[set[str]]:
    node_order = {node.id: index for index, node in enumerate(nodes)}
    return sorted(components, key=lambda component: min(node_order[node_id] for node_id in component))


def split_dae(source: Path, dae_dir: Path, clean: bool) -> list[Path]:
    dae_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        for old in dae_dir.glob("*.dae"):
            old.unlink()

    mesh = collada.Collada(str(source))
    if mesh.scene is None or len(mesh.scene.nodes) != 1:
        raise ValueError("Expected one Collada scene node.")
    nodes = _block_nodes(mesh.scene.nodes[0])
    components = _source_ordered_components(_components(nodes), nodes)

    tree = ET.parse(source)
    root = tree.getroot()
    ns = {"c": root.tag.split("}")[0].strip("{")}
    sketchup = root.find(".//c:library_visual_scenes/c:visual_scene/c:node[@name='SketchUp']", ns)
    if sketchup is None:
        raise ValueError("Could not find SketchUp visual scene node.")
    original_children = list(sketchup)

    outputs = []
    for index, component in enumerate(components, start=1):
        new_root = copy.deepcopy(root)
        new_sketchup = new_root.find(
            ".//c:library_visual_scenes/c:visual_scene/c:node[@name='SketchUp']", ns
        )
        assert new_sketchup is not None
        for child in list(new_sketchup):
            new_sketchup.remove(child)
        for child in original_children:
            child_id = child.attrib.get("id")
            if child_id is None or child_id in component:
                new_sketchup.append(copy.deepcopy(child))
        out = dae_dir / f"g{index:02}.dae"
        ET.ElementTree(new_root).write(out, encoding="utf-8", xml_declaration=True)
        outputs.append(out)
    return outputs


def convert_bgraphs(dae_files: list[Path], bgs_dir: Path, clean: bool) -> None:
    bgs_dir.mkdir(parents=True, exist_ok=True)
    if clean:
        for old in bgs_dir.glob("*.bgraph"):
            old.unlink()
    for dae in dae_files:
        try:
            graph = BlockGraph.from_dae_file(dae, graph_name=dae.stem)
            graph.to_bgraph(bgs_dir / f"{dae.stem}.bgraph", graph_name=dae.stem)
        except Exception as exc:
            print(f"{dae.stem} BGRAPH: {type(exc).__name__}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a monolithic TQEC DAE into component DAE files.")
    parser.add_argument("--input", type=Path, default=ROOT / "uTesting.dae")
    parser.add_argument("--dae-dir", type=Path, default=ROOT / "dae")
    parser.add_argument("--bgs-dir", type=Path, default=ROOT / "bgs")
    parser.add_argument("--write", choices=["dae", "bgraph", "both"], default="both")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    dae_files = split_dae(args.input, args.dae_dir, args.clean)
    print(f"Wrote {len(dae_files)} split DAE files to {args.dae_dir}")
    if args.write in {"bgraph", "both"}:
        convert_bgraphs(dae_files, args.bgs_dir, args.clean)
        print(f"Converted split DAE files to BGRAPH where strict import succeeded.")


if __name__ == "__main__":
    main()
