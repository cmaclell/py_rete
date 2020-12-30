from py_rete.fact import Fact
from py_rete.network import ReteNetwork


class SubFact(Fact):
    pass


def test_fact():

    f3 = Fact(1, 2, name="test")
    assert f3[0] == 1
    assert f3[1] == 2
    assert f3['name'] == 'test'

    f4 = Fact(name="John")
    assert f4['name'] == 'John'


def test_adding_removing_facts():
    net = ReteNetwork()
    f = Fact()

    net.add_fact(f)
    assert f.id is not None

    assert len(net.working_memory) > 0

    net.remove_fact(f)
    assert f.id is None

    assert len(net.working_memory) == 0
