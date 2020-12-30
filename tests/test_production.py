from py_rete.common import WME
from py_rete.common import V
from py_rete.network import ReteNetwork
from py_rete.conditions import Cond
from py_rete.production import Production
from py_rete.fact import Fact


def test_production():

    class Block(Fact):
        pass

    @Production(Block(name=V('x'), clear=True))
    def is_clear(x):
        print(x)

    net = ReteNetwork()
    net.add_production(is_clear)


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
