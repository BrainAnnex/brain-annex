from BrainAnnex.modules.categories.categories import Categories, Collections


def test_count_subcategories():
    count = Categories.count_subcategories(792)
    print(count)


def test_count_parent_categories():
    count = Categories.count_parent_categories(61)
    print(count)



def test_get_subcategories():
    result = Categories.get_subcategories(1)
    print(result)

    result = Categories.get_subcategories(527)
    print(result)


def test_get_parent_categories():
    result = Categories.get_parent_categories(544)
    print(result)



def test_paths_from_root():
    Categories.paths_from_root(799)     # single path, 1-hop
    Categories.paths_from_root(876)     # single path, 2-hop
    Categories.paths_from_root(823)     # single path, 2-hop

    Categories.paths_from_root(814)     # 2 paths, a 2-hop and a 3-hop one

    Categories.paths_from_root(1)       # no results




def test_add_content_at_end():
    new_item_id = Categories.add_content_at_end(category_id=708,
                                                item_class_name="Headers",
                                                item_properties={"text": "This is a New Caption, added at the end"})
    print("new_item_id:", new_item_id)


def test_add_content_at_beginning():
    new_item_id = Categories.add_content_at_beginning(category_id=708,
                                                item_class_name="Headers",
                                                item_properties={"text": "This is a New Caption, added before anything else"})
    print("new_item_id:", new_item_id)


def test_add_content_after_element():
    new_item_id = \
        Categories.add_content_after_element(category_id=708,
                                                item_class_name="Headers", item_properties={"text": "Caption 4, inserted 'after element'"},
                                                insert_after=729)
    print("new_item_id: ", new_item_id)


def test_delete_category():
    Categories.delete_category(category_id=796)


def test_add_subcategory_relationship():
    Categories.add_subcategory_relationship(subcategory_id=3, category_id=526)



def test_remove_subcategory_relationship():
    Categories.remove_subcategory_relationship(subcategory_id=535, category_id=1)




"""
For testing on Neo4j browser:

MATCH (n:BA)-[r :BA_in_category]->(cat:BA {item_id: 708}) RETURN r.pos, n.text, n.name, n.item_id, n.basename ORDER BY r.pos

MATCH (c:BA {item_id: 708}) <- [r :BA_in_category] - (n :BA)
RETURN r.pos, n.item_id, n.text, n.basename
ORDER by r.pos

MATCH (n:BA {item_id: xxx}) RETURN n

MATCH (n:BA {item_id: xxx}) DETACH DELETE n

"""