# *** CAUTION! ***  The database gets cleared out during some of the tests!


import pytest
from brainannex import GraphAccess, NeoSchema, Collections


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=False)
    NeoSchema.set_database(neo_obj)
    Collections.set_database(neo_obj)

    yield neo_obj



# ************  CREATE A SAMPLE COLLECTION for the testing  **************

def create_sample_collections_class(db):
    # Clear the dbase, create a sample Collections Class named "Photo Album" (a Class with a "name" and "uri" properties)

    db.empty_dbase()

    Collections.initialize_collections()

    NeoSchema.create_class_with_properties(name="Photo Album",
                                           properties=["name", "uri"])

    NeoSchema.create_class_relationship(from_class="Photo Album", to_class="Collections",
                                        rel_name="INSTANCE_OF", use_link_node=False)



def create_sample_collection_item_class():
    # Creates a "Photo" Class
    NeoSchema.create_class_with_properties(name="Photo",
                                           properties=["caption", "uri"])



def setup_test_collection(db):
    # Creates a "Photo Album" Class, a "Photo Album" named "Brazil vacation", and a "Photo" Class
    create_sample_collections_class(db)     # Creates a "Photo Album" Class
    create_sample_collection_item_class()   # Creates a "Photo" Class

    # Create a Collection: a "Photo Album" named "Brazil vacation"
    new_uri = NeoSchema.reserve_next_uri(prefix="album-")
    NeoSchema.create_data_node(class_name="Photo Album", properties ={"name": "Brazil vacation"}, new_uri=new_uri)

    return new_uri





# ************  THE ACTUAL TESTS  ************

def test_link_to_collection_at_end(db):
    brazil_album_uri = setup_test_collection(db)

    # Create a 1st Collection Item : a Carnaval photo
    NeoSchema.create_namespace(name="PHOTOS", prefix="photo-")
    carnaval_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "Dancers at Carnaval"}, new_uri=carnaval_photo_uri)

    Collections.link_to_collection_at_end(item_uri=carnaval_photo_uri,
                                          collection_uri=brazil_album_uri,
                                          membership_link_name="in_album")

    # Verify that the "Dancers at Carnaval" photo is linked to the "Brazil vacation", with position 0
    q = '''
        MATCH p=(:Photo {uri: $photo_uri, caption: "Dancers at Carnaval"})
                -[:in_album {pos: 0}]->
                (:`Photo Album` {name: "Brazil vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    #db.debug_query_print(q, data_binding={"carnaval_photo_uri": carnaval_photo_uri})
    result = db.query(q, data_binding={"photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Create a 2nd Collection Item : a canoeing photo
    canoe_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS", prefix="photo-")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "canoeing on the Amazon"}, new_uri=canoe_photo_uri)

    Collections.link_to_collection_at_end(item_uri=canoe_photo_uri,
                                          collection_uri=brazil_album_uri,
                                          membership_link_name="in_album")

    # Repeat the earlier check for the 1st photo
    result = db.query(q, data_binding={"photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1
    # And now check for the 2nd photo
    q = f'''
        MATCH p=(:Photo {{uri: $photo_uri, caption: "canoeing on the Amazon"}})
                -[:in_album {{pos: {Collections.DELTA_POS}}}]->
                (:`Photo Album` {{name: "Brazil vacation"}}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"photo_uri": canoe_photo_uri}, single_cell="number_paths")
    assert result == 1

    # NOTE: here we're not testing correctness under multiple concurrent calls



def test_is_collection(db):
    create_sample_collections_class(db)     # Creates a "Photo Album" Class

    # Create a Collection
    new_uri = NeoSchema.reserve_next_uri(prefix="album-")   # This starts a namespace with autoincrement
    assert new_uri == "album-1"

    NeoSchema.create_data_node(class_name="Photo Album",
                               properties ={"name": "Jamaica vacation"}, new_uri=new_uri)

    assert Collections.is_collection(collection_uri=new_uri)

    with pytest.raises(Exception):
        Collections.is_collection(collection_uri="some random string that is not a URI")


    # Create something that is NOT a collection
    NeoSchema.create_class_with_properties(name="Car",
                                           properties=["color", "uri"])
    NeoSchema.create_namespace(name="cars", prefix="c-")
    car_uri = NeoSchema.reserve_next_uri(namespace="cars")
    NeoSchema.create_data_node(class_name="Car", properties ={"color": "white"}, new_uri=car_uri)
    assert not Collections.is_collection(collection_uri=car_uri)



def test_relocate_to_other_collection_at_end(db):
    create_sample_collections_class(db)     # Creates a "Photo Album" Class

    # Create 2 Collections : "Jamaica" and a "Brazil" photo albums
    NeoSchema.create_namespace(name="ALBUMS", prefix="album-")
    jamaica_uri = NeoSchema.reserve_next_uri(namespace="ALBUMS")
    NeoSchema.create_data_node(class_name="Photo Album", properties ={"name": "Jamaica vacation"}, new_uri=jamaica_uri)
    brazil_uri = NeoSchema.reserve_next_uri(namespace="ALBUMS")
    NeoSchema.create_data_node(class_name="Photo Album",
                               properties ={"name": "Winter in Brazil"}, new_uri=brazil_uri)

    # Create a Collection Item : a Carnaval photo "accidentally" placed in the Jamaica album
    create_sample_collection_item_class()
    NeoSchema.create_namespace(name="PHOTOS", prefix="photo-")
    carnaval_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "Dancers at Carnaval"}, new_uri=carnaval_photo_uri)

    Collections.link_to_collection_at_end(item_uri=carnaval_photo_uri,
                                          collection_uri=jamaica_uri,
                                          membership_link_name="in_album")


    # Fail the attempt to relocate the carnaval photo from the Jamaica album to the Brazil album,
    # because of any of a number of errors
    with pytest.raises(Exception):      # Using wrong relationship name
        Collections.relocate_to_other_collection_at_end(item_uri=carnaval_photo_uri,
                                                        from_collection_uri=jamaica_uri, to_collection_uri=brazil_uri,
                                                        membership_rel_name="I don't exist")

    with pytest.raises(Exception):      # Reversed "from" and "to" Collections
        Collections.relocate_to_other_collection_at_end(item_uri=carnaval_photo_uri,
                                                        to_collection_uri=jamaica_uri, from_collection_uri=brazil_uri,
                                                        membership_rel_name="in_album")

    with pytest.raises(Exception):      # Non-existing Collection Items
        Collections.relocate_to_other_collection_at_end(item_uri="Some junk that does not exist",
                                                        from_collection_uri=jamaica_uri, to_collection_uri=brazil_uri,
                                                        membership_rel_name="in_album")

    with pytest.raises(Exception):      # Non-existing "from" Collection
        Collections.relocate_to_other_collection_at_end(item_uri=carnaval_photo_uri,
                                                        from_collection_uri="Nonexistent URI", to_collection_uri=brazil_uri,
                                                        membership_rel_name="in_album")

    # Verify that the carnaval photo is STILL linked to the Jamaica album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$carnaval_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"carnaval_photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Relocate the carnaval photo from the Jamaica album to the Brazil album
    Collections.relocate_to_other_collection_at_end(item_uri=carnaval_photo_uri,
                                                    from_collection_uri=jamaica_uri, to_collection_uri=brazil_uri,
                                                    membership_rel_name="in_album")

    # Verify that the carnaval photo is now linked to the Brazil album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$carnaval_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Winter in Brazil"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"carnaval_photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Create 2 other Collection Items : a photo of landing in Jamaica and a photo at a Jamaica resort,
    # both "accidentally" placed in the Brazil album
    landing_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "Landing in Jamaica"}, new_uri=landing_photo_uri)

    resort_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "At the resort in Jamaica"}, new_uri=resort_photo_uri)

    Collections.link_to_collection_at_end(item_uri=landing_photo_uri, collection_uri=brazil_uri,
                                          membership_link_name="in_album")

    Collections.link_to_collection_at_end(item_uri=resort_photo_uri, collection_uri=brazil_uri,
                                          membership_link_name="in_album")

    # At this point we have 3 photos ("Collection Items") - all of them in the Brazil album

    # Relocate the landing photo from the Brazil album to the Jamaica one
    Collections.relocate_to_other_collection_at_end(item_uri=landing_photo_uri,
                                                    from_collection_uri=brazil_uri, to_collection_uri=jamaica_uri,
                                                    membership_rel_name="in_album")

    # Verify that the landing photo is now linked to the Jamaica album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$landing_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"landing_photo_uri": landing_photo_uri}, single_cell="number_paths")
    assert result == 1

    # Relocate the resort photo from the Brazil album to the Jamaica one
    Collections.relocate_to_other_collection_at_end(item_uri=resort_photo_uri,
                                                    from_collection_uri=brazil_uri, to_collection_uri=jamaica_uri,
                                                    membership_rel_name="in_album")

    # Verify that the resort photo is now linked to the Jamaica album, with position 20
    q = '''
        MATCH p=(:Photo {uri:$resort_photo_uri})
        -[:in_album {pos: 20}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"resort_photo_uri": resort_photo_uri}, single_cell="number_paths")
    assert result == 1



def test_bulk_relocate_to_other_collection_at_end(db):

    create_sample_collections_class(db)     # Creates a "Photo Album" Class

    # Create 2 Collections : "Jamaica" and a "Brazil" photo albums
    NeoSchema.create_namespace(name="ALBUMS", prefix="album-")
    jamaica_uri = NeoSchema.reserve_next_uri(namespace="ALBUMS")
    NeoSchema.create_data_node(class_name="Photo Album", properties ={"name": "Jamaica vacation"}, new_uri=jamaica_uri)
    brazil_uri = NeoSchema.reserve_next_uri(namespace="ALBUMS")
    NeoSchema.create_data_node(class_name="Photo Album",
                               properties ={"name": "Winter in Brazil"}, new_uri=brazil_uri)

    # Create a Collection Item : a Carnaval photo "accidentally" placed in the Jamaica album
    create_sample_collection_item_class()
    NeoSchema.create_namespace(name="PHOTOS", prefix="photo-")
    carnaval_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS", prefix="photo-")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "Dancers at Carnaval"}, new_uri=carnaval_photo_uri)

    Collections.link_to_collection_at_end(item_uri=carnaval_photo_uri,
                                          collection_uri=jamaica_uri,
                                          membership_link_name="in_album")


    # Fail the attempt to relocate the carnaval photo from the Jamaica album to the Brazil album,
    # because of any of a number of errors

    # Using wrong relationship name
    assert 0 == \
        Collections.bulk_relocate_to_other_collection_at_end(items=[carnaval_photo_uri],
                                                        from_collection=jamaica_uri, to_collection=brazil_uri,
                                                        membership_rel_name="I don't exist")
    # Reversed "from" and "to" Collections
    assert 0 == \
        Collections.bulk_relocate_to_other_collection_at_end(items=["photo-1"],
                                                         from_collection="album-2", to_collection="album-1",
                                                         membership_rel_name="in_album")
    # Non-existing Collection Items
    assert 0 == \
        Collections.bulk_relocate_to_other_collection_at_end(items=["Some junk that does not exist"],
                                                        from_collection=jamaica_uri, to_collection=brazil_uri,
                                                        membership_rel_name="in_album")
    # Non-existing "from" Collection
    assert 0 == \
        Collections.bulk_relocate_to_other_collection_at_end(items=[carnaval_photo_uri],
                                                        from_collection="Nonexistent URI", to_collection=brazil_uri,
                                                        membership_rel_name="in_album")


    # Verify that the carnaval photo is STILL linked to the Jamaica album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$carnaval_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"carnaval_photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Relocate the carnaval photo from the Jamaica album to the empty Brazil album
    Collections.bulk_relocate_to_other_collection_at_end(items=carnaval_photo_uri,
                                                         from_collection=jamaica_uri, to_collection=brazil_uri,
                                                         membership_rel_name="in_album")

    # Verify that the carnaval photo is now linked to the Brazil album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$carnaval_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Winter in Brazil"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"carnaval_photo_uri": carnaval_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Create 2 other Collection Items : a photo of landing in Jamaica and a photo at a Jamaica resort,
    # both "accidentally" placed in the Brazil album
    landing_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "Landing in Jamaica"}, new_uri=landing_photo_uri)

    resort_photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
    NeoSchema.create_data_node(class_name="Photo",
                               properties ={"caption": "At the resort in Jamaica"}, new_uri=resort_photo_uri)

    Collections.link_to_collection_at_end(item_uri=landing_photo_uri, collection_uri=brazil_uri,
                                          membership_link_name="in_album")

    Collections.link_to_collection_at_end(item_uri=resort_photo_uri, collection_uri=brazil_uri,
                                          membership_link_name="in_album")

    # At this point we have 3 photos ("Collection Items") - all of them in the Brazil album

    # Relocate BOTH the landing photo and the the resort photo
    # from the Brazil album to the Jamaica one
    Collections.bulk_relocate_to_other_collection_at_end(items=[landing_photo_uri, resort_photo_uri],
                                                         from_collection=brazil_uri, to_collection=jamaica_uri,
                                                         membership_rel_name="in_album")

    # Verify that the landing photo is now linked to the Jamaica album, with position 0
    q = '''
        MATCH p=(:Photo {uri:$landing_photo_uri})
        -[:in_album {pos: 0}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"landing_photo_uri": landing_photo_uri}, single_cell="number_paths")
    assert result == 1

    # Verify that the resort photo is now linked to the Jamaica album, with position 20
    q = '''
        MATCH p=(:Photo {uri:$resort_photo_uri})
        -[:in_album {pos: 20}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, data_binding={"resort_photo_uri": resort_photo_uri}, single_cell="number_paths")
    assert result == 1


    # Add 2 photos to the Brazil album
    all_photo_uris = [0, 0]
    for i in range(2):
        photo_uri = NeoSchema.reserve_next_uri(namespace="PHOTOS")
        all_photo_uris[i] = photo_uri
        NeoSchema.create_data_node(class_name="Photo",
                                   properties ={"caption": f"photo_{i}"}, new_uri=photo_uri)
        Collections.link_to_collection_at_end(item_uri=photo_uri, collection_uri=brazil_uri,
                                              membership_link_name="in_album")

    #print("**************", all_photo_uris)
    # Now, relocate those 2 photos to the Jamaica album
    Collections.bulk_relocate_to_other_collection_at_end(items=all_photo_uris,
                                                         from_collection=brazil_uri, to_collection=jamaica_uri,
                                                         membership_rel_name="in_album")

    # Verify that those photos are now linked to the Jamaica album, with positions 40 and 60
    q = '''
        MATCH p=(:Photo {caption:"photo_0"})
        -[:in_album {pos: 40}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, single_cell="number_paths")
    assert result == 1

    q = '''
        MATCH p=(:Photo {caption:"photo_1"})
        -[:in_album {pos: 60}]->(:`Photo Album` {name: "Jamaica vacation"}) 
        RETURN COUNT(p) AS number_paths
        '''
    result = db.query(q, single_cell="number_paths")
    assert result == 1

    # Verify that just 1 photo remains in teh Brazil album
    match = db.match(key_name="name", key_value="Winter in Brazil")
    assert 1 == db.count_links(match=match, rel_name="in_album", rel_dir="IN", neighbor_labels = "Photo")
