from typing import Generator
from typing import Dict
from typing import Tuple
from typing import List
from typing import Set
from typing import Union
import random
from itertools import product

from py_rete.bind_node import BindNode
from py_rete.filter_node import FilterNode
from py_rete.ncc_node import NccPartnerNode
from py_rete.ncc_node import NccNode
from py_rete.negative_node import NegativeNode
from py_rete.join_node import TestAtJoinNode
from py_rete.join_node import JoinNode
from py_rete.pnode import PNode
from py_rete.common import WME
from py_rete.common import Token
from py_rete.common import V
from py_rete.common import Match
from py_rete.fact import Fact
from py_rete.alpha import AlphaMemory
from py_rete.beta import ReteNode
from py_rete.beta import BetaMemory
from py_rete.conditions import Cond
from py_rete.conditions import Ncc
from py_rete.conditions import Neg
from py_rete.conditions import Filter
from py_rete.conditions import Bind
from py_rete.production import Production


class ReteNetwork:
    """
    TODO:
        - Add a top level function to get teh current set of productions that
          match
            - Need to track the pnodes somewhere?
        - Add top level function to fire all matching productions
          (simultaneously), a cycle in the wme.
        - Give WMEs a pointer for tracking their dependencies/support, if it
          goes away they need to be retracted.
    """

    def __init__(self):
        self.alpha_hash: Dict[Tuple[str, str, str], AlphaMemory] = {}
        self.beta_root = ReteNode()
        self.buf = None
        self.pnodes: List[PNode] = []
        self.working_memory: Set[WME] = set()
        self.facts: Dict[str, Fact] = {}
        self.fact_counter = 0
        self.production_counter = 0
        self.productions: Set[Production] = set()

    def run(self, n=10):
        while n > 0:
            matches = list(self.matches)
            if len(matches) <= 0:
                break
            match = random.choice(matches)
            match.fire()
            n -= 1

    def __repr__(self):
        output = 'Productions:\n'
        for p in self.productions:
            output += "{}: {}\n".format(p.id, p)
        output += "\nFacts:\n"
        for fid in self.facts:
            copy = self.facts[fid].duplicate()
            for k in copy:
                if isinstance(copy[k], Fact):
                    copy[k] = copy[k].id
            output += "{}: {}\n".format(fid, copy)
        output += "\nWMEs:\n"
        for wme in self.working_memory:
            output += "{}\n".format(wme)
        return output

    def add_fact(self, fact: Fact) -> None:
        """
        Adds a fact to the network and returns the fact id.
        """
        if fact.id is not None:
            raise ValueError("Fact already has an id, cannot add")

        copy = fact.duplicate()
        for k in copy:
            if isinstance(copy[k], Fact):
                if copy[k].id is None:
                    self.add_fact(copy[k])
                copy[k] = copy[k].id

        fact.id = "f-{}".format(self.fact_counter)
        copy.id = fact.id
        self.fact_counter += 1

        self.facts[fact.id] = fact

        for wme in copy.wmes:
            self.add_wme(wme)

    def remove_fact(self, fact: Fact) -> None:
        """
        Removes a fact from the network.
        """
        if fact.id is None or fact.id not in self.facts:
            raise ValueError("Fact has no id or does not exist in network.")

        if fact.id in self.facts:
            del self.facts[fact.id]
            self.remove_wme_by_fact_id(fact.id)

        fact.id = None

    def get_fact_by_id(self, fact_id: str) -> Fact:
        return self.facts[fact_id]

    def update_fact(self, fact: Fact) -> None:
        """
        Todo: Figure out a fancy way to only update part of the fact
        """
        self.remove_fact(fact)
        self.add_fact(fact)

    def remove_wme_by_fact_id(self, identifier: str) -> None:
        to_remove = [wme for wme in self.working_memory if wme.identifier ==
                     identifier]
        for wme in to_remove:
            self.remove_wme(wme)

    @property
    def new_matches(self) -> Generator[Tuple[Production, Token], None, None]:
        for pnode in self.pnodes:
            for t in pnode.new:
                yield Match(pnode.production, t)

    @property
    def matches(self) -> Generator[Tuple[Production, Token], None, None]:
        for pnode in self.pnodes:
            for t in pnode.activations:
                yield Match(pnode.production, t)

    @property
    def wmes(self) -> Set[WME]:
        return self.working_memory

    def add_production(self, prod: Production) -> None:
        """
        Adds a production to the ReteNetwork.
        """
        if prod.id is not None:
            raise ValueError("Production already has an id, cannot add")

        prod.id = "p-{}".format(self.production_counter)
        prod._rete_net = self

        self.production_counter += 1
        self.productions.add(prod)

        for conds in prod.get_rete_conds():
            current_node = self.build_or_share_network_for_conditions(
                self.beta_root, conds, [])
            p_node = self.build_or_share_p(current_node, prod)

            self.pnodes.append(p_node)
            prod.p_nodes.append(p_node)

    def remove_production(self, prod: Production) -> None:
        """
        Removes a pnode from the network
        """
        if prod.id is None:
            raise ValueError("Production has no id, cannot remove.")

        # Remove fact
        self.productions.remove(prod)

        for pnode in prod.p_nodes:
            self.delete_node_and_any_unused_ancestors(pnode)
            self.pnodes.remove(pnode)

        prod.id = None
        prod.p_nodes = []

    def add_wme(self, wme) -> None:
        if wme in self.working_memory:
            return

        keys = product([wme.identifier, '*'],
                       [wme.attribute, '*'],
                       [wme.value, '*'])

        for key in keys:
            if key in self.alpha_hash:
                self.alpha_hash[key].activation(wme)

        self.working_memory.add(wme)

    def remove_wme(self, wme: WME):
        """
        :type wme: WME
        """
        for am in wme.amems:
            am.items.remove(wme)
            if not am.items:
                for node in am.successors:
                    if isinstance(node, (JoinNode, NegativeNode)):
                        # TODO fix type error, triggered by negativenode, which
                        # is also a betamemory, it confuses mypy because of
                        # multiple inheritance
                        node.parent.children.remove(node)  # type: ignore

        for t in wme.tokens:
            t.delete_token_and_descendents()

        for jr in wme.negative_join_results:
            jr.owner.join_results.remove(jr)
            if not jr.owner.join_results:
                if jr.owner.node and jr.owner.node.children is not None:
                    for child in jr.owner.node.children:
                        child.left_activation(jr.owner, None)

        self.working_memory.remove(wme)

    def dump(self):
        self.buf = ""
        self.buf += 'digraph {\n'
        self.dump_beta(self.beta_root)
        # for k in self.alpha_hash:
        #     self.dump_alpha(self.alpha_hash[k])
        # self.dump_alpha(self.alpha_hash)
        # self.dump_alpha2beta(self.alpha_hash)
        self.buf += '}'
        return self.buf

    def dump_alpha(self, node):
        """
        :type node: ConstantTestNode
        """
        # if node == self.alpha_root:
        #     self.buf += "    subgraph cluster_0 {\n"
        #     self.buf += "    label = alpha\n"
        for child in node.children:
            self.buf += '    "%s" -> "%s";\n' % (node.dump(), child.dump())
            self.dump_alpha(child)
        # if node == self.alpha_root:
        #     self.buf += "    }\n"

    def dump_alpha2beta(self, node):
        """
        :type node: ConstantTestNode
        """
        if node.amem:
            for child in node.amem.successors:
                self.buf += '    "%s" -> "%s";\n' % (node.dump(), child.dump())
        for child in node.children:
            self.dump_alpha2beta(child)

    def dump_beta(self, node):
        """
        :type node: BetaNode
        """
        if node == self.beta_root:
            self.buf += "    subgraph cluster_1 {\n"
            self.buf += "    label = beta\n"
        if isinstance(node, NccPartnerNode):
            self.buf += '    "%s" -> "%s";\n' % (node.dump(),
                                                 node.ncc_node.dump())
        for child in node.children:
            self.buf += '    "%s" -> "%s";\n' % (node.dump(), child.dump())
            self.dump_beta(child)
        if node == self.beta_root:
            self.buf += "    }\n"

    def build_or_share_alpha_memory(self, condition):
        """
        :type condition: Condition
        :rtype: AlphaMemory
        """
        id_test = '*'
        attr_test = '*'
        value_test = '*'

        if not isinstance(condition.identifier, V):
            id_test = condition.identifier
        if not isinstance(condition.attribute, V):
            attr_test = condition.attribute
        if not isinstance(condition.value, V):
            value_test = condition.value

        key = (id_test, attr_test, value_test)

        if key in self.alpha_hash:
            return self.alpha_hash[key]

        self.alpha_hash[key] = AlphaMemory()
        self.alpha_hash[key].key = key

        for w in self.working_memory:
            if condition.test(w):
                self.alpha_hash[key].activation(w)

        return self.alpha_hash[key]

    @classmethod
    def get_join_tests_from_condition(cls, c: Cond,
                                      earlier_conds: List[Cond]
                                      ) -> List[TestAtJoinNode]:
        """
        :type c: Cond
        :type earlier_conds: List of Cond
        :rtype: list of TestAtJoinNode
        """
        result = []
        for field_of_v, v in c.vars:
            for idx, cond in enumerate(earlier_conds):
                if isinstance(cond, (Neg, Ncc, Bind, Filter)):
                    continue
                field_of_v2 = cond.contain(v)
                if not field_of_v2:
                    continue
                t = TestAtJoinNode(field_of_v, idx, field_of_v2)
                result.append(t)
        return result

    def build_or_share_join_node(self, parent: BetaMemory, amem: AlphaMemory,
                                 tests: List[TestAtJoinNode], condition: Cond
                                 ) -> JoinNode:
        """
        :type condition: Cond
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :rtype: JoinNode
        """
        for child in parent.all_children:
            if (type(child) == JoinNode and child.amem == amem and
                    child.tests == tests and child.condition == condition):
                return child
        node = JoinNode(children=[], parent=parent, amem=amem, tests=tests,
                        condition=condition)
        parent.children.append(node)
        parent.all_children.append(node)
        amem.successors.append(node)
        amem.reference_count += 1
        node.update_nearest_ancestor_with_same_amem()
        if not parent.items:
            amem.successors.remove(node)
        elif not amem.items:
            parent.children.remove(node)

        return node

    def build_or_share_negative_node(self, parent: JoinNode, amem: AlphaMemory,
                                     tests: List[TestAtJoinNode],
                                     condition: Neg) -> NegativeNode:
        """
        :type parent: BetaNode
        :type amem: AlphaMemory
        :type tests: list of TestAtJoinNode
        :rtype: JoinNode
        """

        for child in parent.children:
            if (isinstance(child, NegativeNode) and child.amem == amem and
                    child.tests == tests):
                return child
        node = NegativeNode(parent=parent, amem=amem, tests=tests,
                            condition=condition)
        parent.children.append(node)
        amem.successors.append(node)

        amem.reference_count += 1
        node.update_nearest_ancestor_with_same_amem()
        self.update_new_node_with_matches_from_above(node)
        if not node.items:
            amem.successors.remove(node)

        return node

    def build_or_share_beta_memory(self, parent: JoinNode) -> BetaMemory:
        """
        :type parent: JoinNode
        :rtype: BetaMemory
        """
        for child in parent.children:
            # if isinstance(child, BetaMemory):  # Don't include subclasses
            if type(child) == BetaMemory:
                return child
        node = BetaMemory(parent=parent)
        parent.children.append(node)
        # dummy top beta memory
        if parent == self.beta_root:
            node.items.append(Token(None, None))
        self.update_new_node_with_matches_from_above(node)
        return node

    def build_or_share_p(self, parent, prod):
        """
        :type kwargs:
        :type parent: BetaNode
        :rtype: PNode
        """
        for child in parent.children:
            if isinstance(child, PNode):
                return child
        node = PNode(production=prod, parent=parent)
        parent.children.append(node)
        if parent == self.beta_root:
            node.left_activation(None, None)
        self.update_new_node_with_matches_from_above(node)
        return node

    def build_or_share_ncc_nodes(self, parent: JoinNode, ncc: Ncc,
                                 earlier_conds: List[Cond]
                                 ) -> NccNode:
        """
        :type earlier_conds: Rule
        :type ncc: Ncc
        :type parent: BetaNode
        """
        bottom_of_subnetwork = self.build_or_share_network_for_conditions(
            parent, ncc, earlier_conds)
        for child in parent.children:
            if (isinstance(child, NccNode) and child.partner.parent ==
                    bottom_of_subnetwork):
                return child

        ncc_partner = NccPartnerNode(parent=bottom_of_subnetwork)
        ncc_node = NccNode(partner=ncc_partner, children=[], parent=parent)
        ncc_partner.ncc_node = ncc_node
        parent.children.insert(0, ncc_node)
        bottom_of_subnetwork.children.append(ncc_partner)
        ncc_partner.number_of_conditions = ncc.number_of_conditions
        self.update_new_node_with_matches_from_above(ncc_node)
        self.update_new_node_with_matches_from_above(ncc_partner)
        return ncc_node

    def build_or_share_filter_node(self, parent, f):
        """
        :type f: Filter
        :type parent: BetaNode
        """
        for child in parent.children:
            if isinstance(child, FilterNode) and child.tmpl == f.tmpl:
                return child
        node = FilterNode([], parent, f.tmpl, self)
        parent.children.append(node)
        return node

    def build_or_share_bind_node(self, parent, b):
        """
        :type b: Bind
        :type parent: BetaNode
        """
        for child in parent.children:
            if isinstance(child, BindNode) and child.tmpl == b.tmpl \
                    and child.bind == b.to:
                return child
        node = BindNode([], parent, b.tmpl, b.to, self)
        parent.children.append(node)
        return node

    def build_or_share_network_for_conditions(self, parent,
                                              rule: Union[Ncc, List[Cond]],
                                              earlier_conds: List[Cond]):
        """
        :type earlier_conds: list of BaseCondition
        :type parent: BetaNode
        :type rule: Rule
        """
        current_node = parent
        conds_higher_up = earlier_conds
        for cond in rule:
            if isinstance(cond, Cond) and not isinstance(cond, Neg):
                current_node = self.build_or_share_beta_memory(current_node)
                tests = self.get_join_tests_from_condition(cond,
                                                           conds_higher_up)
                am = self.build_or_share_alpha_memory(cond)
                current_node = self.build_or_share_join_node(current_node, am,
                                                             tests, cond)
            elif isinstance(cond, Neg):
                tests = self.get_join_tests_from_condition(cond,
                                                           conds_higher_up)
                am = self.build_or_share_alpha_memory(cond)
                current_node = self.build_or_share_negative_node(current_node,
                                                                 am, tests,
                                                                 cond)
            elif isinstance(cond, Ncc):
                current_node = self.build_or_share_ncc_nodes(current_node,
                                                             cond,
                                                             conds_higher_up)
            elif isinstance(cond, Filter):
                current_node = self.build_or_share_filter_node(current_node,
                                                               cond)
            elif isinstance(cond, Bind):
                current_node = self.build_or_share_bind_node(current_node,
                                                             cond)
            conds_higher_up.append(cond)
        return current_node

    def update_new_node_with_matches_from_above(self, new_node):
        """
        :type new_node: BetaNode
        """
        # TODO: named arguments for activations, confusing which is being
        # called.
        parent = new_node.parent
        if isinstance(parent, BetaMemory):
            for tok in parent.items:
                new_node.left_activation(token=tok)
        elif isinstance(parent, JoinNode):
            saved_list_of_children = parent.children
            parent.children = [new_node]
            for item in parent.amem.items:
                parent.right_activation(item)
            parent.children = saved_list_of_children
        elif isinstance(parent, NegativeNode):
            for token in parent.items:
                if not token.join_results:
                    new_node.left_activation(token, None)
        elif isinstance(parent, NccNode):
            for token in parent.items:
                if not token.ncc_results:
                    new_node.left_activation(token, None)
        elif isinstance(parent, (BindNode, FilterNode)):
            saved_list_of_children = parent.children
            parent.children = [new_node]
            self.update_new_node_with_matches_from_above(parent)
            if parent.parent == self.beta_root:
                # parent.left_activation(Token(None, None, {}), None, {})
                parent.left_activation(Token(None, None), None)
            parent.children = saved_list_of_children

    def delete_alpha_memory(self, amem):
        del self.alpha_hash[amem.key]

    def delete_node_and_any_unused_ancestors(self, node):
        """
        :type node: BetaNode
        """
        if isinstance(node, NccNode):
            self.delete_node_and_any_unused_ancestors(node.partner)

        if isinstance(node, (BetaMemory, NegativeNode, NccNode)):
            for item in node.items:
                item.delete_token_and_descendents()

        if isinstance(node, NccPartnerNode):
            for item in node.new_result_buffer:
                item.delete_token_and_descendents()

        if isinstance(node, (JoinNode, NegativeNode)):
            if not node.right_unlinked:
                node.amem.successors.remove(node)
            node.amem.reference_count -= 1
            if node.amem.reference_count == 0:
                self.delete_alpha_memory(node.amem)

        if isinstance(node, JoinNode):
            if not node.left_unlinked:
                node.parent.children.remove(node)
            node.parent.all_children.remove(node)
            if not node.parent.all_children:
                self.delete_node_and_any_unused_ancestors(node.parent)
        elif not node.parent.children:
            self.delete_node_and_any_unused_ancestors(node.parent)
