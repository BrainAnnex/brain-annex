import pytest
from neoaccess import GraphAccess
from brainannex.neoschema.neo_schema import NeoSchema
from brainannex.categories import Categories


# Provide a database connection that can be used by the various tests that need it
@pytest.fixture(scope="module")
def db():
    neo_obj = GraphAccess(debug=True)
    Categories.db = neo_obj
    NeoSchema.db = neo_obj
    yield neo_obj


def test_count_subcategories(db):
    count = Categories.count_subcategories(792)
    print(count)


def test_count_parent_categories(db):
    count = Categories.count_parent_categories(61)
    print(count)



def test_get_subcategories(db):
    result = Categories.get_subcategories(1)
    print(result)

    result = Categories.get_subcategories(527)
    print(result)


def test_get_parent_categories(db):
    result = Categories.get_parent_categories(544)
    print(result)



def test_create_parent_map(db):
    Categories.create_parent_map(799)     # single path, 1-hop
    Categories.create_parent_map(876)     # single path, 2-hop
    Categories.create_parent_map(823)     # single path, 3-hop

    Categories.create_parent_map(814)     # 2 paths, a 2-hop and a 3-hop one

    Categories.create_parent_map(1)       # the root



def test_bread_crumbs(db):
    print(Categories.create_bread_crumbs(1))   # [1]
    print(Categories.create_bread_crumbs(799)) # ['START_CONTAINER', [1, 'ARROW', 799], 'END_CONTAINER']
    print(Categories.create_bread_crumbs(876)) # ['START_CONTAINER', [1, 'ARROW', 799, 'ARROW', 876], 'END_CONTAINER']
    print(Categories.create_bread_crumbs(823)) # ['START_CONTAINER', [1, 'ARROW', 544, 'ARROW', 709, 'ARROW', 823], 'END_CONTAINER']

    print(Categories.create_bread_crumbs(814))
    # [
    #   'START_CONTAINER',
    #   ['START_BLOCK', 'START_LINE', [1, 'ARROW', 799, 'ARROW', 526], 'END_LINE', 'CLEAR_RIGHT', 'START_LINE', [1, 'ARROW', 61], 'END_LINE', 'END_BLOCK', 'ARROW', 814],
    #   'END_CONTAINER'
    # ]


def test_add_content_at_end(db):
    new_uri = Categories.add_content_at_end(category_uri=708,
                                            item_class_name="Header",
                                            item_properties={"text": "This is a New Caption, added at the end"})
    print("new_uri:", new_uri)


def test_add_content_at_beginning(db):
    new_uri = Categories.add_content_at_beginning(category_uri=708,
                                                  item_class_name="Header",
                                                  item_properties={"text": "This is a New Caption, added before anything else"})
    print("new_uri:", new_uri)


def test_add_content_after_element(db):
    new_uri = \
        Categories.add_content_after_element(category_uri=708,
                                             item_class_name="Header", item_properties={"text": "Caption 4, inserted 'after element'"},
                                             insert_after=729)
    print("new_uri: ", new_uri)


def test_delete_category(db):
    Categories.delete_category(uri="796")


def test_add_subcategory_relationship(db):
    Categories.add_subcategory_relationship(subcategory_id=3, category_id=526)



def test_check_for_duplicates(db):
    result = Categories.check_for_duplicates(category_name="some name")
    print(result)
    assert result == []


def test_check_all_categories_for_duplicates(db):
    result = Categories.check_all_categories_for_duplicates()
    print(result)
    assert result == ""



"""
For testing on Neo4j browser:

MATCH (n:BA)-[r :BA_in_category]->(cat:BA {uri: 708}) RETURN r.pos, n.text, n.name, n.uri, n.basename ORDER BY r.pos

MATCH (c:BA {uri: 708}) <- [r :BA_in_category] - (n :BA)
RETURN r.pos, n.uri, n.text, n.basename
ORDER by r.pos

MATCH (n:BA {uri: xxx}) RETURN n

MATCH (n:BA {uri: xxx}) DETACH DELETE n

"""