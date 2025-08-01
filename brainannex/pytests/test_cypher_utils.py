import pytest
from brainannex.cypher_utils import NodeSpecs, CypherMatch, CypherUtils




############   For class NodeSpecs   ############

def test_NodeSpecs_constructor():
    ns = NodeSpecs(internal_id=123,
                   labels="my_label", key_name="a", key_value=100,
                   properties={"age": 22},
                   clause="n.income > 10000", clause_dummy_name="n")

    assert ns.internal_id == 123
    assert ns.labels == "my_label"
    assert ns.key_name == "a"
    assert ns.key_value == 100
    assert ns.properties == {"age": 22}
    assert ns.clause == "n.income > 10000"
    assert ns.clause_dummy_name == "n"

    with pytest.raises(Exception):
        NodeSpecs(internal_id=-123) # Bad ID

    with pytest.raises(Exception):
        NodeSpecs(labels=666)       # Bad labels

    # TODO: test more scenarios




############   For class CypherMatch   ############

def test_CypherMatch_constructor():
    ns = NodeSpecs(internal_id=123,
                   labels="my_label", key_name="a", key_value=100,
                   properties={"age": 22},
                   clause="n.income > 30000", clause_dummy_name="n")

    cm = CypherMatch(node_specs=ns)
    # The presence of internal_id over-ride everything else
    assert cm.node == "(n)"
    assert cm.where == "id(n) = 123"
    assert cm.data_binding == {}
    assert cm.dummy_node_name == "n"


    ns = NodeSpecs(labels="my_label",
                   key_name="a", key_value=100,
                   properties={"age": 22},
                   clause="n.income > 30000", clause_dummy_name="n")

    cm = CypherMatch(node_specs=ns)

    assert cm.node == "(n :`my_label` {`age`: $n_par_1, `a`: $n_par_2})"
    assert cm.where == "n.income > 30000"
    assert cm.data_binding == {"n_par_1": 22, "n_par_2": 100}
    assert cm.dummy_node_name == "n"

    # TODO: test more scenarios



############   For class CypherUtils   ############

def test_assert_valid_internal_id():
    CypherUtils.assert_valid_internal_id(23)
    CypherUtils.assert_valid_internal_id(0)
    with pytest.raises(Exception):
        CypherUtils.assert_valid_internal_id(-1)
    with pytest.raises(Exception):
        CypherUtils.assert_valid_internal_id("Do I look like a database ID")
    with pytest.raises(Exception):
        CypherUtils.assert_valid_internal_id([2,3])



def test_valid_internal_id():
    assert CypherUtils.valid_internal_id(23) == True
    assert CypherUtils.valid_internal_id(0) == True
    assert CypherUtils.valid_internal_id(-1) == False
    assert CypherUtils.valid_internal_id("Do I look like a database ID") == False
    assert CypherUtils.valid_internal_id([2,3]) == False



def test_prepare_labels():
    lbl = None
    assert CypherUtils.prepare_labels(lbl) == ""

    lbl = ""
    assert CypherUtils.prepare_labels(lbl) == ""

    lbl = "client"
    assert CypherUtils.prepare_labels(lbl) == ":`client`"

    lbl = ["car", "car manufacturer"]
    assert CypherUtils.prepare_labels(lbl) == ":`car`:`car manufacturer`"



def test_prepare_where():
    assert CypherUtils.prepare_where("") == ""
    assert CypherUtils.prepare_where("      ") == ""
    assert CypherUtils.prepare_where([]) == ""
    assert CypherUtils.prepare_where([""]) == ""
    assert CypherUtils.prepare_where(("  ", "")) == ""

    wh = "n.name = 'Julian'"
    assert CypherUtils.prepare_where(wh) == "WHERE (n.name = 'Julian')"

    wh = ["n.name = 'Julian'"]
    assert CypherUtils.prepare_where(wh) == "WHERE (n.name = 'Julian')"

    wh = ("p.key1 = 123", "   ",  "p.key2 = 456")
    assert CypherUtils.prepare_where(wh) == "WHERE (p.key1 = 123 AND p.key2 = 456)"

    with pytest.raises(Exception):
        assert CypherUtils.prepare_where(123)    # Not a string, nor tuple, nor list



def test_dict_to_cypher():
    d = {'since': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d) == ('{`since`: $par_1, `code`: $par_2}', {'par_1': 2003, 'par_2': 'xyz'})

    d = {'year first met': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d) == ('{`year first met`: $par_1, `code`: $par_2}', {'par_1': 2003, 'par_2': 'xyz'})

    d = {'year first met': 2003, 'code': 'xyz'}
    assert CypherUtils.dict_to_cypher(d, prefix="val_") == ('{`year first met`: $val_1, `code`: $val_2}', {'val_1': 2003, 'val_2': 'xyz'})

    d = {'cost': 65.99, 'code': 'the "red" button'}
    assert CypherUtils.dict_to_cypher(d) == ('{`cost`: $par_1, `code`: $par_2}', {'par_1': 65.99, 'par_2': 'the "red" button'})

    d = {'phrase': "it's ready!"}
    assert CypherUtils.dict_to_cypher(d) == ('{`phrase`: $par_1}', {'par_1': "it's ready!"})

    d = {'phrase': '''it's "ready"!'''}
    assert CypherUtils.dict_to_cypher(d) == ('{`phrase`: $par_1}', {'par_1': 'it\'s "ready"!'})

    d = None
    assert CypherUtils.dict_to_cypher(d) == ("", {})

    d = {}
    assert CypherUtils.dict_to_cypher(d) == ("", {})
