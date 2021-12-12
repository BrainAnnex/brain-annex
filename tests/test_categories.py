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




################################    COLLECTIONS    ########################################

def test_is_collection():
    result = Collections.is_collection(collection_id=792)
    print(result)



def test_collection_size():
    number_items_attached = Collections.collection_size(collection_id=795, membership_rel_name="BA_in_category", skip_check=False)
    print(number_items_attached)



def test_add_to_collection_at_end():
    new_item_id = Collections.add_to_collection_at_end(collection_id=708, membership_rel_name="BA_in_category",
                                                       item_class_name="Headers", item_properties={"text": "New Caption, at the end"})
    print("new_item_id:", new_item_id)


def test_add_to_collection_at_beginning():
    new_item_id = Collections.add_to_collection_at_beginning(collection_id=708, membership_rel_name="BA_in_category",
                                                       item_class_name="Headers", item_properties={"text": "New Caption, at the very top"})
    print("new_item_id:", new_item_id)


def test_add_to_collection_after_element():
    new_item_id = \
        Collections.add_to_collection_after_element(collection_id=708, membership_rel_name="BA_in_category",
                                                     item_class_name="Headers", item_properties={"text": "Caption 4, inserted 'after element'"},
                                                     insert_after=729)
    print("new_item_id: ", new_item_id)


def test_shift_down():
    number_shifted = Collections.shift_down(collection_id=708, membership_rel_name="BA_in_category",
                                            first_to_move=41)
    print("number_shifted: ", number_shifted)


"""
For testing on Neo4j browser:

MATCH (n:BA)-[r :BA_in_category]->(cat:BA {item_id: 708}) RETURN r.pos, n.text, n.name, n.item_id, n.basename ORDER BY r.pos

MATCH (c:BA {item_id: 708}) <- [r :BA_in_category] - (n :BA)
RETURN r.pos, n.item_id, n.text, n.basename
ORDER by r.pos

MATCH (n:BA {item_id: xxx}) RETURN n

MATCH (n:BA {item_id: xxx}) DETACH DELETE n

"""