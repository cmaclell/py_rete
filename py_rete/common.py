# -*- coding: utf-8 -*-
"""
    TODO:
        - Why is fields at the top? is it mutable?
            - seems to be used in other functions to get the field names
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List
    from typing import Optional
    from py_rete.alpha import AlphaMemory
    from py_rete.beta import ReteNode


def is_var(v):
    return v.startswith('$')


class WME:
    """
    This is essentially a fact, it has no variables in it. A working memory is
    essentially comprised of a collection of these elements.

    TODO:
        - Change to prefix?
        - Add tests to raise exception in the presence of variables.
    """

    def __init__(self, identifier: str, attribute: str, value: str) -> None:
        """
        identifier, attribute, and value are all strings, if they start with a
        $ then they are a variable.

        :type identifier: str
        :type attribute: str
        :type value: str
        """
        assert not is_var(identifier)
        assert not is_var(attribute)
        assert not is_var(value)

        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        self.amems: List[AlphaMemory] = []  # the ones containing this WME
        self.tokens: List[Token] = []  # the ones containing this WME
        self.negative_join_results: List[NegativeJoinResult] = []

    def __hash__(self):
        return hash((self.identifier, self.attribute, self.value))

    def __repr__(self):
        return "(%s ^%s %s)" % (self.identifier, self.attribute, self.value)

    def __eq__(self, other: object) -> bool:
        """
        :type other: WME
        """
        if not isinstance(other, WME):
            return False
        return self.identifier == other.identifier and \
            self.attribute == other.attribute and \
            self.value == other.value


class Token:
    """
    Tokens represent matches within the alpha and beta memories. The parent
    corresponds to the match that was extended to create the current token.

    TODO:
        - Node, maybe should be of type BetaMemory, it shoud have items.
    """

    def __init__(self, parent: Optional[Token], wme: Optional[WME], node:
                 Optional[ReteNode] = None,
                 binding: Optional[dict] = None) -> None:
        """
        :type wme: WME
        :type parent: Token
        :type binding: dict
        """
        self.parent = parent
        self.wme = wme
        # points to memory this token is in
        self.node = node
        # the ones with parent = this token
        self.children: List[Token] = []
        # used only on tokens in negative nodes
        self.join_results: List[NegativeJoinResult] = []
        self.ncc_results: List[Token] = []
        # Ncc
        self.owner: Optional[Token] = None
        self.binding = binding if binding else {}  # {"$x": "B1"}

        if self.parent:
            self.parent.children.append(self)
        if self.wme:
            self.wme.tokens.append(self)

    def __repr__(self) -> str:
        return "<Token %s>" % self.wmes

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Token) and self.parent == other.parent and
                self.wme == other.wme)

    def is_root(self) -> bool:
        return not self.parent and not self.wme

    @property
    def wmes(self) -> List[Optional[WME]]:
        ret = [self.wme]
        t = self
        while t.parent and not t.parent.is_root():
            t = t.parent
            ret.insert(0, t.wme)
        return ret

    def get_binding(self, v: str) -> Optional[str]:
        """
        Walks up the parents until it finds a binding for the variable.

        TODO:
            - Seems expensive, maybe possible to cache?
        """
        assert is_var(v)
        t = self
        ret = t.binding.get(v)
        while not ret and t.parent:
            t = t.parent
            ret = t.binding.get(v)
        return ret

    def all_binding(self) -> dict:
        path = [self]
        if path[0].parent:
            path.insert(0, path[0].parent)
        binding = {}
        for t in path:
            binding.update(t.binding)
        return binding

    def delete_descendents_of_token(self) -> None:
        """
        Helper function to delete all the descendent tokens.
        """
        for t in self.children:
            t.delete_token_and_descendents()

    def delete_token_and_descendents(self) -> None:
        """
        Deletes a token and its descendents, but has special cases that make
        this difficult to understand in isolation.

        TODO:
            - Add optimization for right unlinking (pg 87 of Doorenbois
              thesis).

        :type token: Token
        """
        from py_rete.ncc_node import NccNode
        from py_rete.ncc_node import NccPartnerNode
        from py_rete.negative_node import NegativeNode
        from py_rete.beta import BetaMemory
        from py_rete.pnode import PNode

        for child in self.children:
            child.delete_token_and_descendents()

        if (isinstance(self.node, (BetaMemory, NegativeNode, PNode)) and not
                isinstance(self.node, NccPartnerNode)):
            self.node.items.remove(self)

        if self.wme:
            self.wme.tokens.remove(self)
        if self.parent:
            self.parent.children.remove(self)

        if isinstance(self.node, BetaMemory):
            if not self.node.items:
                for bmchild in self.node.children:
                    bmchild.amem.successors.remove(bmchild)

        if isinstance(self.node, NegativeNode):
            if not self.node.items:
                self.node.amem.successors.remove(self.node)
            for jr in self.join_results:
                jr.wme.negative_join_results.remove(jr)

        if isinstance(self.node, NccNode):
            for result_tok in self.ncc_results:
                if result_tok.wme:
                    result_tok.wme.tokens.remove(result_tok)
                if result_tok.parent:
                    result_tok.parent.children.remove(result_tok)

        elif isinstance(self.node, NccPartnerNode):
            self.owner.ncc_results.remove(self)
            if not self.owner.ncc_results and self.node.ncc_node:
                for bchild in self.node.ncc_node.children:
                    # TODO what is the None?
                    bchild.left_activation(self.owner, None)


class NegativeJoinResult:
    """
    A new class to store the result of a negative join. Similar to a token, it
    is owned by a token.
    """

    def __init__(self, owner: Token, wme: WME):
        """
        :type wme: rete.WME
        :type owner: rete.Token
        """
        self.owner = owner
        self.wme = wme
