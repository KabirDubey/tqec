Y half cubes
============

A Y half cube (see :ref:`terminology <terminology>` for the definition) implements in-place Y-basis
logical initialization or measurement.
This page describes how to place one in a :py:class:`~tqec.computation.block_graph.BlockGraph`,
compile it to a ``stim.Circuit``, and which restrictions apply.

.. important::

    The layer specification used to implement Y half cubes (the sequence of rounds described
    below and the default number of padding rounds) may be revised in a future release.
    Do not rely on the exact round structure.

Placing a Y half cube
---------------------

A Y half cube is a cube of kind ``"Y"`` (:py:attr:`.LeafCubeKind.Y_HALF_CUBE`). It must be connected
to exactly one pipe, and that pipe must be along the time (``Z``) axis. Whether the half cube
initializes or measures is decided by the side of the pipe it sits on:

- a Y half cube with a pipe going **up** (towards larger ``z``) is a Y-basis **initialization**;
- a Y half cube with a pipe going **down** is a Y-basis **measurement**.

The pipe kind also sets the orientation of the half cube (it fixes the basis of the horizontal
boundary of the connected pipe).

The following block graph is a Y-basis memory: a Y initialization followed by a Y measurement.
It is the same graph as ``tqec.gallery.memory(PauliBasis.Y)``.

.. code-block:: python

    from tqec import BlockGraph, compile_block_graph
    from tqec.compile.convention import FIXED_BULK_CONVENTION
    from tqec.utils.position import Position3D

    g = BlockGraph("Y-basis memory")
    n1 = g.add_cube(Position3D(0, 0, 0), "Y")
    n2 = g.add_cube(Position3D(0, 0, 1), "Y")
    g.add_pipe(n1, n2, "ZXO")

    compiled = compile_block_graph(g, FIXED_BULK_CONVENTION)
    circuit = compiled.generate_stim_circuit(k=1, noise_model=None)

The ``"ZXO"`` pipe above was checked to compile with ``k=1``; the test-suite also compiles
``"XZO"`` pipes. A Y half cube can also be attached to the other cubes of a computation; see
:py:func:`tqec.gallery.s_gate_teleportation` for an example, which accepts
``PauliBasis.Y`` as its input observable basis.

Supported conventions
---------------------

Y half cubes are only implemented for the **fixed bulk** convention
(:py:data:`tqec.compile.convention.FIXED_BULK_CONVENTION`). Compiling a block graph that contains a
Y half cube with the fixed boundary convention raises a ``NotImplementedError``.

Rounds and padding
------------------

The block implementing a Y half cube is made of three kinds of rounds:

- a *transition* round, which deforms the surface code patch into a degenerate patch (or the
  reverse for an initialization);
- *padding* rounds on the degenerate patch;
- a *final* round, which reads out the data qubits.

A measurement half cube is the transition round, then the padding rounds, then the final round.
An initialization half cube is the time reverse of that sequence. The transition round is the
side of the half cube connected to the neighbouring cube and is placed directly against the state
of that neighbour: no idle round is inserted between them.

When compiling a block graph, the number of padding rounds is the ``block_temporal_height`` argument
of :py:func:`~tqec.compile.compile.compile_block_graph` (default ``2k - 1``), i.e. the same number
of repeated rounds as the other cubes of the graph. Detectors are not hard-coded in the Y half cube
blocks; they are computed when the circuit is generated.

Interaction with conditional cubes
----------------------------------

Conditional cubes (:py:class:`~tqec.computation.cube.ConditionalCubeKind`) can have Y half cubes as
branches, and such graphs can be constructed, validated and serialized. They **cannot be
compiled**: the cube builders of both the fixed bulk and the fixed boundary conventions raise
``NotImplementedError("Conditional cube is not implemented.")`` when they meet a conditional cube
kind, whatever its branches are. This is also the case for conditional cubes without any Y branch.

Current limitations
-------------------

- Only the fixed bulk convention is supported (see above).
- Y half cubes with conditional cubes cannot be compiled (see above).
- For ``k=1`` and an ``"XZO"`` pipe, the compiled Y memory is currently not guaranteed to reach
  the expected circuit-level distance with the released ``tqecd`` version: the corresponding test
  is marked as an expected failure until a ``tqecd`` release with the fix is available.
- Only occupied time slices are compiled. If the block graph has a gap in ``z`` (a range of
  ``z`` values without any cube), the empty time slices are dropped, and the circuit does not
  contain any time between the two parts of the computation separated by the gap.
