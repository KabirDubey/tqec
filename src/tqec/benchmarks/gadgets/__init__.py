"""Registry of test gadgets: named block graphs with the facts needed to benchmark them.

A :class:`~tqec.benchmarks.gadgets.spec.GadgetSpec` carries a block graph builder, the error
mechanisms the gadget covers (:data:`~tqec.benchmarks.gadgets.mechanisms.MECHANISMS`), the status
and distance expected of each convention, and what blocks it. :func:`vend` turns specs into the
inputs of :func:`tqec.orchestration.prepare_batch`:

.. code-block:: python

    from tqec.benchmarks.gadgets import iter_gadgets, vend

    inputs = vend(iter_gadgets(family="memory"))

``python -m tqec.benchmarks.gadgets --list`` prints the registry.
"""

# Importing the family modules registers their specs.
from tqec.benchmarks.gadgets import (  # noqa: F401
    conditional,
    cubes,
    gallery,
    hadamard,
    junctions,
    pipes,
    y_half_cube,
)
from tqec.benchmarks.gadgets.mechanisms import CONVENTIONS as CONVENTIONS
from tqec.benchmarks.gadgets.mechanisms import MECHANISMS as MECHANISMS
from tqec.benchmarks.gadgets.mechanisms import PENDING as PENDING
from tqec.benchmarks.gadgets.mechanisms import STATUSES as STATUSES
from tqec.benchmarks.gadgets.spec import GadgetSpec as GadgetSpec
from tqec.benchmarks.gadgets.spec import build_graph as build_graph
from tqec.benchmarks.gadgets.spec import get as get
from tqec.benchmarks.gadgets.spec import iter_gadgets as iter_gadgets
from tqec.benchmarks.gadgets.spec import register as register
from tqec.benchmarks.gadgets.spec import vend as vend
