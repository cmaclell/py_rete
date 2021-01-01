from py_rete.common import WME
from py_rete.network import ReteNetwork
from py_rete.conditions import Cond
from py_rete.production import Production
from py_rete.common import V
import pytest


def test_root():
    # network is root, uses hash
    net = ReteNetwork()

    c0 = Cond('a', 'b', 'c')
    am0 = net.build_or_share_alpha_memory(c0)
    assert am0 is not None

    am1 = net.build_or_share_alpha_memory(c0)
    assert am0 == am1

    assert len(net.alpha_hash) == 1

    wme = WME('a', 'b', 'c')
    net.add_wme(wme)

    assert len(am0.items) == 1


@pytest.mark.skip(reason="not necessary if facts are main elements.")
def test_intra_condition_consistency():
    net = ReteNetwork()
    c = Cond(V('x'), 'b', V('x'))

    @Production(c)
    def test():
        pass

    net.add_production(test)

    wme = WME('a', 'b', 'c')

    net.add_wme(wme)

    assert len(list(net.matches)) == 0

    c2 = Cond(V('x'), 'b', V('z'))

    @Production(c2)
    def test2():
        pass

    net.add_production(test2)

    assert len(list(net.matches)) == 1
