from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token

if TYPE_CHECKING:
    from typing import List
    from typing import Optional
    from py_rete.common import WME
    from py_rete.alpha import AlphaMemory
    from py_rete.join_node import JoinNode


class ReteNode:
    """
    Base BetaNode class, tracks parent and children.
    """

    def __init__(self, children=None, parent=None, **kwargs):
        super(ReteNode, self).__init__()
        self.children = children if children else []
        self.parent = parent

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        return None

    def dump(self):
        return "%s %s" % (self.__class__.__name__, id(self))


class BetaMemory(ReteNode):
    """
    A memory node for the beta network.
    """
    parent: JoinNode
    children: List[JoinNode]

    def __init__(self, items: Optional[List[Token]] = None, **kwargs):
        """
        Similar to alpha memory, but items is a set of tokens instead of wmes.

        :type items: list of Token
        """
        super(BetaMemory, self).__init__(**kwargs)
        self.items: List[Token] = items if items else []
        self.all_children: List[JoinNode] = []

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        return self.parent.find_nearest_ancestor_with_same_amem(amem)

    def left_activation(self, token: Optional[Token] = None,
                        wme: Optional[WME] = None,
                        binding: Optional[dict] = None):
        """
        Creates a new token based on the incoming token/wme, adds it to the
        memory (items) then activates the children with the token.

        TODO:
            - What about activation or right_activiation?
            - check order of activating children

        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)
        for child in self.children:
            child.left_activation(new_token)
