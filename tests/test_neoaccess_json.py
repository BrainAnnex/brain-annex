# Testing of JSON-based Import/Export

import pytest
from BrainAnnex.modules.neo_access import neo_access



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = neo_access.NeoAccess(debug=False, verbose=False)
    yield neo_obj



def test_export_dbase_json(db):
    # Completely clear the database
    db.empty_dbase()

    # Start by exporting the empty database
    result = db.export_dbase_json()
    assert result == {'nodes': 0, 'relationships': 0, 'properties': 0, 'data': '[\n]'}

    # Create a first node
    node_id1 = db.create_node("User", {'name': 'Eve'})
    result = db.export_dbase_json()
    assert result['nodes'] == 1
    assert result['relationships'] == 0
    assert result['properties'] == 1
    expected_json = '[{"type":"node","id":"' + str(node_id1) + '","labels":["User"],"properties":{"name":"Eve"}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}}
                ]
    '''


    # Create a 2nd node
    node_id2 = db.create_node("User", {'name': 'Adam', 'age': 30})
    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 0
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id1}","labels":["User"],"properties":{{"name":"Eve"}}}},\n {{"type":"node","id":"{node_id2}","labels":["User"],"properties":{{"name":"Adam","age":30}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
                [{"type":"node","id":"100","labels":["User"],"properties":{"name":"Eve"}},
                 {"type":"node","id":"101","labels":["User"],"properties":{"name":"Adam","age":30}}
                ]
    '''

    # Now add relationship (with no properties) between the above two nodes
    db.link_nodes_by_ids(node_id1, node_id2, "LOVES")
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_1 = query_result[0]["rel_id"]

    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 1
    assert result['properties'] == 3
    expected_json = f'[{{"type":"node","id":"{node_id1}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id2}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id1}","labels":["User"]}},"end":{{"id":"{node_id2}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"108","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"109","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"3","type":"relationship","label":"LOVES","start":{"id":"108","labels":["User"]},"end":{"id":"109","labels":["User"]}}
        ]
    '''

    # Add a 2nd relationship (this time with properties) between the two nodes
    db.link_nodes_by_ids(node_id1, node_id2, "KNOWS", {'since': 1976, 'intensity': 'eternal'})
    # Look up the Neo4j ID of the relationship just created
    cypher = "MATCH (to)-[r:KNOWS]->(from) RETURN id(r) AS rel_id"
    query_result = db.query(cypher)
    rel_id_2 = query_result[0]["rel_id"]

    result = db.export_dbase_json()
    assert result['nodes'] == 2
    assert result['relationships'] == 2
    assert result['properties'] == 5    # Note that the 2 properties in the latest relationship went into the count
    expected_json = f'[{{"type":"node","id":"{node_id1}","labels":["User"],"properties":{{"name":"Eve"}}}},\n' \
                    f' {{"type":"node","id":"{node_id2}","labels":["User"],"properties":{{"name":"Adam","age":30}}}},\n' \
                    f' {{"id":"{rel_id_1}","type":"relationship","label":"LOVES","start":{{"id":"{node_id1}","labels":["User"]}},"end":{{"id":"{node_id2}","labels":["User"]}}}},\n' \
                    f' {{"id":"{rel_id_2}","type":"relationship","label":"KNOWS","properties":{{"intensity":"eternal","since":1976}},"start":{{"id":"{node_id1}","labels":["User"]}},"end":{{"id":"{node_id2}","labels":["User"]}}}}\n]'
    assert result['data'] == expected_json
    ''' EXAMPLE of JSON string:
        [{"type":"node","id":"124","labels":["User"],"properties":{"name":"Eve"}},
         {"type":"node","id":"125","labels":["User"],"properties":{"name":"Adam","age":30}},
         {"id":"11","type":"relationship","label":"LOVES","start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}},
         {"id":"12","type":"relationship","label":"KNOWS","properties":{"intensity":"eternal","since":1976},"start":{"id":"124","labels":["User"]},"end":{"id":"125","labels":["User"]}}
        ]
    '''



def test_import_json_data(db):

    # Check various malformed JSON data dumps
    with pytest.raises(Exception):
        assert db.import_json_data("Nonsensical JSON string")   # This ought to raise an Exception:
                                                                # Incorrectly-formatted JSON string. Expecting value: line 1 column 1 (char 0)
    with pytest.raises(Exception):
        assert db.import_json_data('{"a": "this is good JSON, but not a list!"}')   # This ought to raise an Exception:
                                                                                    # "The JSON string does not represent the expected list"
    # TODO: extend

    # Now, test actual imports

    # Completely clear the database
    db.empty_dbase()

    json = '[{"type":"node","id":"123","labels":["User"],"properties":{"name":"Eve"}}]'
    details = db.import_json_data(json)
    assert details == "Successful import of 1 node(s) and 0 relationship(s)"
    match = db.find(labels="User", properties={"name": "Eve"})
    retrieved_records = db.fetch_nodes(match)
    assert len(retrieved_records) == 1

    # TODO: extend
