Test gadgets
============

:mod:`tqec.gallery.gadgets` is a registry of small block graphs (gadgets) for testing and
benchmarking the compiler. Each entry (a :class:`~tqec.gallery.gadgets.spec.GadgetSpec`) has an id,
a family, a set of tags naming the logical error mechanisms the gadget covers, the status the
compiler is expected to reach under the fixed bulk convention, and, if it is blocked, the pull
request or branch that must land first.

Only the fixed bulk convention is covered.

List and filter
---------------

.. code-block:: bash

    python -m tqec.gallery.gadgets --list
    python -m tqec.gallery.gadgets --family memory
    python -m tqec.gallery.gadgets --mechanism time:memory:z --mechanism space:regular:xchain
    python -m tqec.gallery.gadgets --convention fixed_bulk --status ready --json

``--status`` requires ``--convention``.

Export
------

.. code-block:: bash

    python -m tqec.gallery.gadgets --family pair --export out/ --format bgraph

``--format dae`` writes Collada files instead.

Use from Python
---------------

.. code-block:: python

    from tqec.gallery.gadgets import iter_gadgets, vend

    ready = iter_gadgets(convention="fixed_bulk", status="ready")
    inputs = vend(ready)  # BlockGraphs named after the ids, or Paths for file-backed gadgets

``inputs`` can be passed to :func:`tqec.orchestration.prepare_batch` where batch processing is
available.

Add a gadget
------------

Create ``src/tqec/gallery/gadgets/<family>.py``, call ``register(GadgetSpec(...))`` and import
the module in ``tqec/gallery/gadgets/__init__.py``. Tags must come from
:data:`~tqec.gallery.gadgets.mechanisms.MECHANISMS`. A gadget stored as a file can give
``build=lambda: DATA_DIR / "my_gadget.bgraph"``. The fast tests check that ids are unique and every
tag has a gadget; the slow test (``pytest -m slow tests/gallery/gadgets_compile_test.py``)
compiles each gadget at ``k=1`` and compares its status and distance with the spec. It takes
about a minute, but compiles circuits, so run it on a compute machine.

Worked example: a patch rotation gadget (#1101)
-----------------------------------------------

The tags for the patch rotation block are predeclared in
:data:`~tqec.gallery.gadgets.mechanisms.PENDING`, mapped to the blocking issue (#1012). A
contributor adds only a family module and the drawn files; ``mechanisms.py``, ``spec.py`` and the
tests stay untouched, because the coverage test allows pending tags that no spec covers yet.

.. code-block:: python

    # src/tqec/gallery/gadgets/patch_rotation.py
    from pathlib import Path

    from tqec.gallery.gadgets.spec import GadgetSpec, register

    DATA_DIR = Path(__file__).parent / "data" / "patch_rotation"

    register(
        GadgetSpec(
            id="patch_rotation_temporal_z",
            build=lambda: DATA_DIR / "patch_rotation_temporal_z.dae",
            family="patch_rotation",
            mechanisms=frozenset({"space:patch_rotation:temporal:z"}),
            expected={"fixed_bulk": "import_failed"},
            blocked_by=("https://github.com/tqec/tqec/issues/1012",),
        )
    )

Then put the ``.dae`` file in ``data/patch_rotation/`` and import ``patch_rotation`` in
``tqec/gallery/gadgets/__init__.py``. When #1012 lands and the file imports, change ``expected``
to the observed status.
