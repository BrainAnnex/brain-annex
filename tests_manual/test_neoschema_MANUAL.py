# *** CAUTION! ***  The database gets cleared out during some of the tests!

import pytest
from neoaccess import NeoAccess
from BrainAnnex.modules.utilities.comparisons import compare_recordsets
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema



# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = NeoAccess(debug=False)
    NeoSchema.db = neo_obj
    #yield neo_obj      # Shouldn't need to reach directly into NeoAccess in these tests



#############   CLASS-related   #############

def test_create_class(db):
    NeoSchema.create_class("French Vocabulary")



def test_create_class_relationship(db):
    #french_class_id = NeoSchema.create_class("French Vocabulary")
    #foreign_class_id = NeoSchema.create_class("Foreign Vocabulary")
    NeoSchema.create_class_relationship(from_id=93, to_id=19, rel_name="INSTANCE_OF")



def test_get_class_relationships(db):
    schema_id = NeoSchema.get_class_id("Restaurants")
    print("schema_id is: ", schema_id)

    result = NeoSchema.get_class_relationships(schema_id)
    assert result == {'out': ['INSTANCE_OF', 'BA_located_in', 'BA_cuisine_type'], 'in': ['BA_served_at']}

    result = NeoSchema.get_class_relationships(schema_id, link_dir="BOTH")
    assert result == {'out': ['INSTANCE_OF', 'BA_located_in', 'BA_cuisine_type'], 'in': ['BA_served_at']}

    result = NeoSchema.get_class_relationships(schema_id, omit_instance=True)
    assert result == {'out': ['BA_located_in', 'BA_cuisine_type'], 'in': ['BA_served_at']}

    result = NeoSchema.get_class_relationships(schema_id, link_dir="OUT", omit_instance=True)
    assert result == ['BA_located_in', 'BA_cuisine_type']

    result = NeoSchema.get_class_relationships(schema_id, link_dir="IN")
    assert result == ['BA_served_at']




#############   PROPERTIES-RELATED   #############

def test_get_class_properties(db):
    prop_list = NeoSchema.get_class_properties(4)
    assert prop_list == ['French']

    prop_list = NeoSchema.get_class_properties(4, include_ancestors=True, sort_by_path_len="ASC")
    assert prop_list == ['French', 'English', 'notes']

    prop_list = NeoSchema.get_class_properties(1, include_ancestors=False)
    assert prop_list == ['German']



def test_add_properties_to_class(db):
    result = NeoSchema.add_properties_to_class(class_id=1, property_list=["Gender", "German"])
    assert result == 2

    """
    German_class_id = 1
    Profl_class_id = 2
    French_class_id = 4
    result = NeoSchema.add_properties_to_class(class_id = German_class_id, property_list=["German", "English", "Notes"])
    assert result == 3
    result = NeoSchema.add_properties_to_class(class_id = Profl_class_id, property_list=["name", "role", "location", "notes"])
    assert result == 4
    result = NeoSchema.add_properties_to_class(class_id = French_class_id, property_list=["French", "English", "Notes"])
    assert result == 3
    """



def test_remove_property_from_class(db):
    NeoSchema.remove_property_from_class(class_id=1, property_id=5)



#############   SCHEMA-CODE  RELATED   ###########

#############   DATA POINTS   ###########


def test_create_tree_from_dict(db):
    root_id = NeoSchema.create_tree_from_dict({}, class_name="Restaurants")




#############   EXPORT SCHEMA   ###########



def test_data_points_of_class(db):
    all_category_ids = NeoSchema.data_points_of_class("Categories")
    print(all_category_ids)
    assert len(all_category_ids) == 27


def test_allows_datanodes(db):
    print(NeoSchema.allows_data_nodes("Records"))
    print(NeoSchema.allows_data_nodes("Foreign Vocabulary"))
    print(NeoSchema.allows_data_nodes("German Vocabulary"))
    print(NeoSchema.allows_data_nodes("Quotes"))



def test_add_root_category(db):
    NeoSchema.add_data_point(class_name="Categories",
                             data_dict={"name": "ROOT (Home)", "remarks": "EVERYTHING - top level"},
                             labels="BA")



def test_initialize_schema(db):
    db.empty_dbase()    # Completely clear the database

    _ , German_class_id = NeoSchema.create_class("German Vocabulary")
    print(German_class_id)

    _ , Profl_class_id = NeoSchema.create_class("Profl Connections")
    print(Profl_class_id)

    NeoSchema.add_properties_to_class(class_id = German_class_id, property_list=["German", "English", "Notes"])

    NeoSchema.add_properties_to_class(class_id = Profl_class_id, property_list=["name", "role", "location", "notes"])

    q = '''
        MATCH (c:CLASS {schema_id:1})
        MERGE (c)<-[:SCHEMA]-(n:BA {German: "Guten", item_id:88})
        '''
    db.query(q)

    result = NeoSchema.all_properties("BA", "item_id", 88)
    assert result == ['Notes', 'English', 'German']     # Note: order might differ!





def test_get_class_instances(db):
    result = NeoSchema.get_class_instances("Records", leaf_only=True)
    print(result)



def test_new_class_with_properties(db):
    """
    _, new_id = NeoSchema.create_class_with_properties("Images",
                                                 ["width", "caption"], code="i"
                                                 )
    """
    _, new_id = NeoSchema.create_class_with_properties(class_name="Documents",
                                                       property_list=["caption"],
                                                       code="d",
                                                       class_to_link_to="Media"
                                                       )
    assert NeoSchema.valid_schema_id(new_id)
    print("test_new_class_with_properties() - New class was assigned schema id: ", new_id)

    #NeoSchema.create_class_with_properties("Category", ["name", "remarks"])
    #NeoSchema.create_class_with_properties("Foreign Vocabulary", ["English", "notes"])



def test_unlink_classes(db):
    status = NeoSchema.unlink_classes(26, 15)
    assert status == True



def test_rename_class_rel(db):
    status = NeoSchema.rename_class_rel(from_class=1, to_class=19, new_rel_name="INSTANCE_OF")
    assert status == True



def test_next_available_id(db):

    db.empty_dbase()    # Completely clear the database

    # Try on empty database
    assert NeoSchema.next_available_id() == 1

    db.create_node("CLASS", {"schema_id": 1})
    assert NeoSchema.next_available_id() == 2

    db.create_node("CLASS", {"schema_id": 2})
    assert NeoSchema.next_available_id() == 3

    db.create_node("PROPERTY", {"schema_id": 3})
    assert NeoSchema.next_available_id() == 4

    db.create_node("some_other_label", {"schema_id": 12345})
    assert NeoSchema.next_available_id() == 4      # Unaffected by other labels

    db.create_node("CLASS", {"schema_id": 100})
    assert NeoSchema.next_available_id() == 101

    db.create_node("PROPERTY", {"schema_id": 665})
    assert NeoSchema.next_available_id() == 666

    #print(NeoSchema.next_available_id())



def test_next_available_datapoint_id(db):
    print(NeoSchema.next_available_datapoint_id())




###########   Related to Schema CODES   ###########

def test_get_schema_code(db):
    # TODO: assumes pre-set database!
    assert NeoSchema.get_schema_code("Restaurants") == "r"
    assert NeoSchema.get_schema_code("Entrees") == "r"
    assert NeoSchema.get_schema_code("Records") == "r"
    assert NeoSchema.get_schema_code("Foreign Vocabulary") == "r"
    assert NeoSchema.get_schema_code("French Vocabulary") == "r"
    assert NeoSchema.get_schema_code("Notes") == "n"
    assert NeoSchema.get_schema_code("Category") == "cat"
    assert NeoSchema.get_schema_code("Media") == ""



def test_get_schema_id(db):
    # TODO: assumes pre-set database!
    assert NeoSchema.get_schema_id("h") == 31
    assert NeoSchema.get_schema_id("n") == 23
    assert NeoSchema.get_schema_id("junk") == -1




###########   DATA POINTS   ###########

def test_add_data_point(db):

    new_id = NeoSchema.add_data_point(class_name="German Vocabulary",
                                      data_dict = {"German": "Tür",
                                                   "English": "door"
                                                   },
                                      labels="BA",
                                      connected_to_id=60, connected_to_labels="BA",
                                      rel_name="BA_in_category", rel_prop_key="pos", rel_prop_value=120
                                      )
    """
    new_id = NeoSchema.add_data_point(class_name="Restaurants",
                                      data_dict = {"name": "The Red Sea",
                                       "address": "5200 Claremont Ave, at Telegraph",
                                       "phone": "(510) 655-3757",
                                       "website": "https://redseaoakland.com/",
                                       "eval": "SUPERB"
                                      },
                                      labels="BA",
                                      connected_to_id=535, connected_to_labels="BA", rel_name="BA_in_category", rel_dir="OUT",
                                      rel_prop_key="pos", rel_prop_value=100
                                      )

    
    status = NeoSchema.add_data_point("Entrees",
                                      {"name": "mushrooms pie", "eval": "OK"},
                                      labels="BA",
                                      connected_to_id=540, connected_to_labels="BA", rel_name="BA_served_at", rel_dir="OUT"
                                      )
                    
    status = NeoSchema.add_data_point("Cars",
                                      {"make": "Toyota", "color": "white"},
                                      labels="car",
                                      connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT"
                                      )
    """
    print("New data point assigned ID: ", new_id)



def test_add_existing_data_point(db):

    neo_id = db.create_node("BA", {"note": "TO DELETE!"})
    new_item_ID = NeoSchema.register_existing_data_point(schema_id=19, existing_neo_id=neo_id)
    print("new_item_ID: ", new_item_ID)

    neo_id = db.create_node("BA", {"formula": "NH3"})
    new_item_ID = NeoSchema.register_existing_data_point(class_name="Chemicals", existing_neo_id=neo_id)
    print("new_item_ID: ", new_item_ID)



def test_delete_data_point(db):
    pass



def test_add_data_relationship(db):
    #status = NeoSchema.add_data_relationship(subcategory_id=536, category_id=540, rel_name="BA_served_at")
    #status = NeoSchema.add_data_relationship(subcategory_id=514, category_id=544, rel_name="BA_subcategory_of")
    #status = NeoSchema.add_data_relationship(subcategory_id=541, category_id=535, rel_name="BA_in_category")
    number_added = NeoSchema.add_data_relationship(from_id=9, to_id=690, rel_name="BA_testing")
    assert number_added == 1



def test_remove_data_relationship(db):
    NeoSchema.remove_data_relationship(from_id=3, to_id=1, rel_name="BA_subcategory_of")
