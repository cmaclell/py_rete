from __future__ import annotations

from py_rete.common import Token
from py_rete.production import Production
from py_rete.beta import BetaMemory


class PNode(BetaMemory):
    """
    A beta network node that stores the matches for productions.
    """

    def __init__(self, production: Production, **kwargs):
        """
        :type items: list of Token
        """
        super(PNode, self).__init__(**kwargs)
        self.production = production

    def left_activation(self, token, wme, binding=None):
        """
        :type wme: WME
        :type token: Token
        :type binding: dict
        """
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)

    @property
    def activations(self):
        for t in self.items:
            yield t
