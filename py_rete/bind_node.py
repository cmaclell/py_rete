from __future__ import annotations
from typing import TYPE_CHECKING
import inspect
import copy
from py_rete.beta import ReteNode
from py_rete.common import V

if TYPE_CHECKING:
    from py_rete.network import ReteNetwork


class BindNode(ReteNode):
    """
    A beta network class. This class stores a code snipit, with variables in
    it. It gets all the bindings from the incoming token, updates them with the
    current bindings, binds the result to the target variable (to), then
    activates its children with the updated bindings.

    TODO:
        - Rewrite code.replace to use something that does all the bindings
          with a single pass?
        - Use functions/partials instead of string code snipits, with arg
          lists that contain variables or constants
    """

    def __init__(self, children, parent, tmpl, to, rete: ReteNetwork):
        """
        :type children:
        :type parent: BetaNode
        :type to: str
        """
        super(BindNode, self).__init__(children=children, parent=parent)
        self.tmpl = tmpl
        self.bind = to
        self._rete_net = rete

    def get_function_result(self, token, wme, binding=None):
        func = self.tmpl
        all_binding = token.all_binding()
        if binding:
            all_binding.update(binding)

        args = inspect.getfullargspec(func)[0]

        # args = {arg: self._rete_net if arg == 'net' else all_binding[V(arg)]
        #         for arg in args}

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
        if binding is None:
            binding = {}
        binding[self.bind] = self.get_function_result(token, wme, binding)

        for child in self.children:
            binding = copy.deepcopy(binding)
            child.left_activation(token, wme, binding)
