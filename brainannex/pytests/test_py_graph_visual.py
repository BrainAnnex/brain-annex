# MAKE SURE TO FIRST SET THE ENVIRONMENT VARIABLES, prior to run the pytests in this file!

from brainannex import PyGraphVisual, GraphAccess
from utilities.comparisons import *
import pytest
import neo4j.time



def test_get_graph_data():
    graph = PyGraphVisual()
    graph.node_structure = ["my_node_list"]
    graph.edge_structure = ["my_edge_list"]
    graph.color_mapping = {"a": "red"}
    graph.caption_mapping = {"z": 99}

    assert graph.get_graph_data() == {
                    "node_structure": ["my_node_list"],
                    "edge_structure": ["my_edge_list"],
                    "color_mapping": {"a": "red"},
                    "caption_mapping": {"z": 99}
                }



def test_add_node():
    graph = PyGraphVisual()

    graph.add_node(node_id=123, labels="Person", properties={"name": "Julian"})

    result = graph.get_graph_data()

    assert result == {'node_structure': [{'name': 'Julian', 'id': 123, '_node_labels': ['Person']}],
                      'edge_structure' : [],
                      'color_mapping': {}, 'caption_mapping': {}}
    assert graph._all_node_ids == [123]


    graph.add_node(node_id=456, labels="Person", properties={"name": "Val"})

    result = graph.get_graph_data().get("node_structure")

    expected = [{'id': 123, 'name': 'Julian', '_node_labels': ['Person']},
                {'id': 456, 'name': 'Val', '_node_labels': ['Person']}]

    assert compare_recordsets(result , expected)
    assert graph._all_node_ids == [123, 456]


    # Duplicate node_id
    graph.add_node(node_id=456, labels="Person", properties={"name": "it doesn't matter"})

    result = graph.get_graph_data().get("node_structure")

    assert compare_recordsets(result , expected)    # No change from before
    assert graph._all_node_ids == [123, 456]


    with pytest.raises(Exception):
        graph.add_node(node_id=["??"])

    with pytest.raises(Exception):
        graph.add_node(node_id="")



def test_add_edge():
    graph = PyGraphVisual()

    graph.add_node(node_id=123, labels="Person", properties={"name": "Julian"})
    graph.add_node(node_id=456, labels="Person", properties={"name": "Val"})

    graph.add_edge(from_node=123, to_node=456, name="KNOWS")

    result = graph.get_graph_data()
    assert result["color_mapping"] == {}
    assert result["caption_mapping"] == {}
    assert result["node_structure"] == [ {'id': 123, 'name': 'Julian', '_node_labels': ['Person']},
                                         {'id': 456, 'name': 'Val', '_node_labels': ['Person']}
                                       ]
    assert result["edge_structure"] == [ {'id': 'edge-1', 'name': 'KNOWS', 'source': 123, 'target': 456} ]

    graph.add_node(node_id="car-1", labels=["Car", "Vehicle"], properties={"color": "white"})
    graph.add_edge(from_node=123, to_node="car-1", name="OWNS", properties={"paid": 100})

    result = graph.get_graph_data()
    assert result["color_mapping"] == {}
    assert result["caption_mapping"] == {}
    assert result["node_structure"] == [    {'id': 123, 'name': 'Julian', '_node_labels': ['Person']},
                                            {'id': 456, 'name': 'Val', '_node_labels': ['Person']},
                                            {'id': 'car-1', 'color': 'white', '_node_labels': ["Car", "Vehicle"]}
                                        ]
    assert result["edge_structure"] == [
                                            {'id': 'edge-1', 'name': 'KNOWS', 'source': 123, 'target': 456},
                                            {'id': 'edge-2', 'name': 'OWNS', 'source': 123, 'target': 'car-1', 'paid':100}
                                        ]



def test_assign_caption():
    graph = PyGraphVisual()

    graph.assign_caption(label = "my_label_1", caption = "title")
    assert graph.get_graph_data().get("caption_mapping") == {"my_label_1": "title"}



def test_assign_color_mapping():
    graph = PyGraphVisual()

    graph.assign_color_mapping(label = "my_label_1", color = "yellow")
    assert graph.get_graph_data().get("color_mapping") == {"my_label_1": "yellow"}

    graph.assign_color_mapping(label = "my_label_2", color = "#FF0088")
    assert graph.get_graph_data().get("color_mapping") == {"my_label_1": "yellow", "my_label_2": "#FF0088"}

    graph.assign_color_mapping(label = "my_label_3", color = "graph_orange")
    assert graph.get_graph_data().get("color_mapping") \
        == {"my_label_1": "yellow", "my_label_2": "#FF0088", "my_label_3": "#F79768"}



def test_prepare_recordset():
    graph = PyGraphVisual()

    with pytest.raises(Exception):
        graph.prepare_recordset(id_list=[1, 2, 3])     # Missing db handle when initializing PyGraphVisual()

    db = GraphAccess(debug=False)

    graph = PyGraphVisual(db=db)
    db.empty_dbase()

    with pytest.raises(Exception):
        graph.prepare_recordset(id_list="I'm not a list")

    result = graph.prepare_recordset(id_list=[1, 2, 3])    # Non-existent nodes
    assert result == []


    # Start populating the database
    p_1 = db.create_node(labels="Person", properties={'name': 'Julian'})

    result = graph.prepare_recordset(id_list=[p_1])
    assert result == [{'internal_id': p_1, '_node_labels': ['Person'], 'name': 'Julian'}]


    p_2 = db.create_node(labels="Person", properties={'name': 'Val'})
    result = graph.prepare_recordset(id_list=[p_1, p_2])
    expected = [{'internal_id': p_1, '_node_labels': ['Person'], 'name': 'Julian'},
                {'internal_id': p_2, '_node_labels': ['Person'], 'name': 'Val'}]
    assert compare_recordsets(result, expected)



def test_prepare_graph_1():
    db = GraphAccess(debug=False)

    graph = PyGraphVisual(db=db)

    # Prepare a graph with 2 nodes and no links
    dataset = [  {"internal_id": 123, "_node_labels": ["Person"], 'name': 'Julian'},
                 {"internal_id": 456, "_node_labels": ["Person"], 'name': 'Val'}
              ]

    result = graph.prepare_graph(result_dataset=dataset, add_edges=False)
    assert result == [123, 456]

    internal_data = graph.get_graph_data()

    assert internal_data['color_mapping'] == {}
    assert internal_data['caption_mapping'] == {}

    expected_node_structure = [{'id': 123, 'internal_id': 123, 'name': 'Julian', '_node_labels': ['Person']},
                                {'id': 456, 'internal_id': 456, 'name': 'Val', '_node_labels': ['Person']}]
    expected_edge_structure = []

    assert compare_recordsets(internal_data["node_structure"] , expected_node_structure)
    assert compare_recordsets(internal_data["edge_structure"] , expected_edge_structure)
    assert graph._all_node_ids == [123, 456]


    # Adding a record with a key named 'id' (which automatically gets renamed 'id_original'
    dataset += [{'internal_id': 789, "_node_labels": ["Person"], 'name': 'Rese', 'id': 'some value'}]
    result = graph.prepare_graph(result_dataset=dataset, add_edges=False)
    assert result == [123, 456, 789]

    internal_node_structure = graph.get_graph_data().get("node_structure")
    expected_node_structure = [{'id': 123, 'internal_id': 123, 'name': 'Julian', '_node_labels': ['Person']},
                               {'id': 456, 'internal_id': 456, 'name': 'Val',    '_node_labels': ['Person']},
                               {'id': 789, 'internal_id': 789, 'name': 'Rese',   '_node_labels': ['Person'], 'id_original': 'some value'}]

    assert compare_recordsets(internal_node_structure , expected_node_structure)

    internal_edge_structure = graph.get_graph_data().get("edge_structure")
    expected_edge_structure = []

    assert compare_recordsets(internal_edge_structure , expected_edge_structure)

    dataset += [{'internal_id': 666, 'id': 'X', 'id_original': 'Y' }]
    with pytest.raises(Exception):
        # Unable to rename 'id' as 'id_original', because it already exists
        graph.prepare_graph(result_dataset=dataset, add_edges=False)



def test_prepare_graph_2():
    # Prepare the database with 3 nodes and 2 links
    db = GraphAccess(debug=False)
    db.empty_dbase()

    p_1 = db.create_node(labels="Person", properties={'name': 'Julian'})
    p_2 = db.create_node(labels="Person", properties={'name': 'Val'})
    db.add_links(match_from=p_1, match_to=p_2, rel_name="KNOWS")

    c_1 = db.create_node(labels=["Car"], properties={"color": "white"})
    db.add_links_fast(match_from=p_1, match_to=c_1, rel_name="OWNS", rel_props={"paid": 100})


    match = db.match()      # This will pull all the 3 nodes in the database
    dataset = db.get_nodes(match=match, return_internal_id=True, return_labels=True)

    graph = PyGraphVisual(db=db)
    result = graph.prepare_graph(result_dataset=dataset, add_edges=False)
    assert compare_unordered_lists(result, [p_1, p_2, c_1])
    assert compare_unordered_lists(graph._all_node_ids, [p_1, p_2, c_1])

    expected_node_structure = [{'id': p_1, 'internal_id': p_1, 'name': 'Julian', '_node_labels': ['Person']},
                               {'id': p_2, 'internal_id': p_2, 'name': 'Val',    '_node_labels': ['Person']},
                               {'id': c_1, 'internal_id': c_1, 'color': 'white', '_node_labels': ['Car']}]

    internal_data = graph.get_graph_data()
    assert compare_recordsets(internal_data["node_structure"] , expected_node_structure)


    # Repeat, but now also automatically fetch all edges
    graph = PyGraphVisual(db=db)

    result = graph.prepare_graph(result_dataset=dataset, add_edges=True)
    assert compare_unordered_lists(graph._all_node_ids, [p_1, p_2, c_1])

    assert compare_unordered_lists(result, [p_1, p_2, c_1])
    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")

    assert compare_recordsets(internal_node_structure , expected_node_structure)

    expected_edge_structure_1 = [
                                  {'name': 'OWNS', 'source': p_1, 'target': c_1, 'id': 'edge-1', 'paid':100},
                                  {'name': 'KNOWS', 'source': p_1, 'target': p_2, 'id': 'edge-2'}
                                ]

    # Make allowance for the fact that the edges could be returned in any order (and thus have reversed id's)
    expected_edge_structure_2 = [
                                  {'name': 'OWNS', 'source': p_1, 'target': c_1, 'id': 'edge-2', 'paid':100},
                                  {'name': 'KNOWS', 'source': p_1, 'target': p_2, 'id': 'edge-1'}
                               ]

    assert compare_recordsets(internal_edge_structure , expected_edge_structure_1) \
                or compare_recordsets(internal_edge_structure , expected_edge_structure_2)


    # Now exclude some edges by name
    graph.prepare_graph(result_dataset=dataset, add_edges=True, avoid_links="NON_EXISTENT_LINK")
    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")

    # Same as before
    assert compare_recordsets(internal_node_structure , expected_node_structure)
    assert compare_recordsets(internal_edge_structure , expected_edge_structure_1) \
                or compare_recordsets(internal_edge_structure , expected_edge_structure_2)


    graph.prepare_graph(result_dataset=dataset, add_edges=True, avoid_links="OWNS")
    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")
    expected_edge_structure = [
                                {'name': 'KNOWS', 'source': p_1, 'target': p_2, 'id': 'edge-1'}
                             ]  # We have now lost en edge
    assert compare_recordsets(internal_node_structure , expected_node_structure)
    assert compare_recordsets(internal_edge_structure , expected_edge_structure)


    graph.prepare_graph(result_dataset=dataset, add_edges=True, avoid_links="KNOWS")
    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")
    expected_edge_structure = [
                                {'name': 'OWNS', 'source': p_1, 'target': c_1, 'id': 'edge-1', 'paid':100},
                              ]
    assert compare_recordsets(internal_node_structure , expected_node_structure)
    assert compare_recordsets(internal_edge_structure , expected_edge_structure)


    graph.prepare_graph(result_dataset=dataset, add_edges=True, avoid_links=["KNOWS", "OWNS"])
    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")
    expected_edge_structure = [ ]
    assert compare_recordsets(internal_node_structure , expected_node_structure)
    assert compare_recordsets(internal_edge_structure , expected_edge_structure)


    with pytest.raises(Exception):
        # Bad type for `avoid_links`
        graph.prepare_graph(result_dataset=dataset, add_edges=True, avoid_links=("KNOWS", "OWNS"))



def test_prepare_graph_3():
    # Prepare the database with nodes and links that contain date(time) fields
    db = GraphAccess(debug=False)
    db.empty_dbase()

    car_id = db.create_node(labels="Car", properties={"color": "red",
                                             "make": "Honda",
                                             "manufactured_on": neo4j.time.Date(2019, 6, 1),
                                             "certified": neo4j.time.DateTime(2019, 8, 31, 18, 59, 35)
                                             })
    dataset = db.get_nodes(match=car_id, return_internal_id=True, return_labels=True)

    graph = PyGraphVisual(db=db)
    result = graph.prepare_graph(result_dataset=dataset, add_edges=False)
    assert result == [car_id]

    assert graph.get_graph_data()['node_structure'] == [{'color': 'red', 'make': 'Honda',
                                                         'manufactured_on': '2019/06/01', 'certified': '2019/08/31',
                                                         'id': car_id, 'internal_id': car_id, '_node_labels': ['Car']}]

    assert graph.get_graph_data()['edge_structure'] == []


    # Add a 2nd node, to be linked to the 1st one
    person_id = db.create_node(labels=["Person"], properties={"name": "Julian"})

    # Now add the link
    '''
    # This won't work yet until a limitation in add_links_fast() is lifted
    db.add_links_fast(match_from=person_id, match_to=car_id, rel_name="OWNS",
                      rel_props={"bought": neo4j.time.DateTime(2025, 11, 13, 13, 29, 15)})
    '''
    rel_props="{bought: $par_1}"
    q = f'''
        MATCH (from), (to)
        WHERE id(from) = {person_id} AND id(to) = {car_id}
        MERGE (from) -[:`OWNS` {rel_props}]-> (to)           
        '''
    db.update_query(q, {"par_1": neo4j.time.DateTime(2025, 11, 13, 13, 29, 15)})


    match = db.match()      # This will fetch all the nodes in the database
    dataset = db.get_nodes(match=match, return_internal_id=True, return_labels=True)

    graph = PyGraphVisual(db=db)
    result = graph.prepare_graph(result_dataset=dataset, add_edges=True)
    assert compare_unordered_lists(result, [car_id, person_id])

    internal_node_structure = graph.get_graph_data().get("node_structure")
    internal_edge_structure = graph.get_graph_data().get("edge_structure")

    expected_node_structure  = \
            [   {'color': 'red', 'certified': '2019/08/31', 'make': 'Honda', 'manufactured_on': '2019/06/01', 'id': car_id, 'internal_id': car_id, '_node_labels': ['Car']},
                {'name': 'Julian', 'id': person_id, 'internal_id': person_id, '_node_labels': ['Person']}
            ]

    expected_edge_structure  = [{'name': 'OWNS', 'source': person_id, 'target': car_id, 'id': 'edge-1', 'bought': '2025/11/13'}]

    assert compare_recordsets(internal_node_structure , expected_node_structure)
    assert compare_recordsets(internal_edge_structure , expected_edge_structure)



def test_assemble_graph():
    graph = PyGraphVisual()

    with pytest.raises(Exception):
        graph.assemble_graph(id_list=[1, 2, 3])     # Missing db handle when initializing PyGraphVisual()

    db = GraphAccess(debug=False)

    graph = PyGraphVisual(db=db)
    db.empty_dbase()


    with pytest.raises(Exception):
        graph.assemble_graph(id_list="I'm not a list")

    result = graph.assemble_graph(id_list=[1, 2, 3])    # Non-existent nodes
    assert result == ([], [])


    # Start populating the database
    p_1 = db.create_node(labels="Person", properties={'name': 'Julian'})

    result = graph.assemble_graph(id_list=[p_1])
    assert result == ([{'id': p_1, 'internal_id': p_1, '_node_labels': ['Person'], 'name': 'Julian'}] , [])

    p_2 = db.create_node(labels="Person", properties={'name': 'Val'})

    result = graph.assemble_graph(id_list=[p_1, p_2])
    #print(result)
    #return
    expected_nodes = [{'id': p_1, 'internal_id': p_1, '_node_labels': ['Person'], 'name': 'Julian'},
                      {'id': p_2, 'internal_id': p_2, '_node_labels': ['Person'], 'name': 'Val'}
                    ]
    expected_edges = []

    assert compare_recordsets(result[0], expected_nodes)
    assert compare_recordsets(result[1], expected_edges)


    c_1 = db.create_node(labels="Car", properties={"color": "red",
                                             "make": "Honda",
                                             "manufactured_on": neo4j.time.Date(2019, 6, 1),
                                             "certified": neo4j.time.DateTime(2019, 8, 31, 18, 59, 35)
                                             })

    result = graph.assemble_graph(id_list=[p_1, p_2, c_1])
    expected_nodes = [  {'id': p_1, 'internal_id': p_1, '_node_labels': ['Person'], 'name': 'Julian'},
                        {'id': p_2, 'internal_id': p_2, '_node_labels': ['Person'], 'name': 'Val'},
                        {'id': c_1, 'internal_id': c_1, '_node_labels': ['Car'], 'color': 'red', 'make': 'Honda', 'certified': '2019/08/31', 'manufactured_on': '2019/06/01'}
                     ]
    expected_edges = []
    assert compare_recordsets(result[0], expected_nodes)
    assert compare_recordsets(result[1], expected_edges)


    # Now add a link
    rel_props="{bought: $par_1}"
    q = f'''
        MATCH (from), (to)
        WHERE id(from) = {p_2} AND id(to) = {c_1}
        MERGE (from) -[:`OWNS` {rel_props}]-> (to)           
        '''
    db.update_query(q, {"par_1": neo4j.time.DateTime(2025, 11, 13, 13, 29, 15)})

    result = graph.assemble_graph(id_list=[p_1, p_2, c_1])

    expected_edges = [{'name': 'OWNS', 'source': p_2, 'target': c_1, 'id': 'edge-1', 'bought': '2025/11/13'}]

    assert compare_recordsets(result[0], expected_nodes)    # Same nodes as before
    assert compare_recordsets(result[1], expected_edges)



def test_link_node_groups():
    pass    # TODO