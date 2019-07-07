from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from typing import Optional
    from typing import Generator
    from typing import Union
    from py_rete.join_node import JoinNode
    from py_rete.negative_node import NegativeNode
    from py_rete.common import WME


class AlphaMemory:

    def __init__(self, items: Optional[List[WME]] = None, successors=None):
        """
        Stores a set of WMEs (items). If activating an activated wme does not
        exist, then it addes it. It also right activates all of its successors,
        which correspond ot beta nodes.

        TODO:
            - replace self.items with a set rather than a list?
            - why are beta nodes (successors) activated in reverse order?

        :type successors: list of BetaNode
        :type items: list of rete.WME
        """
        self.items: List[WME] = items if items else []
        self.successors: List[Union[JoinNode, NegativeNode]
                              ] = successors if successors else []
        self.reference_count = 0

    def activations(self) -> Generator[WME, None, None]:
        for wme in self.items:
            yield wme

    def activation(self, wme: WME) -> None:
        """
        :type wme: rete.WME
        """
        self.items.append(wme)
        wme.amems.append(self)
        for child in reversed(self.successors):
            child.right_activation(wme)
