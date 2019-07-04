import copy
from py_rete.beta import BetaNode


class BindNode(BetaNode):

    kind = 'bind-node'

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
        TODO:
            - Rewrite code.replace to use something that does all the bindings
              with a single pass?

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
