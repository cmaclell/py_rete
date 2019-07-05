from py_rete.common import Token
from py_rete.common import ReteNode
from py_rete.production import Production


class PNode(ReteNode):
    """
    A beta network node that stores the matches for productions.
    """

    def __init__(self, production: Production, children=None, parent=None,
                 items=None):
        """
        :type items: list of Token
        """
        super(PNode, self).__init__(children=children, parent=parent)
        self.items = items if items else []
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
