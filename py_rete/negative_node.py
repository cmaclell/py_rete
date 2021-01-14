from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token
from py_rete.common import NegativeJoinResult
from py_rete.alpha import AlphaMemory
from py_rete.beta import BetaMemory
from py_rete.join_node import JoinNode

if TYPE_CHECKING:  # pragma: no cover
    from typing import Dict
    from typing import Any
    from py_rete.common import V
    from py_rete.common import WME


class NegativeNode(BetaMemory, JoinNode):  # type: ignore
    """
    A beta network class that only passes on tokens when there is no match. The
    left activation is called by the parent beta node.  The right activation is
    called from the alpha network (amem).  Test are similar to those that
    appear in JoinNode
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        if self.amem == amem:
            return self
        return self.parent.find_nearest_ancestor_with_same_amem(amem)

    @property
    def right_unlinked(self) -> bool:
        return len(self.items) == 0

    def left_activation(self, token: Token, wme: WME, binding: Dict[V, Any]):
        if not self.items:
            self.relink_to_alpha_memory()

        new_token = Token(parent=token, wme=wme, node=self, binding=binding)
        self.items.append(new_token)

        for wme in self.amem.items:
            if self.perform_join_test(new_token, wme):
                jr = NegativeJoinResult(new_token, wme)
                new_token.join_results.append(jr)
                wme.negative_join_results.append(jr)

        if not new_token.join_results:
            for child in self.children:
                child.left_activation(new_token, None, binding)

    def right_activation(self, wme: WME):
        for token in self.items:
            if self.perform_join_test(token, wme):
                if not token.join_results:
                    # TODO: TEST THIS - Chris
                    token.delete_descendents_of_token()
                    # t.delete_token_and_descendents()
                jr = NegativeJoinResult(token, wme)
                token.join_results.append(jr)
                wme.negative_join_results.append(jr)
