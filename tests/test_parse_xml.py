from py_rete.utils import parse_xml
from py_rete.conditions import AND
from py_rete.conditions import Cond
from py_rete.conditions import Ncc
from py_rete.conditions import Filter
from py_rete.conditions import Bind
from py_rete.common import V
import pytest


@pytest.mark.skip(reason="variables not parsing correctly")
def test_xml():
    s = """<?xml version="1.0"?>
    <data version="0.0.2">
        <production>
            <lhs>
                <has identifier="?x" attribute="on" value="?y" />
                <bind to="?test">1+1</bind>
                <filter>?y != "table"</filter>
                <ncc>
                    <has identifier="?z" attribute="color" value="red" />
                    <has identifier="?z" attribute="on" value="?w" />
                </ncc>
            </lhs>
            <rhs></rhs>
        </production>
    </data>"""
    result = parse_xml(s)
    assert result[0][0] == AND(
        Cond(V('x'), 'on', V('y')),
        Bind(lambda: 1+1, V('test')),
        Filter(lambda y: y != "table"),
        Ncc(Cond(V('z'), 'color', 'red'),
            Cond(V('z'), 'on', V('w'))))
