r"""Logical S Gate
==============

This example demonstrates a logical S gate by gate teleportation, with an
inplace Y basis measurement, as in :footcite:t:`Gidney_inplace_access_2024`.

Construction
------------

The S gate is teleported in two steps:

- an :math:`M_{ZZ}` measurement between the target qubit and an ancilla qubit
  initialized in the :math:`|+\rangle` state,
- a Y basis measurement of the ancilla qubit, done by a Y half cube.

``tqec`` provides the builtin function ``tqec.gallery.s_gate_teleportation`` to
construct it. The ``In`` port is at the bottom of the block graph and the ``Out``
port is at the top.
"""

# ruff: noqa: E402

from tqec import PauliBasis
from tqec.gallery import s_gate_teleportation

graph = s_gate_teleportation(PauliBasis.X)
# %%

graph.view_as_html()

# %%
# Up to signs, the S gate maps :math:`X` to :math:`Y` and :math:`Z` to :math:`Z`.
# The correlation surface below shows the :math:`X` operator at the input, at the
# bottom, mapped to the :math:`Y` operator at the output, at the top, where the Y
# half cube measures it.

correlation_surfaces = graph.find_correlation_surfaces()
# %%

graph.view_as_html(
    pop_faces_at_directions=("-Y",),
    show_correlation_surface=correlation_surfaces[0],
)

# %%
# Circuit
# -------
#
# You can download the circuit for a ``d=3`` S gate from
# :download:`here <../media/gallery/s_gate/circuit.stim>`, or generate it with
# the code below. The link it prints opens the ``d=5`` (``k=2``) circuit in Crumble.

from IPython.display import HTML

from tqec import NoiseModel, compile_block_graph

compiled_graph = compile_block_graph(graph)
circuit = compiled_graph.generate_stim_circuit(
    k=1, noise_model=NoiseModel.uniform_depolarizing(p=0.001)
)
HTML(f'<a href="{compiled_graph.generate_crumble_url(k=2)}">Open the d=5 circuit in Crumble</a>')

# %%
# Simulation
# ----------
#
# Here we show the simulation results of the :math:`X \rightarrow Y` and
# :math:`Z \rightarrow Z` flows under the **uniform depolarizing** noise model.
#
# The full code used for the simulation is shown below.

from multiprocessing import cpu_count
from pathlib import Path

import matplotlib.pyplot as plt
import numpy
import sinter

from tqec.simulation.plotting.inset import plot_observable_as_inset
from tqec.simulation.simulation import start_simulation_using_sinter


def generate_graphs(in_observable_basis: PauliBasis) -> None:
    """Generate the logical error-rate graphs corresponding to the provided basis."""
    block_graph = s_gate_teleportation(in_observable_basis)
    zx_graph = block_graph.to_zx_graph()

    correlation_surfaces = block_graph.find_correlation_surfaces()

    stats = start_simulation_using_sinter(
        block_graph,
        range(1, 4),
        list(numpy.logspace(-4, -1, 10)),
        NoiseModel.uniform_depolarizing,
        manhattan_radius=2,
        observables=correlation_surfaces,
        num_workers=cpu_count(),
        max_shots=1_000_000,
        max_errors=5_000,
        decoders=["pymatching"],
        # note that save_resume_filepath and database_path can help reduce the time taken
        # by the simulation after the database and result statistics have been saved to
        # the chosen path
        save_resume_filepath=Path(
            f"../_examples_database/s_gate_stats_{in_observable_basis.value}.csv"
        ),
        database_path=Path("../_examples_database/database.pkl"),
    )

    for i, stat in enumerate(stats):
        _, ax = plt.subplots()
        sinter.plot_error_rate(
            ax=ax,
            stats=stat,
            x_func=lambda stat: stat.json_metadata["p"],
            failure_units_per_shot_func=lambda stat: stat.json_metadata["d"],
            group_func=lambda stat: stat.json_metadata["d"],
        )
        plot_observable_as_inset(ax, zx_graph, correlation_surfaces[i])
        ax.grid(axis="both")
        ax.legend()
        ax.loglog()
        ax.set_title("Logical S Gate Error Rate")
        ax.set_xlabel("Physical Error Rate")
        ax.set_ylabel("Logical Error Rate")


# %%
# :math:`X \rightarrow Y`
# ~~~~~~~~~~~~~~~~~~~~~~~

generate_graphs(PauliBasis.X)

# %%
# :math:`Z \rightarrow Z`
# ~~~~~~~~~~~~~~~~~~~~~~~

generate_graphs(PauliBasis.Z)

# %%
# References
# ----------
#
# .. footbibliography::
