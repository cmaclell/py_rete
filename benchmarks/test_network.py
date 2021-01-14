# from py_rete.production import Bind
from py_rete.conditions import Cond
from py_rete.conditions import AND
from py_rete.production import Production
from py_rete.common import WME
from py_rete.common import V
from py_rete.fact import Fact
from py_rete.conditions import Bind
from py_rete.conditions import Filter
from py_rete.network import ReteNetwork


def init_network():
    net = ReteNetwork()
    c0 = Cond(V('x'), 'on', V('y'))
    c1 = Cond(V('y'), 'left-of', V('z'))
    c2 = Cond(V('z'), 'color', 'red')

    @Production(AND(c0, c1, c2))
    def test():
        pass

    net.add_production(test)

    return net


def test_fire():
    fire_counting()


def add_to_depth():
    net = ReteNetwork()

    @Production(Fact(number=V('x'), depth=V('xd')) &
                Fact(number=V('y'), depth=V('yd')) &
                Filter(lambda xd, yd: xd+yd < 1))
    def add(net, x, y, xd, yd):
        f = Fact(number=x+y, depth=xd+yd+1)
        net.add_fact(f)

    net.add_fact(Fact(name="1", number=1, depth=0))
    net.add_fact(Fact(name="2", number=2, depth=0))
    # net.add_fact(Fact(name="3", number=3, depth=0))
    # net.add_fact(Fact(name="5", number=5, depth=0))
    # net.add_fact(Fact(name="7", number=7, depth=0))

    net.add_production(add)

    while len(list(net.new_matches)) > 0:
        # print(len(list(net.new_matches)))
        m = net.get_new_match()
        m.fire()


def fire_counting():
    net = ReteNetwork()

    @Production(Fact(number=V('x')) &
                ~Fact(before=V('x')) &
                Bind(lambda x: str(int(x) + 1), V('y')))
    def add1(net, x, y):
        f = Fact(number=y, before=x)
        net.add_fact(f)

    net.add_production(add1)
    assert len(net.wmes) == 0

    net.add_fact(Fact(number='1'))
    assert len(net.wmes) == 2

    print(net)

    for i in range(5):
        net.run(1)
        assert len(net.wmes) == (3*(i+1))+2


def test_fire_counting(benchmark):
    benchmark(fire_counting)


def add_wmes():
    net = init_network()
    wmes = [
        WME('B1', 'on', 'B2'),
        WME('B1', 'on', 'B3'),
        WME('B1', 'color', 'red'),
        WME('B2', 'on', 'table'),
        WME('B2', 'left-of', 'B3'),
        WME('B2', 'color', 'blue'),
        WME('B3', 'left-of', 'B4'),
        WME('B3', 'on', 'table'),
        WME('B3', 'color', 'red')
    ]
    for wme in wmes:
        net.add_wme(wme)

    return net


def test_add_to_depth(benchmark):
    benchmark(add_to_depth)


def test_init_network(benchmark):
    benchmark(init_network)


def test_add_wmes(benchmark):
    benchmark(add_wmes)


def test_activation():
    net = ReteNetwork()
    c0 = Cond(V('x'), 'on', V('y'))
    c1 = Cond(V('y'), 'color', 'red')

    @Production(AND(c0, c1))
    def p():
        pass

    net.add_production(p)

    activations = [p for p in net.matches]
    assert len(activations) == 0

    wmes = [WME('B1', 'on', 'B2'),
            WME('B2', 'color', 'red')]

    for wme in wmes:
        net.add_wme(wme)

    print(net.working_memory)
    print(net)

    activations = [p for p in net.matches]
    assert len(activations) == 1

    net.remove_wme(wmes[0])

    activations = [p for p in net.matches]
    assert len(activations) == 0


def test_facts():
    net = ReteNetwork()

    wmes = [e for e in net.wmes]
    assert len(wmes) == 0

    wmes = set([WME('B1', 'on', 'B2'), WME('B2', 'color', 'red')])

    for wme in wmes:
        net.add_wme(wme)

    stored_wmes = set([e for e in net.wmes])
    assert len(stored_wmes) == 2
    assert len(wmes.union(stored_wmes)) == 2

    wmes = list(wmes)
    net.remove_wme(wmes[0])
    stored_wmes = [e for e in net.wmes]
    assert len(stored_wmes) == 1
    assert stored_wmes == wmes[1:]


if __name__ == "__main__":
    add_to_depth()
