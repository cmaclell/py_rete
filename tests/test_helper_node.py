from py_rete.production import Production
from py_rete.conditions import Cond
from py_rete.conditions import AND
from py_rete.conditions import Filter
from py_rete.conditions import Bind
from py_rete.network import ReteNetwork
from py_rete.common import WME
from py_rete.common import V


def test_filter_compare():
    net = ReteNetwork()
    c0 = Cond('spu:1', 'price', V('x'))
    f0 = Filter(lambda x: x > 100)
    f1 = Filter(lambda x: x < 200)
    f2 = Filter(lambda x: x > 200 and x < 400)
    f3 = Filter(lambda x: x > 300)

    @Production(AND(c0, f0, f1))
    def p0():
        pass
    net.add_production(p0)

    @Production(AND(c0, f2))
    def p1():
        pass
    net.add_production(p1)

    @Production(AND(c0, f3))
    def p2():
        pass
    net.add_production(p2)

    net.add_wme(WME('spu:1', 'price', 100))
    net.add_wme(WME('spu:1', 'price', 150))
    net.add_wme(WME('spu:1', 'price', 300))

    assert len(list(p0.activations)) == 1
    token = list(p0.activations)[0]
    assert token.get_binding(V('x')) == 150

    assert len(list(p1.activations)) == 1
    token = list(p1.activations)[0]
    assert token.get_binding(V('x')) == 300

    assert len(list(p2.activations)) == 0


def test_bind():
    net = ReteNetwork()
    c0 = Cond('spu:1', 'sales', V('x'))
    b0 = Bind(lambda x: len(set(x) & set(range(1, 100))), V('num'))
    f0 = Filter(lambda num: num > 0)

    @Production(AND(c0, b0, f0))
    def p0():
        pass
    net.add_production(p0)

    b1 = Bind(lambda x: len(set(x) & set(range(100, 200))), V('num'))

    @Production(AND(c0, b1, f0))
    def p1():
        pass
    net.add_production(p1)

    b2 = Bind(lambda x: len(set(x) & set(range(300, 400))), V('num'))

    @Production(AND(c0, b2, f0))
    def p2():
        pass
    net.add_production(p2)

    net.add_wme(WME('spu:1', 'sales', range(50, 110)))

    assert len(list(p0.activations)) == 1
    assert len(list(p1.activations)) == 1
    assert len(list(p2.activations)) == 0
    t0 = list(p0.activations)[0]
    t1 = list(p1.activations)[0]
    assert t0.get_binding(V('num')) == 50
    assert t1.get_binding(V('num')) == 10
