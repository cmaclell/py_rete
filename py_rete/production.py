from __future__ import annotations
from typing import TYPE_CHECKING
from functools import update_wrapper
import inspect

from py_rete.conditions import BaseCond
from py_rete.conditions import Cond
from py_rete.conditions import Ncc
from py_rete.conditions import Filter
from py_rete.conditions import Bind
from py_rete.conditions import AND
from py_rete.fact import Fact

if TYPE_CHECKING:
    from typing import Optional
    from typing import Callable
    from typing import List
    from py_rete.pnode import PNode


def get_rete_conds(it):
    for ele in it:
        if isinstance(ele, (Cond, Ncc, Bind, Filter)):
            yield ele
        elif isinstance(ele, Fact):
            for cond in ele.conds:
                yield cond
        elif isinstance(ele, AND):
            for cond in get_rete_conds(ele):
                yield cond


class Production(BaseCond):
    """
    A production rule in py_rete. It is comprised of conditions and a function
    to execute once all conditions are bound.

    TODO:
        - What do we do with empty conditions?
        - What do we do with empty effects? Currently just pass None, can rules
          ever have empty effects? Maybe ok, if they have more complicated
          effects.
    """
    __wrapped__: Optional[Callable]
    id: Optional[str]
    p_nodes: List[PNode]

    def __new__(cls, *args):
        obj = super().__new__(cls, *args)
        obj.__wrapped__ = None
        obj._wrapped_args = []
        obj._rete_net = None

        obj.id = None
        obj.p_nodes = []

        return obj

    @property
    def activations(self):
        for node in self.p_nodes:
            for token in node.activations:
                yield token

    def get_rete_conds(self):
        return list(get_rete_conds(self))

    def __call__(self, *args, **kwargs):

        # Need to see if we've already wrapped a function, if not, then do so.
        if self.__wrapped__ is None:
            if not args:
                raise AttributeError("Apply Production as a decorator around a"
                                     " function to create a production.")
            else:
                func = args[0]

                signature = inspect.signature(func)
                if not any(p.kind == inspect.Parameter.VAR_KEYWORD
                           for p in signature.parameters.values()):
                    # There is not **kwargs defined. Pass only the defined
                    # names.
                    self._wrapped_args = set(signature.parameters.keys())

                return update_wrapper(self, func)

        else:
            if self._wrapped_args:
                kwargs = {k: v for k, v in kwargs.items()
                          if k in self._wrapped_args}

            # Inject the working rete_net pointer
            g = self.__wrapped__.__globals__
            sentinel = object()
            old_value = g.get('rete_net', sentinel)
            g['rete_net'] = self._rete_net

            try:
                result = self.__wrapped__(*args, **kwargs)
            finally:
                if old_value is sentinel:
                    del g['rete_net']
                else:
                    g['rete_net'] = old_value

            return result

    def __repr__(self) -> str:
        if self.__wrapped__ is None:
            raise ValueError("Not instantiated as a decorator.")

        signature = inspect.signature(self.__wrapped__)
        return "IF {} THEN {}{}".format(self[0].__repr__(),
                                        self.__wrapped__.__name__,
                                        signature)

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Production) and self.id == other.id)

    def __hash__(self):
        return hash("{}-{}".format(self.__class__.__name__, self.id))

    # def get_effects(self, token: Token):
    #     if self.rhs:
    #         return self.rhs.bind(token.binding)
    #     return []
