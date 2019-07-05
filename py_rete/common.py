# -*- coding: utf-8 -*-
"""
    TODO:
        - Why is fields at the top? is it mutable?
            - seems to be used in other functions to get the field names
"""
from __future__ import annotations
from typing import List
from typing import Tuple
from typing import Optional

from py_rete.alpha import AlphaMemory


def is_var(v):
    return v.startswith('$')


class ReteNode:
    """
    Base BetaNode class, tracks parent and children.
    """
    items: Optional[List[Token]]

    def __init__(self, children: Optional[List[ReteNode]] = None, parent:
                 Optional[ReteNode] = None, **kwargs):
        self.children: List[ReteNode] = children if children else []
        self.parent = parent

    def dump(self):
        return "%s %s" % (self.__class__.__name__, id(self))

    def left_activation(self, token: Optional[Token], wme: Optional[WME],
                        binding: Optional[dict] = None):
        raise NotImplementedError


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
        self.identifier = identifier
        self.attribute = attribute
        self.value = value
        self.amems: List[AlphaMemory] = []  # the ones containing this WME
        self.tokens: List[Token] = []  # the ones containing this WME
        self.negative_join_results: List[NegativeJoinResult] = []

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


class Has:
    """
    Essentially a pattern/condition to match, can have variables.

    TODO:
        - Rename as conditions.
        - Change order to be prefix? idk.
    """

    def __init__(self, identifier: Optional[str] = None, attribute:
                 Optional[str] = None, value: Optional[str] = None) -> None:
        """
        Constructor.

        TODO:
            - Can I change the order of these to make them prefix?

        (<x> ^self <y>)
        repr as:
        ('$x', 'self', '$y')

        :type value: Var or str
        :type attribute: Var or str
        :type identifier: Var or str
        """
        self.identifier = identifier
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return "(%s %s %s)" % (self.identifier, self.attribute, self.value)

    def __eq__(self, other: object):
        if not isinstance(other, Has):
            return False
        return (self.__class__ == other.__class__
                and self.identifier == other.identifier
                and self.attribute == other.attribute
                and self.value == other.value)

    @property
    def vars(self) -> List[Tuple[str, str]]:
        """
        Returns a list of variables with the labels for the slots they occupy.

        :rtype: list
        """
        ret = []
        for field in ['identifier', 'attribute', 'value']:
            v = getattr(self, field)
            if is_var(v):
                ret.append((field, v))
        return ret

    def contain(self, v: str) -> str:
        """
        Checks if a variable is in a pattern. Returns field if it is, otherwise
        an empty string.

        TODO:
            - Why does this return an empty string on failure?

        :type v: Var
        :rtype: bool
        """
        assert is_var(v)

        for f in ['identifier', 'attribute', 'value']:
            _v = getattr(self, f)
            if _v == v:
                return f
        return ""

    def test(self, w: WME) -> bool:
        """
        Checks if a pattern matches a working memory element.

        :type w: rete.WME
        """
        for f in ['identifier', 'attribute', 'value']:
            v = getattr(self, f)
            if is_var(v):
                continue
            if v != getattr(w, f):
                return False
        return True


class Neg(Has):
    """
    A negated pattern.

    TODO:
        - Does this need test implemented?
    """

    def __repr__(self):
        return "-(%s %s %s)" % (self.identifier, self.attribute, self.value)


class Rule(list):
    """
    Essentially an AND, a list of conditions.

    TODO:
        - Implement an OR equivelent, that gets compiled when added to a
          network into multiple rules.
        - Need somewhere to store right hand sides? What to do when rules fire.
          Might need an actual rule or production class.
    """

    def __init__(self, *args: List[Has]) -> None:
        self.extend(args)


class Ncc(Rule):
    """
    Essentially a negated AND, a negated list of conditions.
    """

    def __repr__(self):
        return "-%s" % super(Ncc, self).__repr__()

    @property
    def number_of_conditions(self) -> int:
        return len(self)


class Filter:
    """
    This is a test, it includes a code snippit that might include variables.
    When employed in rete, it replaces the variables, then executes the code.
    The code should evalute to a boolean result.

    If it does not evaluate to True, then the test fails.
    """

    def __init__(self, tmpl: str) -> None:
        self.tmpl = tmpl

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Filter) and self.tmpl == other.tmpl


class Bind:
    """
    This node binds the result of a code evaluation to a variable, which can
    then be used in subsequent patterns.

    TODO:
        - Could these use some form of partials to eliminate the need to do
          find replace for variable? Maybe save an arglist of vars and a
          partial that accepts bound values for the arg list. Could be faster.
    """

    def __init__(self, tmp: str, to: str):
        self.tmpl = tmp
        self.to = to
        assert is_var(self.to)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bind) and \
            self.tmpl == other.tmpl and self.to == other.to


class Token:
    """
    Tokens represent matches within the alpha and beta memories. The parent
    corresponds to the match that was extended to create the current token.
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

        if self.wme:
            self.wme.tokens.append(self)
        if self.parent:
            self.parent.children.append(self)

    def __repr__(self) -> str:
        return "<Token %s>" % self.wmes

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Token) and \
            self.parent == other.parent and self.wme == other.wme

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

        for child in self.children:
            child.delete_token_and_descendents()
        if (self.node and self.node.items and not
                isinstance(self.node, NccPartnerNode)):
            self.node.items.remove(self)
        if self.wme:
            self.wme.tokens.remove(self)
        if self.parent:
            self.parent.children.remove(self)
        if isinstance(self.node, NegativeNode):
            for jr in self.join_results:
                jr.wme.negative_join_results.remove(jr)
        elif isinstance(self.node, NccNode):
            for result_tok in self.ncc_results:
                if result_tok.wme:
                    result_tok.wme.tokens.remove(result_tok)
                if result_tok.parent:
                    result_tok.parent.children.remove(result_tok)
        elif isinstance(self.node, NccPartnerNode):
            if self.owner:
                self.owner.ncc_results.remove(self)
                if not self.owner.ncc_results and self.node.ncc_node:
                    for bchild in self.node.ncc_node.children:
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
