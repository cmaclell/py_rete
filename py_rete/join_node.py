from __future__ import annotations
from typing import TYPE_CHECKING

from py_rete.common import Token
from py_rete.common import WME
from py_rete.alpha import AlphaMemory
from py_rete.beta import ReteNode

if TYPE_CHECKING:
    from typing import List
    from py_rete.beta import BetaMemory


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
        - perform_join_test
            - Push the actual test evaluation into the TestAtJoinNode class, so
              it can be subclassed with other kinds of tests.
            - Currently only supports equality, maybe add support for other
              tests?
    """
    parent: BetaMemory
    children: List[BetaMemory]

    def __init__(self, amem, tests, condition, **kwargs):
        """
        :type children:
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :type has: Has
        """
        super(JoinNode, self).__init__(**kwargs)
        self.amem: AlphaMemory = amem
        self.tests: List[TestAtJoinNode] = tests
        self.condition = condition
        self.nearest_ancestor_with_same_amem = None

    @property
    def amem_recently_nonempty(self) -> bool:
        return len(self.amem.items) == 1

    @property
    def parent_recently_nonempty(self) -> bool:
        return len(self.parent.items) == 1

    @property
    def right_unlinked(self) -> bool:
        return len(self.parent.items) == 0

    @property
    def left_unlinked(self) -> bool:
        return len(self.amem.items) == 0

    def update_nearest_ancestor_with_same_amem(self):
        ancestor = self.parent.find_nearest_ancestor_with_same_amem(self.amem)
        self.nearest_ancestor_with_same_amem = ancestor

    def find_nearest_ancestor_with_same_amem(self, amem: AlphaMemory):
        if self.amem == amem:
            return self
        return self.parent.find_nearest_ancestor_with_same_amem(amem)

    def right_activation(self, wme: WME):
        """
        Called when an element is added to the respective alpha memory.

        TODO:
            - Explore typing, parent and parent.items should not be optional.

        :type wme: rete.WME
        """
        if self.amem_recently_nonempty:
            self.relink_to_beta_memory()
            if not self.parent.items:
                self.amem.successors.remove(self)
        for token in self.parent.items:
            if self.perform_join_test(token, wme):
                binding = self.make_binding(wme)
                for child in self.children:
                    child.left_activation(token, wme, binding)

    def relink_to_alpha_memory(self):
        """
        TODO:
            - test and verify
        """
        ancestor = self.nearest_ancestor_with_same_amem
        while ancestor and ancestor.right_unlinked:
            ancestor = ancestor.nearest_ancestor_with_same_amem
        if ancestor:
            try:
                loc = self.amem.successors.index(ancestor)
            except ValueError:
                loc = -1
            self.amem.successors.insert(loc+1, self)
        else:
            self.amem.successors.insert(0, self)

    def relink_to_beta_memory(self):
        """
        TODO:
            - test and verify
        """
        self.parent.children.append(self)

    def left_activation(self, token):
        """
        Called when an element is added to the parent beta node.

        :type token: rete.Token
        """
        if self.parent_recently_nonempty:
            self.relink_to_alpha_memory()
            if not self.amem.items:
                self.parent.children.remove(self)
        for wme in self.amem.items:
            if self.perform_join_test(token, wme):
                binding = self.make_binding(wme)
                for child in self.children:
                    child.left_activation(token=token, wme=wme,
                                          binding=binding)

    def perform_join_test(self, token: Token, wme: WME) -> bool:
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
        for field, v in self.condition.vars:
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
