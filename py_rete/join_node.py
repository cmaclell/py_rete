from py_rete.common import ReteNode


class JoinNode(ReteNode):
    """
    A beta network class. Does the heavly lifting of joining two beta network
    paths.

    This class has an alpha memory connected to its right side, which triggers
    right_activations.

    The parent constitutes the left side (another node in the beta network),
    which triggers left_activations.

    The tests are a list of join node tests, corresponding to variables on the
    left and right sides that must be consistent.

    When the JoinNode is right activated, it checks the incoming wme against
    all the tokens in the parent (on the left side), using the tests. For
    every match, updated bindings are created and the children are activated.

    When the JoinNode is left activated, it checks the incoming token against
    the wmes from the alpha memory instead (essentially the opposite direction
    as above). Similarly, for matches, updated bindings are created and
    children are activated.

    The Has is used to make new variable bindings, but not sure what it
    represents.

    TODO:
        - Why does it get a has, or a pattern?
        - Consider using hashing in left and right activations, so only
          portions of the respective memories need to be searched. E.g.,
          memories might be indexed by the 8 constant/var patterns for
          patterns, which should reduce iteration substantially (but increase
          mem usage). See page 25 of Doorenbos thesis.
        - perform_join_test
            - Push the actual test evaluation into the TestAtJoinNode class, so
              it can be subclassed with other kinds of tests.
            - Currently only supports equality, maybe add support for other
              tests?
    """

    def __init__(self, children, parent, amem, tests, has):
        """
        :type children:
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :type has: Has
        """
        super(JoinNode, self).__init__(children=children, parent=parent)
        self.amem = amem
        self.tests = tests
        self.has = has

    def right_activation(self, wme):
        """
        Called when an element is added to the respective alpha memory.

        :type wme: rete.WME
        """
        for token in self.parent.items:
            if self.perform_join_test(token, wme):
                binding = self.make_binding(wme)
                for child in self.children:
                    child.left_activation(token, wme, binding)

    def left_activation(self, token):
        """
        Called when an element is added to the parent beta node.

        :type token: rete.Token
        """
        for wme in self.amem.items:
            if self.perform_join_test(token, wme):
                binding = self.make_binding(wme)
                for child in self.children:
                    child.left_activation(token, wme, binding)

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

    def make_binding(self, wme):
        """
        :type wme: WME
        """
        binding = {}
        for field, v in self.has.vars:
            val = getattr(wme, field)
            binding[v] = val
        return binding


class TestAtJoinNode:
    """
    This class stores information for testing if a token and wme are compatible
    within a join node.

    TODO:
        - Explore how to support other tests besides equality?
    """

    def __init__(self, field_of_arg1, condition_number_of_arg2, field_of_arg2):
        self.field_of_arg1 = field_of_arg1
        self.condition_number_of_arg2 = condition_number_of_arg2
        self.field_of_arg2 = field_of_arg2

    def __repr__(self):
        return "<TestAtJoinNode WME.%s=Condition%s.%s?>" % (
            self.field_of_arg1, self.condition_number_of_arg2,
            self.field_of_arg2)

    def __eq__(self, other):
        return isinstance(other, TestAtJoinNode) and \
            self.field_of_arg1 == other.field_of_arg1 and \
            self.field_of_arg2 == other.field_of_arg2 and \
            self.condition_number_of_arg2 == other.condition_number_of_arg2
