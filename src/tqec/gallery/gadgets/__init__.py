"""Registry of test gadgets: named block graphs with the facts needed to benchmark them.

A :class:`~tqec.gallery.gadgets.spec.GadgetSpec` carries a block graph builder, the error
mechanisms the gadget covers (:data:`~tqec.gallery.gadgets.mechanisms.MECHANISMS`), the status
and distance expected of each convention, and what blocks it. :func:`vend` turns specs into the
inputs of :func:`tqec.orchestration.prepare_batch`:

.. code-block:: python

    from tqec.gallery.gadgets import iter_gadgets, vend

    inputs = vend(iter_gadgets(family="memory"))

``python -m tqec.gallery.gadgets --list`` prints the registry.
"""

# Importing the family modules registers their specs.
from tqec.gallery.gadgets import (  # noqa: F401
    conditional,
    cubes,
    gallery,
    hadamard,
    junctions,
    pipes,
    y_half_cube,
)
from tqec.gallery.gadgets.mechanisms import CONVENTIONS as CONVENTIONS
from tqec.gallery.gadgets.mechanisms import MECHANISMS as MECHANISMS
from tqec.gallery.gadgets.mechanisms import STATUSES as STATUSES
from tqec.gallery.gadgets.spec import GadgetSpec as GadgetSpec
from tqec.gallery.gadgets.spec import Witness as Witness
from tqec.gallery.gadgets.spec import build_graph as build_graph
from tqec.gallery.gadgets.spec import get as get
from tqec.gallery.gadgets.spec import iter_gadgets as iter_gadgets
from tqec.gallery.gadgets.spec import register as register
from tqec.gallery.gadgets.spec import vend as vend
