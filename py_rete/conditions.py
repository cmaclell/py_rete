from __future__ import annotations
from typing import TYPE_CHECKING
from itertools import chain

from py_rete.common import V

if TYPE_CHECKING:
    from typing import List
    from typing import Tuple
    from typing import Callable
    from typing import Any
    from py_rete.common import WME


class BaseCond(tuple):
    """Base Conditional"""

    def __new__(cls, *args):
        return super().__new__(cls, args)

    def __repr__(self):
        return "{}{}".format(self.__class__.__name__, super().__repr__())


class ComposableCond:
    """A Mixin for making compositional mixins"""

    def __and__(self, other: ComposableCond):
        if isinstance(self, AND) and isinstance(other, AND):
            return AND(*[x for x in chain(self, other)])
        elif isinstance(self, AND):
            return AND(*[x for x in self]+[other])
        elif isinstance(other, AND):
            return AND(*[self]+[x for x in other])
        else:
            return AND(self, other)

    def __or__(self, other: ComposableCond):
        if isinstance(self, OR) and isinstance(other, OR):
            return OR(*[x for x in chain(self, other)])
        elif isinstance(self, OR):
            return OR(*[x for x in self]+[other])
        elif isinstance(other, OR):
            return OR(*[self]+[x for x in other])
        else:
            return OR(self, other)

    def __invert__(self):
        return NOT(self)


class AND(BaseCond, ComposableCond):
    pass


class OR(BaseCond, ComposableCond):
    pass


class NOT(BaseCond, ComposableCond):
    pass


class TEST(BaseCond, ComposableCond):
    pass


class EXISTS(BaseCond, ComposableCond):
    pass


class FORALL(BaseCond, ComposableCond):
    pass


class Cond(ComposableCond):
    """
    Essentially a pattern/condition to match, can have variables.
    """

    def __init__(self, identifier: Any, attribute: Any, value: Any):
        """
        Constructor.

        (<x> ^self <y>)
        repr as:
        ('?x', 'self', '?y')

        :type value: Var or str
        :type attribute: Var or str
        :type identifier: Var or str
        """
        self.identifier = identifier
        self.attribute = attribute
        self.value = value

    def __repr__(self):
        return "(%s ^%s %s)" % (self.identifier, self.attribute, self.value)

    def __eq__(self, other: object):
        if not isinstance(other, Cond):
            return False
        return (self.__class__ == other.__class__
                and self.identifier == other.identifier
                and self.attribute == other.attribute
                and self.value == other.value)

    def __hash__(self):
        return hash(tuple(['cond', self.identifier, self.attribute,
                           self.value]))

    @property
    def vars(self) -> List[Tuple[str, V]]:
        """
        Returns a list of variables with the labels for the slots they occupy.

        :rtype: list
        """
        ret = []
        for field in ['identifier', 'attribute', 'value']:
            v = getattr(self, field)
            if isinstance(v, V):
                ret.append((field, v))
        return ret

    def contain(self, v: V) -> str:
        """
        Checks if a variable is in a pattern. Returns field if it is, otherwise
        an empty string.

        TODO:
            - Why does this return an empty string on failure?

        :type v: Var
        :rtype: bool
        """
        assert isinstance(v, V)

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
            if isinstance(v, V):
                continue
            if v != getattr(w, f):
                return False
        return True


class Neg(Cond):
    """
    A negated pattern.

    TODO:
        - Does this need test implemented?
    """

    def __repr__(self):
        return "-(%s %s %s)" % (self.identifier, self.attribute, self.value)

    def __hash__(self):
        return hash(tuple(['neg', self.identifier, self.attribute,
                           self.value]))


# class AndCond(list):
#     """
#     Essentially an AND, a list of conditions.
#
#     TODO:
#         - Implement an OR equivelent, that gets compiled when added to a
#           network into multiple rules.
#         - Need somewhere to store right hand sides? What to do when rules
#         fire.
#           Might need an actual rule or production class.
#     """
#
#     def __init__(self, *args: List[Cond]) -> None:
#         self.extend(args)


class Ncc(AND):
    """
    Essentially a negated AND, a negated list of conditions.
    """

    def __repr__(self):
        return "-%s" % super(Ncc, self).__repr__()

    @property
    def number_of_conditions(self) -> int:
        return len(self)

    def __hash__(self):
        return hash(tuple(['ncc', tuple(self)]))


class Filter:
    """
    This is a test, it includes a code snippit that might include variables.
    When employed in rete, it replaces the variables, then executes the code.
    The code should evalute to a boolean result.

    If it does not evaluate to True, then the test fails.
    """

    def __init__(self, tmpl: Callable) -> None:
        self.tmpl = tmpl

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Filter) and self.tmpl == other.tmpl

    def __hash__(self):
        return hash(tuple(['filter', self.tmpl]))


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
        assert isinstance(self.to, V)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bind) and \
            self.tmpl == other.tmpl and self.to == other.to

    def __hash__(self):
        return hash(tuple(['bind', self.tmpl, self.to]))
