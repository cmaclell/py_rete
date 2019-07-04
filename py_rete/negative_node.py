from py_rete.common import Token
from py_rete.beta import BetaNode


class NegativeJoinResult:
    """
    A new class to store the result of a negative join. Similar to a token, it
    is owned by a token.
    """

    def __init__(self, owner, wme):
        """
        :type wme: rete.WME
        :type owner: rete.Token
        """
        self.owner = owner
        self.wme = wme


class NegativeNode(BetaNode):
    """
    A beta network class that only passes on tokens when there is no match.

    The left activation is called by the parent beta node.
    The right activation is called from the alpha network (amem).
    Test are similar to those that appear in JoinNode

    TODO:
        - should negative node be a subclass of JoinNode?
            - perform_join_test is identical to JoinNode
            - doesn't have Has, not sure why JoinNode does though.
        - should this have a kind?

    """

    def __init__(self, children=None, parent=None, amem=None, tests=None):
        """
        :type children:
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        """
        super(NegativeNode, self).__init__(children=children, parent=parent)
        self.items = []
        self.amem = amem
        self.tests = tests if tests else []

    def left_activation(self, token, wme, binding=None):
        """
        :type wme: rete.WME
        :type token: rete.Token
        :type binding: dict
        """
        new_token = Token(token, wme, self, binding)
        self.items.append(new_token)
        for item in self.amem.items:
            if self.perform_join_test(new_token, item):
                jr = NegativeJoinResult(new_token, item)
                new_token.join_results.append(jr)
                item.negative_join_result.append(jr)
        if not new_token.join_results:
            for child in self.children:
                child.left_activation(new_token, None)

    def right_activation(self, wme):
        """
        :type wme: rete.WME
        """
        for t in self.items:
            if self.perform_join_test(t, wme):
                if not t.join_results:
                    # TODO: According to doorenbos this should be
                    # delete_descendents_of_token instead (pg. 43).
                    # write tests to confirm.
                    Token.delete_descendents_of_token(t)
                    # Token.delete_token_and_descendents(t)
                jr = NegativeJoinResult(t, wme)
                t.join_results.append(jr)
                wme.negative_join_result.append(jr)

    def perform_join_test(self, token, wme):
        """
        :type token: rete.Token
        :type wme: rete.WME
        """
        for this_test in self.tests:
            arg1 = getattr(wme, this_test.field_of_arg1)
            wme2 = token.wmes[this_test.condition_number_of_arg2]
            arg2 = getattr(wme2, this_test.field_of_arg2)
            if arg1 != arg2:
                return False
        return True
