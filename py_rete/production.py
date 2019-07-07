from __future__ import annotations
from typing import List
from typing import Tuple
from typing import Optional

from py_rete.common import is_var
from py_rete.common import WME


class Cond:
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


class AndCond(list):
    """
    Essentially an AND, a list of conditions.

    TODO:
        - Implement an OR equivelent, that gets compiled when added to a
          network into multiple rules.
        - Need somewhere to store right hand sides? What to do when rules fire.
          Might need an actual rule or production class.
    """

    def __init__(self, *args: List[Cond]) -> None:
        self.extend(args)


class Ncc(AndCond):
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

    def __init__(self, tmpl: str) -> None:
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
        assert is_var(self.to)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bind) and \
            self.tmpl == other.tmpl and self.to == other.to

    def __hash__(self):
        return hash(tuple(['bind', self.tmpl, self.to]))


class Production:
    """
    A left and a right side
    """

    def __init__(self, lhs: AndCond, add_effects=None,
                 del_effects=None) -> None:
        self.lhs = lhs
        self.add_effects = add_effects
        self.del_effects = del_effects

    def __repr__(self) -> str:
        return (repr(self.lhs) + " --> Add:" + repr(self.add_effects) + " Del:"
                + repr(self.del_effects))

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Production) and self.lhs == other.lhs and
                self.add_effects == other.add_effects and self.del_effects ==
                other.del_effects)

    def __hash__(self):
        return hash(tuple(self.lhs))
