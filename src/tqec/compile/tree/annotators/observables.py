from __future__ import annotations

from typing import TYPE_CHECKING

from tqec.circuit.measurement_map import MeasurementRecordsMap
from tqec.compile.blocks.layers.atomic.layout import LayoutLayer
from tqec.compile.blocks.layers.composed.sequenced import SequencedLayers
from tqec.compile.observables.abstract_observable import AbstractObservable
from tqec.compile.observables.builder import (
    ObservableBuilder,
    ObservableComponent,
    get_observable_with_measurement_records,
)
from tqec.utils.position import BlockPosition2D

if TYPE_CHECKING:
    from tqec.compile.tree.node import LayerNode


def get_ordered_leaves(root: LayerNode) -> list[LayerNode]:
    """Return the leaves of the tree in time order."""
    if root.is_leaf:
        return [root]
    return [n for child in root.children for n in get_ordered_leaves(child)]


def annotate_observable(
    root: LayerNode,
    k: int,
    observable: AbstractObservable,
    observable_index: int,
    observable_builder: ObservableBuilder,
) -> None:
    """Annotates the observables on the tree.

    Args:
        root: root node of the tree.
        k: distance parameter.
        observable: observable to annotate.
        observable_index: index of the observable in the circuit.
        observable_builder: builder that computes and constructs qubits whose
            measurements will be included in the logical observable.

    """
    for subtree_root in root.children:
        layer = subtree_root._layer
        assert isinstance(layer, SequencedLayers)
        z = layer.z_coordinate
        assert z is not None, "z_coordinate must be set for observable annotation"

        leaves = get_ordered_leaves(subtree_root)
        obs_slice = observable.slice_at_z(z)
        # Annotate the observable at the bottom of the blocks
        _annotate_observable_at_node(
            leaves[0],
            obs_slice,
            k,
            observable_index,
            observable_builder,
            ObservableComponent.BOTTOM_STABILIZERS,
        )
        readout_layer = leaves[-1]
        if obs_slice.temporal_hadamard_pipes:
            readout_layer = leaves[-2]
            # Annotate the observable at the realignment layer in temporal hadamard pipes
            _annotate_observable_at_node(
                leaves[-1],
                obs_slice,
                k,
                observable_index,
                observable_builder,
                ObservableComponent.REALIGNMENT,
            )
        # Annotate the observable at the top of the blocks
        _annotate_observable_at_node(
            readout_layer,
            obs_slice,
            k,
            observable_index,
            observable_builder,
            ObservableComponent.TOP_READOUTS,
        )


def _annotate_observable_at_node(
    node: LayerNode,
    obs_slice: AbstractObservable,
    k: int,
    observable_index: int,
    observable_builder: ObservableBuilder,
    component: ObservableComponent,
) -> None:
    circuit = node.get_annotations(k).circuit
    assert circuit is not None
    measurement_record = MeasurementRecordsMap.from_scheduled_circuit(circuit)
    assert isinstance(node._layer, LayoutLayer)
    template, _ = node._layer.to_template_and_plaquettes()
    obs_qubits = observable_builder.build(k, template, obs_slice, component)
    if obs_qubits:
        obs_annotation = get_observable_with_measurement_records(
            obs_qubits, measurement_record, observable_index
        )
        node.get_annotations(k).observables.append(obs_annotation)


def y_switch_top_by_position(leaf: LayerNode) -> dict[BlockPosition2D, str]:
    """Map each Y half cube's block position to its transition (SWITCH) top boundary basis.

    The fixed-bulk Y logical (midline) is measured during the transition round, so a non-empty
    result also identifies the interior layer at which it should be annotated. A spatial junction
    can host Y cubes of *both* boundary bases at the same z-slice, so the midline geometry must be
    resolved per cube (each ``_YRoundTemplate`` carries its own ``top``), not once per leaf.
    Returns an empty mapping for any layer that is not a Y transition round.
    """
    # Lazy imports: keep the generic annotator free of a convention-specific dependency.
    from tqec.compile.blocks.positioning import LayoutCubePosition2D  # noqa: PLC0415
    from tqec.compile.specs.library.generators.y_basis_fixed_bulk import (  # noqa: PLC0415
        _YRoundTemplate,
    )

    result: dict[BlockPosition2D, str] = {}
    layer = leaf._layer
    if not isinstance(layer, LayoutLayer):
        return result
    for position, plaquette_layer in layer.layers.items():
        template = getattr(plaquette_layer, "template", None)
        if (
            isinstance(template, _YRoundTemplate)
            and template.kind == "switch"
            and isinstance(position, LayoutCubePosition2D)
        ):
            result[position.to_block_position()] = template.top
    return result


def _annotate_y_observable_at_node(
    node: LayerNode,
    obs_slice: AbstractObservable,
    k: int,
    observable_index: int,
    observable_builder: ObservableBuilder,
    top_by_position: dict[BlockPosition2D, str],
    component: ObservableComponent | None = None,
) -> None:
    """Annotate the fixed-bulk Y-basis logical (midline) at the transition (SWITCH) round node.

    The Y logical is the product of the single-corner ``MY`` and the two orthogonal midline
    stabiliser measurements, all measured during the transition round -- an interior layer of the
    Y half-cube block, not covered by the top/bottom face annotations. Each Y cube uses the top
    boundary basis of *its own* transition (``top_by_position``), so that a junction mixing X- and
    Z-oriented Y cubes annotates each midline correctly.
    """
    # Lazy import: keep the generic annotator free of a convention-specific dependency.
    from tqec.compile.specs.library.generators.y_basis_fixed_bulk import (  # noqa: PLC0415
        y_corner_local_coord,
        y_observable_local_coords,
    )

    circuit = node.get_annotations(k).circuit
    assert circuit is not None
    records = MeasurementRecordsMap.from_scheduled_circuit(circuit)
    assert isinstance(node._layer, LayoutLayer)
    layout_template, _ = node._layer.to_template_and_plaquettes()
    for cube in obs_slice.y_half_cubes:
        y_top = top_by_position.get(BlockPosition2D(cube.position.x, cube.position.y))
        if y_top is None:
            continue
        # The Y logical is read out only by the measurement half cube, whose single-corner ``MY``
        # is measured; the initialization half cube prepares the state (its corner is reset).
        corner_local = [y_corner_local_coord(2 * k + 1, y_top)]
        corner = observable_builder.transform_coords_into_grid(
            k, layout_template, corner_local, cube.position
        )
        if not any(c in records for c in corner):
            continue
        local_coords = y_observable_local_coords(2 * k + 1, y_top)
        qubits = observable_builder.transform_coords_into_grid(
            k, layout_template, local_coords, cube.position
        )
        obs_annotation = get_observable_with_measurement_records(qubits, records, observable_index)
        node.get_annotations(k).observables.append(obs_annotation)
