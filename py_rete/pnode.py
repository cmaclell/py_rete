from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token
from py_rete.production import Production
from py_rete.beta import BetaMemory

if TYPE_CHECKING:  # pragma: no cover
    from typing import List
    from typing import Dict
    from typing import Any
    from py_rete.common import WME
    from py_rete.common import V


class PNode(BetaMemory):
    """
    A beta network node that stores the matches for productions.
    """

    def __init__(self, production: Production, **kwargs):
        super(PNode, self).__init__(**kwargs)
        self.production = production
        self.new: List[Token] = []

    def left_activation(self, token: Token, wme: WME, binding: Dict[V, Any]):
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)
        self.new.append(new_token)

    def pop_new_token(self):
        if self.new:
            return self.new.pop()

    def new_activations(self):
        while self.new:
            t = self.new.pop()
            yield t

    @property
    def activations(self):
        for t in self.items:
            yield t
