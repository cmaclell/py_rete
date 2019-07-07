from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token
from py_rete.common import NegativeJoinResult
from py_rete.alpha import AlphaMemory
from py_rete.beta import BetaMemory
from py_rete.join_node import JoinNode


if TYPE_CHECKING:
    from typing import List
    from py_rete.common import WME


class NegativeNode(BetaMemory, JoinNode):  # type: ignore
    """
    A beta network class that only passes on tokens when there is no match.

    The left activation is called by the parent beta node.
    The right activation is called from the alpha network (amem).
    Test are similar to those that appear in JoinNode

    TODO:
        - should negative node be a subclass of JoinNode?
            - perform_join_test is identical to JoinNode
            - doesn't have Has, not sure why JoinNode does though.
        - should this have a kind?

    """
    parent: JoinNode  # type: ignore
    children: List[JoinNode]  # type: ignore

    def __init__(self, **kwargs):
        """
        :type children:
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        """
        super(NegativeNode, self).__init__(**kwargs)

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        if self.amem == amem:
            return self
        return self.parent.find_nearest_ancestor_with_same_amem(amem)

    @property
    def right_unlinked(self) -> bool:
        return len(self.items) == 0

    def left_activation(self, token, wme, binding=None):
        """
        :type wme: rete.WME
        :type token: rete.Token
        :type binding: dict
        """
        if not self.items:
            self.relink_to_alpha_memory()

        new_token = Token(parent=token, wme=wme, node=self, binding=binding)
        self.items.append(new_token)

        for item in self.amem.items:
            if self.perform_join_test(new_token, item):
                jr = NegativeJoinResult(new_token, item)
                new_token.join_results.append(jr)
                item.negative_join_results.append(jr)

        if not new_token.join_results:
            for child in self.children:
                child.left_activation(new_token, None)

    def right_activation(self, wme):
        """
        :type wme: rete.WME
        """
        for t in self.items:
            if self.perform_join_test(t, wme):
                if not t.join_results:
                    # TODO: TEST THIS - Chris
                    t.delete_descendents_of_token()
                    # t.delete_token_and_descendents()
                jr = NegativeJoinResult(t, wme)
                t.join_results.append(jr)
                wme.negative_join_results.append(jr)

    def perform_join_test(self, token: Token, wme: WME):
        """
        :type token: rete.Token
        :type wme: rete.WME
        """
        for this_test in self.tests:
            arg1 = getattr(wme, this_test.field_of_arg1)
            wme2 = token.wmes[this_test.condition_number_of_arg2]
            arg2 = getattr(wme2, this_test.field_of_arg2)
            if arg1 != arg2:
                return False
        return True
