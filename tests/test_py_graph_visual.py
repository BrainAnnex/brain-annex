import pytest
from brainannex.modules.py_graph_visual.py_graph_visual import PyGraphVisual
from brainannex.modules.utilities.comparisons import *



def test_add_node():
    graph = PyGraphVisual()

    graph.add_node(node_id=123, labels="Person", data={"name": "Julian"})

    result = graph.get_graph_data()

    assert result == {'structure': [{'name': 'Julian', 'id': 123, 'labels': ['Person']}],
                      'color_mapping': {}, 'caption_mapping': {}}
    assert graph._all_node_ids == [123]


    graph.add_node(node_id=456, labels="Person", data={"name": "Val"})

    result = graph.get_graph_data().get("structure")

    expected = [{'name': 'Julian', 'id': 123, 'labels': ['Person']},
                {'name': 'Val', 'id': 456, 'labels': ['Person']}]

    assert compare_recordsets(result , expected)
    assert graph._all_node_ids == [123, 456]


    graph.add_node(node_id=456, labels="Person", data={"name": "it doesn't matter"})

    result = graph.get_graph_data().get("structure")

    assert compare_recordsets(result , expected)    # No change from before
    assert graph._all_node_ids == [123, 456]
