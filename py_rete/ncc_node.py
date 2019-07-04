from py_rete.common import Token
from py_rete.beta import BetaNode


class NccNode(BetaNode):
    """
    A beta network class for negated conjunctive conditions (ncc).

    This has a memory of tokens (items) and a partner node. On left_activation
    (from parent), the node adds results from its partner's result buffer to
    the newly created token's ncc_results list, and sets the owner of the
    result to the new token. If the new token does not have a any results in
    the ncc_results list, then it activates all the children.

    Notes:
        - I'm currently assuming that the partner node is activated first (in
          the parent's children list). Doorenbos suggests this is more
          efficient (see page 47 of his thesis). The psuedocode apparently
          supports either ordering, but activating the partner first saves
          work.

    TODO:
        - Check to confirm that the partner node is activated first.
          like the partner should be activated first for efficiency reasons.
        - Should items be a set? Maybe indexed?
        - Can left_activation be modified, so it only requires a token, not a
          wme?
        - In left_activation, pop in a loop rather than iterate and remove
          (which also iterates)?
    """

    def __init__(self, children=None, parent=None, items=None, partner=None):
        """
        :type partner: NccPartnerNode
        :type items: list of rete.Token
        """
        super(NccNode, self).__init__(children=children, parent=parent)
        self.items = items if items else []
        self.partner = partner

    def left_activation(self, token, wme, binding=None):
        """
        :type w: rete.WME
        :type t: rete.Token
        :type binding: dict
        """
        new_token = Token(token, wme, self, binding)
        self.items.append(new_token)
        for result in self.partner.new_result_buffer:
            self.partner.new_result_buffer.remove(result)
            new_token.ncc_results.append(result)
            result.owner = new_token
        if not new_token.ncc_results:
            for child in self.children:
                child.left_activation(new_token, None)


class NccPartnerNode(BetaNode):
    """
    The partner node for negated conjunctive conditions node.

    Takes the associated ncc node, the number of conditions, and a buffer of
    any new results.

    TODO:
        - Can left activation be modified to remove the need for wme, just
          requiring a token?
        - I believe the left_activation code commented out below is correct and
          should replace the current implementation. Need to write test cases
          to distinguish/verify.
    """

    def __init__(self, children=None, parent=None, ncc_node=None,
                 number_of_conditions=0, new_result_buffer=None):
        """
        :type new_result_buffer: list of rete.Token
        :type ncc_node: NccNode
        """
        super(NccPartnerNode, self).__init__(children=children, parent=parent)
        self.ncc_node = ncc_node
        self.number_of_conditions = number_of_conditions
        self.new_result_buffer = new_result_buffer if new_result_buffer else []

    def left_activation(self, token, wme, binding=None):
        """
        :type w: rete.WME
        :type t: rete.Token
        :type binding: dict
        """
        new_result = Token(token, wme, self, binding)
        owners_t = token
        owners_w = wme
        for i in range(self.number_of_conditions):
            owners_w = owners_t.wme
            owners_t = owners_t.parent
        for token in self.ncc_node.items:
            if token.parent == owners_t and token.wme == owners_w:
                token.ncc_results.append(new_result)
                new_result.owner = token

                # TODO: Doorenboos suggests the use of this helper instead.
                # write tests to confirm.
                Token.delete_descendents_of_token(token)
                # Token.delete_token_and_descendents(token)

        self.new_result_buffer.append(new_result)

    # def left_activation(self, token, wme, binding=None):
    #     """
    #     :type w: rete.WME
    #     :type t: rete.Token
    #     :type binding: dict
    #     """
    #     new_result = Token(token, wme, self, binding)
    #     owners_t = token
    #     owners_w = wme
    #     for i in range(self.number_of_conditions):
    #         owners_w = owners_t.wme
    #         owners_t = owners_t.parent
    #     for token in self.ncc_node.items:
    #         if token.parent == owners_t and token.wme == owners_w:
    #             token.ncc_results.append(new_result)
    #             new_result.owner = token
    #             Token.delete_token_and_descendents(token)
    #             break
    #     else:
    #         self.new_result_buffer.append(new_result)
