import copy
from py_rete.beta import ReteNode


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

    def __init__(self, children, parent, tmpl, to):
        """
        :type children:
        :type parent: BetaNode
        :type to: str
        """
        super(BindNode, self).__init__(children=children, parent=parent)
        self.tmpl = tmpl
        self.bind = to

    def left_activation(self, token, wme, binding=None):
        """
        :type binding: dict
        :type wme: WME
        :type token: Token
        """
        code = self.tmpl
        all_binding = token.all_binding()
        all_binding.update(binding)
        for k in all_binding:
            code = code.replace(k, str(all_binding[k]))
        result = eval(code)
        binding[self.bind] = result
        for child in self.children:
            binding = copy.deepcopy(binding)
            child.left_activation(token, wme, binding)
