from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token
from py_rete.alpha import AlphaMemory
from py_rete.beta import BetaMemory

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional
    from typing import List
    from typing import Dict
    from typing import Any
    from py_rete.beta import ReteNode
    from py_rete.common import V
    from py_rete.common import WME


class NccNode(BetaMemory):
    """
    A beta network class for negated conjunctive conditions (ncc).

    This has a memory of tokens (items) and a partner node. On left_activation
    (from parent), the node adds results from its partner's result buffer to
    the newly created token's ncc_results list, and sets the owner of the
    result to the new token. If the new token does not have a any results in
    the ncc_results list, then it activates all the children.
    """

    def __init__(self, partner: NccPartnerNode = None, **kwargs):
        super().__init__(**kwargs)
        self.partner = partner

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        return self.partner.parent.find_nearest_ancestor_with_same_amem(amem)

    def left_activation(self, token: Token, wme: WME, binding: Dict[V, Any]):
        new_token = Token(token, wme, self, binding)
        self.items.append(new_token)
        for result in self.partner.new_result_buffer:
            self.partner.new_result_buffer.remove(result)
            new_token.ncc_results.append(result)
            result.owner = new_token
        if not new_token.ncc_results:
            for child in self.children:
                child.left_activation(new_token, None, binding)


class NccPartnerNode:
    """
    The partner node for negated conjunctive conditions node.

    Takes the associated ncc node, the number of conditions, and a buffer of
    any new results.
    """

    def __init__(self, parent: Optional[ReteNode] = None,
                 ncc_node: Optional[NccNode] = None,
                 number_of_conditions: int = 0,
                 new_result_buffer: Optional[List[Token]] = None):
        self.parent = parent
        self.ncc_node = ncc_node
        self.number_of_conditions = number_of_conditions
        self.new_result_buffer = new_result_buffer if new_result_buffer else []

    def left_activation(self, token: Token, wme: WME, binding: Dict[V, Any]):
        new_result = Token(token, wme, self, binding)
        owners_t = token
        owners_w = wme
        for i in range(self.number_of_conditions):
            owners_w = owners_t.wme
            owners_t = owners_t.parent
        for token in self.ncc_node.items:
            if token.parent == owners_t and token.wme == owners_w:
                token.ncc_results.append(new_result)
                new_result.owner = token
                token.delete_descendents_of_token()
                break
        else:
            self.new_result_buffer.append(new_result)
