from __future__ import annotations
from typing import TYPE_CHECKING
import inspect

from py_rete.beta import ReteNode
from py_rete.common import V

if TYPE_CHECKING:
    from py_rete.network import ReteNetwork


class FilterNode(ReteNode):
    """
    A beta network class. Takes a code snipit, replaces variables with bound
    values, executes it. If the code evaluates to True (boolean), then it
    activates the children with the token/wme

    TODO:
        - explore use of functions/partials instead of string code snipits
    """

    def __init__(self, children, parent, tmpl, rete: ReteNetwork):
        """
        :type children:
        :type parent: BetaNode
        :type bind: str
        """
        super(FilterNode, self).__init__(children=children, parent=parent)
        self.tmpl = tmpl
        self._rete_net = rete

    def get_function_result(self, token, wme, binding=None):
        func = self.tmpl
        all_binding = token.all_binding()
        if binding:
            all_binding.update(binding)

        args = inspect.getfullargspec(func)[0]

        # binds net and if a variable is bound to a fact id then it gets the
        # Fact itself
        args = {arg: self._rete_net if arg == 'net' else
                self._rete_net.facts[all_binding[V(arg)]] if
                all_binding[V(arg)] in self._rete_net.facts else
                all_binding[V(arg)] for arg in args}

        return func(**args)

    def left_activation(self, token, wme, binding=None):
        """
        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        result = self.get_function_result(token, wme, binding)
        if bool(result):
            for child in self.children:
                child.left_activation(token, wme, binding)
