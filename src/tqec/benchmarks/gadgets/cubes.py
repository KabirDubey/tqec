"""Single-cube gadgets: memory and stability experiments."""

from functools import partial

from tqec.benchmarks.gadgets._common import READY, build, pos
from tqec.benchmarks.gadgets.spec import GadgetSpec, register
from tqec.computation.block_graph import BlockGraph


def _single_cube(name: str, kind: str) -> BlockGraph:
    return build(name, [(pos(0, 0, 0), kind.upper())], [])


for _kind in ("zxz", "xzz", "zxx", "xzx"):
    # The last letter is the observable basis; the chain that flips it is of the other type.
    _basis = _kind[2]
    _chain = "x" if _basis == "z" else "z"
    register(
        GadgetSpec(
            id=f"memory_{_kind}",
            build=partial(_single_cube, f"memory_{_kind}", _kind),
            family="memory",
            mechanisms=frozenset(
                {
                    f"space:regular:{_chain}chain",
                    f"time:memory:{_basis}",
                    f"time:boundary:init:{_basis}",
                    f"time:boundary:meas:{_basis}",
                }
            ),
            expected=READY,
        )
    )

for _kind in ("zzx", "xxz"):
    _basis = _kind[0]
    register(
        GadgetSpec(
            id=f"stability_{_kind}",
            build=partial(_single_cube, f"stability_{_kind}", _kind),
            family="stability",
            mechanisms=frozenset({f"time:stability:{_basis}"}),
            expected=READY,
        )
    )
