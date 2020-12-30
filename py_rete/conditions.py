from __future__ import annotations
from typing import TYPE_CHECKING
from itertools import chain

from py_rete.common import V

if TYPE_CHECKING:
    from typing import List
    from typing import Union
    from typing import Tuple
    from typing import Callable
    from typing import Hashable
    from py_rete.common import WME


class ConditionalElement():
    """
    A single conditional element (e.g., Test, Condition, Neg, Bind). Does not
    include list conditionals. Used for type checking primarily.
    """
    pass


class ConditionalList(tuple):
    """
    A conditional that consists of a list of other conditionals.
    """

    def __new__(cls, *args: List[Union[ConditionalList, ConditionalElement]]):
        return super().__new__(cls, args)

    def __repr__(self):
        return "{}{}".format(self.__class__.__name__, super().__repr__())

    def __hash__(self):
        return hash(tuple([self.__class__.__name__, tuple(self)]))


class ComposableCond:
    """
    A Mixin for making a conditional compositional using bitwise operators.
    """

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


class AND(ConditionalList, ComposableCond):
    pass


class OR(ConditionalList, ComposableCond):
    pass


class NOT(ConditionalList, ComposableCond):
    pass


# class EXISTS(ConditionalElement, ComposableCond):
#     pass
#
#
# class FORALL(ConditionalElement, ComposableCond):
#     pass


class Cond(ConditionalElement, ComposableCond):
    """
    Essentially a pattern/condition to match, can have variables.
    """

    def __init__(self, identifier: Hashable, attribute: Hashable,
                 value: Hashable):
        """
        Specifies a pattern that consists of an identifier, attribute, and
        value. Note, these should be hashable values.

        Repr as: (<identifier> ^<attribute> <value>)
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


class Ncc(ConditionalList, ComposableCond):
    """
    Essentially a negated AND, a negated list of conditions.
    """
    def __repr__(self):
        return "-{}".format(super(Ncc, self).__repr__())

    @property
    def number_of_conditions(self) -> int:
        return len(self)

    def __hash__(self):
        return hash(tuple(['ncc', tuple(self)]))


class Filter(ConditionalElement, ComposableCond):
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


class Bind(ConditionalElement, ComposableCond):
    """
    This node binds the result of a code evaluation to a variable, which can
    then be used in subsequent patterns.
    """

    def __init__(self, tmp: Callable, to: V):
        self.tmpl = tmp
        self.to = to
        assert isinstance(self.to, V)

    def __repr__(self):
        return "Bind({},{})".format(repr(self.tmpl), repr(self.to))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bind) and \
            self.tmpl == other.tmpl and self.to == other.to

    def __hash__(self):
        return hash(tuple(['bind', self.tmpl, self.to]))
