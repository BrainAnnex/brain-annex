from brainannex.categories import Collections



def test_is_collection():
    result = Collections.is_collection(collection_id=792)
    print(result)



def test_collection_size():
    number_items_attached = Collections.collection_size(collection_id=795, membership_rel_name="BA_in_category", skip_check=False)
    print(number_items_attached)



def test_add_to_collection_at_end():
    new_uri = Collections.add_to_collection_at_end(collection_uri=708, membership_rel_name="BA_in_category",
                                                   item_class_name="Headers", item_properties={"text": "New Caption, at the end"})
    print("new_uri:", new_uri)


def test_add_to_collection_at_beginning():
    new_uri = Collections.add_to_collection_at_beginning(collection_uri=708, membership_rel_name="BA_in_category",
                                                         item_class_name="Headers", item_properties={"text": "New Caption, at the very top"})
    print("new_uri:", new_uri)


def test_add_to_collection_after_element():
    new_uri = \
        Collections.add_to_collection_after_element(collection_uri=708, membership_rel_name="BA_in_category",
                                                    item_class_name="Headers", item_properties={"text": "Caption 4, inserted 'after element'"},
                                                    insert_after_uri=729)
    print("new_uri: ", new_uri)


def test_shift_down():
    number_shifted = Collections.shift_down(collection_id=708, membership_rel_name="BA_in_category",
                                            first_to_move=41)
    print("number_shifted: ", number_shifted)
