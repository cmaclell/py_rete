from __future__ import annotations
from typing import TYPE_CHECKING
from itertools import chain

from py_rete.conditions import ComposableCond
from py_rete.conditions import Cond
from py_rete.common import gen_variable
from py_rete.common import WME
from py_rete.common import V

if TYPE_CHECKING:
    from typing import Generator
    from typing import Optional


class Fact(dict, ComposableCond):

    def __init__(self, *args, **kwargs) -> None:
        self.id: Optional[str] = None
        self.gen_var = gen_variable()

        self.update(dict(chain(enumerate(args), kwargs.items())))

        if '__fact_type__' in self:
            raise ValueError("`__fact_type__` cannot be used, it is a reserved"
                             " keyword for matching type internally.")

    def duplicate(self) -> Fact:
        """
        Returns a copy of the fact without the ID set.

        This is basically a shallow copy, if the fact contains other facts,
        those are not copied.
        """
        new = Fact()
        new.update(self)
        return new

    @property
    def conds(self) -> Generator[Cond, None, None]:
        if self.id is None:
            fact_id = self.gen_var
        else:
            fact_id = self.id

        # Put the type condition first as it should be a quick way to narrow
        # things down.
        # TODO Could do something with inheritance here, where we do an OR on
        # type. Alternatively, when we add facts to the network as wmes they
        # get all of their parent classes.
        yield Cond(fact_id, '__fact_type__', self.__class__)

        for k in self:
            yield Cond(fact_id, k, self[k])

    @property
    def wmes(self) -> Generator[WME, None, None]:
        if self.id is None:
            raise ValueError("No id assigned to fact, add to network first.")

        for k in self:
            if isinstance(k, V) or isinstance(self[k], V):
                raise ValueError("Facts converted into wmes cannot have"
                                 " variables.")

        yield WME(self.id, '__fact_type__', self.__class__)

        for k in self:
            yield WME(self.id, k, self[k])

    def __repr__(self):
        kvs = []
        for k in self:
            kvs.append("{}={}".format(k, self[k]))

        return "{}({})".format(self.__class__.__name__, ", ".join(kvs))

    def __hash__(self):
        return hash("{}-{}".format(self.__class__.__name__, self.id))

    def __eq__(self, other):
        if self.id != other.id:
            return False

        keys = set()
        keys.update(self)
        keys.update(other)

        for k in keys:
            if k not in self:
                return False
            if k not in other:
                return False
            if self[k] != other[k]:
                return False

        return True
