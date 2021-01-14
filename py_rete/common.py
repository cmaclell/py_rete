from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:  # pragma: no cover
    from typing import Hashable
    from typing import List
    from typing import Optional
    from py_rete.alpha import AlphaMemory
    from py_rete.beta import ReteNode
    from py_rete.pnode import PNode


variable_counter = 0


def gen_variable():
    """
    Used for generating variables with a unique name in the global context.
    """
    global variable_counter
    variable_counter += 1
    return V('genvar{}'.format(variable_counter))


@dataclass(eq=True, frozen=True)
class V:
    """
    A variable for pattern matching.
    """
    __slots__ = ['name']
    name: str

    def __repr__(self):
        return "V({})".format(self.name)


@dataclass(eq=True, frozen=True)
class Match:
    pnode: PNode
    token: Token

    def fire(self):
        return self.pnode.production.fire(self.token)


class WME:
    """
    This is essentially a fact, it has no variables in it. A working memory is
    essentially comprised of a collection of these elements.
    """
    __slots__ = ['identifier', 'attribute', 'value', 'amems', 'tokens',
                 'negative_join_results']

    def __init__(self, identifier: Hashable, attribute: Hashable, value:
                 Hashable) -> None:
        """
        Identifier, attribute, and value can be any kind of object except V
        objects (i.e., variables).
        """
        if (isinstance(identifier, V) or isinstance(attribute, V) or
                isinstance(value, V)):
            raise ValueError("WMEs cannot have variables (V objects).")

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
    """
    __slots__ = ['parent', 'wme', 'node', 'children', 'join_results',
                 'ncc_results', 'owner', 'binding']

    def __init__(self, parent: Optional[Token],
                 wme: Optional[WME],
                 node: Optional[ReteNode] = None,
                 binding: Optional[dict] = None
                 ) -> None:
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
        from py_rete.join_node import JoinNode

        for child in self.children:
            child.delete_token_and_descendents()

        if (isinstance(self.node, BetaMemory) and not
                isinstance(self.node, NccPartnerNode)):
            self.node.items.remove(self)

        if self.wme:
            self.wme.tokens.remove(self)
        if self.parent:
            self.parent.children.remove(self)

        if isinstance(self.node, BetaMemory):
            if not self.node.items:
                for bmchild in self.node.children:
                    if (isinstance(bmchild, JoinNode) and bmchild in
                            bmchild.amem.successors):
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
                    bchild.left_activation(self.owner, None,
                                           self.owner.binding)


@dataclass(eq=True, frozen=True)
class NegativeJoinResult:
    """
    A new class to store the result of a negative join. Similar to a token, it
    is owned by a token.
    """
    __slots__ = ['owner', 'wme']
    owner: Token
    wme: WME
