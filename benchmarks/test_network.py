# -*- coding: utf-8 -*-
from py_rete.production import Bind
from py_rete.production import Cond
from py_rete.production import AndCond
from py_rete.production import Effect
from py_rete.production import AndEffect
from py_rete.production import Production
from py_rete.common import WME
from py_rete.network import Network


def init_network():
    net = Network()
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'left-of', '$z')
    c2 = Cond('$z', 'color', 'red')
    net.add_production(Production('Test', AndCond(c0, c1, c2)))
    return net


def test_fire():
    fire_counting()


def fire_counting():
    net = Network()
    c0 = Cond('$node', 'number', '$x')
    c1 = Bind('str($x + 1)', '$y')
    e0 = Effect('$node', 'number', '$y')
    p0 = Production('add1', AndCond(c0, c1), AndEffect(e0))
    w0 = WME('root', 'number', '1')

    net.add_production(p0)
    assert len(net.wmes) == 0

    net.add_wme(w0)
    assert len(net.wmes) == 1

    for i in range(10):
        net.fire_all()
        assert len(net.wmes) == i+2


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


def test_init_network(benchmark):
    benchmark(init_network)


def test_add_wmes(benchmark):
    benchmark(add_wmes)


def test_activation():
    net = Network()
    c0 = Cond('$x', 'on', '$y')
    c1 = Cond('$y', 'color', 'red')
    p = Production('test', AndCond(c0, c1))
    net.add_production(p)

    activations = [p for p in net.matches]
    assert len(activations) == 0

    wmes = [WME('B1', 'on', 'B2'),
            WME('B2', 'color', 'red')]

    for wme in wmes:
        net.add_wme(wme)

    activations = [p for p in net.matches]
    assert len(activations) == 1

    net.remove_wme(wmes[0])

    activations = [p for p in net.matches]
    assert len(activations) == 0


def test_facts():
    net = Network()

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
