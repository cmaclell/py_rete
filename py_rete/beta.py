from py_rete.common import Token
from py_rete.common import ReteNode


class BetaMemory(ReteNode):
    """
    A memory to store tokens in the beta network."
    """

    def __init__(self, children=None, parent=None, items=None):
        """
        Similar to alpha memory, items is a set of tokens

        TODO:
            - should items be a set?

        :type items: list of Token
        """
        super(BetaMemory, self).__init__(children=children, parent=parent)
        self.items = items if items else []

    def left_activation(self, token, wme, binding=None):
        """
        Creates a new token based on the incoming token/wme, adds it to the
        memory (items) then activates the children with the token.

        TODO:
            - What about activation or right_activiation?
            - Token contains the wme, so do we need wme?

        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        new_token = Token(token, wme, node=self, binding=binding)
        self.items.append(new_token)
        for child in self.children:
            child.left_activation(new_token)
