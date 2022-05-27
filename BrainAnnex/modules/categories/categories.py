from BrainAnnex.modules.neo_access import neo_access
from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema
from typing import Union

# 2 classes: "Categories" and  "Collections"


class Categories:
    """
    Library for Category-related operations.

    Contains the following groups of methods:
        1. LOOKUP
        2. UPDATE
        3. POSITIONING WITHIN CATEGORIES
    """

    db = None   # MUST be set before using this class!
                # Database-interface object is a CLASS variable, accessible as cls.db

    DELTA_POS = 20      # Arbitrary shift in "pos" value; best to be even, and not too small nor too large



    ##########  1. LOOKUP  ##########

    @classmethod
    def get_category_info(cls, category_id) -> dict:
        """
        Return the Name and Remarks attached to the given Category.  If not found, return an empty dictionary

        :return:    The Category's name (or a blank dictionary if not found)
                    EXAMPLE:  {"item_id": 123, "name": "Astronomy", "remarks": "except cosmology"}
        """
        # Note: since the category_id is a primary key,
        #       specifying a value for the labels and the "schema_code" property is for redundancy
        return NeoSchema.fetch_data_point(item_id=category_id, labels="BA", properties={"schema_code": "cat"})



    @classmethod
    def is_root_category(cls, category_id: int) -> bool:
        """
        Return True if the given ID corresponds to the ROOT Category, or False otherwise

        TODO: maybe raise an Exception if the argument isn't a valid ID
        :param category_id: An integer with the item_id of a Category node
        :return:            True if the given ID corresponds to the ROOT Category, or False otherwise
        """
        # NOTE: historically, 1 has been used for the ROOT Category; however, now that item_id is shared
        #       among all types of plugins, maybe a different approach would be better (such as an attribute in the node)
        return True if category_id == 1 else False



    @classmethod
    def count_subcategories(cls, category_id: int) -> int:
        """
        Return the number of (direct) Subcategories of the given Category
        TODO: maybe turn into a method of NeoSchema :  count_inbound_rels(labels="BA, item_id=category_id, class_name="Categories")

        :param category_id: An integer with a value of the "item_id" field
                            that identifies a data node containing the desired Category
        :return:            The number of (direct) Subcategories of the given Category; possibly, zero
        """

        match = cls.db.find(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        return cls.db.count_links(match, rel_name="BA_subcategory_of", rel_dir="IN")


    @classmethod
    def count_parent_categories(cls, category_id: int) -> int:
        """
        Return the number of (direct) Subcategories of the given Category
        TODO: maybe turn into a method of NeoSchema :  count_outbound_rels(labels="BA, item_id=category_id, class_name="Categories")

        :param category_id: An integer with a value of the "item_id" field
                            that identifies a data node containing the desired Category
        :return:            The number of (direct) parent categories of the given Category; possibly, zero
        """

        match = cls.db.find(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        return cls.db.count_links(match, rel_name="BA_subcategory_of", rel_dir="OUT")



    @classmethod
    def get_subcategories(cls, category_id: int) -> [dict]:
        """
        Return all the (direct) Subcategories of the given category,
        as a list of dictionaries with all the keys of the Category Class
        EXAMPLE:
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :param category_id: An integer with a value of the "item_id" field
                                    that identifies a data node containing the desired Category
        :return:            A list of dictionaries
        """
        match = cls.db.find(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        return cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="IN",
                                     neighbor_labels="BA")



    @classmethod
    def get_parent_categories(cls, category_id) -> [dict]:
        """
        Return all the (direct) parent categories of the given category,
        as a list of dictionaries with all the keys of the Category Class
        EXAMPLE:
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :param category_id:
        :return:            A list of dictionaries
        """
        match = cls.db.find(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        return cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="OUT",
                                     neighbor_labels="BA")



    @classmethod
    def get_all_categories(cls, exclude_root=True, include_remarks=False) -> [dict]:
        """
        Return all the existing Categories - possibly except the root -
        as a list of dictionaries with keys 'item_id' and 'name',
        sorted by name.

        EXAMPLES:
            [{'item_id': 3, 'name': 'Hobbies'}, {'item_id': 2, 'name': 'Work'}]
            [{'item_id': 3, 'name': 'Hobbies'}, {'item_id': 2, 'name': 'Work', 'remarks': 'Current or past'}]

        :return:    A list of dictionaries
        """
        clause = ""
        if exclude_root:
            clause = "WHERE cat.item_id <> 1"

        remarks_subquery = ", cat.remarks AS remarks"  if include_remarks else ""

        q =  f'''
             MATCH (cat:BA {{schema_code:"cat"}})
             {clause}
             RETURN cat.item_id AS item_id, cat.name AS name {remarks_subquery}
             ORDER BY toLower(cat.name)
             '''
        # Notes: 1 is the ROOT category.
        # Sorting must be done across consistent capitalization, or "GSK" will appear before "German"!

        result =  cls.db.query(q)

        # If remarks are being included, ditch all the MISSING "remarks" values
        if include_remarks:
            for item in result:
                if item["remarks"] is None:
                    del item["remarks"]     # To avoid a dictionary entry of the type 'remarks': None

        return result



    @classmethod
    def create_parent_map(cls, category_id: int) -> dict:
        """
        Taking into account the set of all the ancestor nodes of the given Category (i.e. all its super-categories),
        create and return a dictionary that maps each of the Category IDs of the nodes of that set
        into list of ID's of its parent Categories.

        :param category_id:
        :return:            A dictionary mapping integers into lists of integers
                            EXAMPLES:       {799: [1]}
                                            {823: [709], 709: [544], 544: [1]}              # A single 3-hop path from Category 823 to the root (1)
                                            {814: [526, 61], 61: [1], 526: [799], 799: [1]} # Two paths from Category 514 to the root
        """
        # Based on the "BA_subcategory_of" relationship,
        #       extract a child (c) - parent (p) map,
        #       where the child is an ancestor node of the given Category node
        q = '''
            MATCH (:BA {schema_code:"cat", item_id:$category_id})-[:BA_subcategory_of*0..5]->(c :BA)-[:BA_subcategory_of]->(p)
            WITH c, collect(p.item_id) AS all_parents
            RETURN c.item_id AS item_id, all_parents
            '''
        result = cls.db.query(q, {"category_id": category_id})      # A list of dictionaries
        # EXAMPLE:  [{'item_id': 876, 'all_parents': [799]}, {'item_id': 799, 'all_parents': [1]}]

        parent_map = {}
        for entry in result:
            key = entry["item_id"]
            value = entry["all_parents"]
            parent_map[key] = value

        #print(parent_map, "\n")
        return parent_map



    @classmethod
    def paths_from_root(cls, category_id: int):     # *** NOT IN CURRENT USE ***
        """
        Extract and return all the existing paths from the ROOT category to the given one,
        traversing the relationship "BA_subcategory_of"

        :param category_id:
        :return:            A list of of paths.  Each path is a list of nodes along it.  Each node is a dict of its properties
                            EXAMPLE 1:
                                [[{'name': 'HOME', 'item_id': 1, 'schema_code': 'cat', 'remarks': 'ROOT NODE'}, {'name': 'Jobs', 'item_id': 799, 'schema_code': 'cat'}]]
                            EXAMPLE 2:
                                [
                                 [{'name': 'HOME', 'item_id': 1, 'schema_code': 'cat', 'remarks': 'ROOT NODE'}, {'name': 'Food', 'item_id': 61, 'schema_code': 'cat'}, {'name': 'Nutrition', 'item_id': 814, 'schema_code': 'cat'}],
                                 [{'name': 'HOME', 'item_id': 1, 'schema_code': 'cat', 'remarks': 'ROOT NODE'}, {'name': 'Health', 'item_id': 799, 'schema_code': 'cat'}, {'name': 'Nutrition', 'item_id': 814, 'schema_code': 'cat'}]
                                ]

        """
        # Look up and return all the paths (p) from the ROOT category (ID 1) to the given one,
        #   following 1 or more hops along the relationship "BA_subcategory_of"
        q = '''
            MATCH p=(root :BA {schema_code:"cat", item_id:1})<-[:BA_subcategory_of*]-(c :BA {schema_code:"cat", item_id:$category_id}) 
            RETURN p
            '''

        result = cls.db.query(q, {"category_id": category_id})
        # EXAMPLE:
        #   [{'p': [{'name': 'HOME', 'item_id': 1, 'schema_code': 'cat', 'remarks': 'ROOT NODE'}, 'BA_subcategory_of', {'name': 'Jobs', 'item_id': 799, 'schema_code': 'cat'}]}]
        #print(f"\n*****  PATHS TO CATEGORY {category_id} ***********")
        #print(f"result contains {len(result)} elements")
        #print(result)

        all_paths = []
        for path_map in result:
            #print(path_map)
            path = path_map["p"]

            node_path = []
            for i, step in enumerate(path):
                # Only take the 0-th, 2nd, 4th, etc. elements, skipping over the relationship name
                if i%2 == 0:
                    node_path.append(step)

            all_paths.append(node_path)

        print(all_paths, "\n")
        return all_paths

        # Desired intermediate structure:
        example = \
        [
            [
                {'name': 'HOME', 'item_id': 1, 'remarks': 'ROOT NODE'},
                {'name': 'Professional Networking', 'item_id': 61},
                {'name': 'People at XYZ', 'item_id': 814}
            ],
            [
                {'name': 'HOME', 'item_id': 1, 'remarks': 'ROOT NODE'},
                {'name': 'Jobs', 'item_id': 799},
                {'name': 'XYZ', 'item_id': 526},
                {'name': 'People at XYZ', 'item_id': 814}
            ]
        ]

        # Desired final structure:
        parents_map = {814: [526, 61], 526: [799], 799: [1], 61: [1], 1: []}
        names = {814: 'People at GSK', 526: 'GSK', 799: 'Jobs', 61: 'Professional Networking', 1: 'HOME'
                 } # Ignoring `remarks` field for now

        # Maybe encode a tree in JSON
        json_data = [[['HOME', 'Jobs', 'GSK'] , ['HOME', 'Professional Networking']], 'People at GSK']
        # OR
        json_data_2 = ['People at GSK', [ ['Professional Networking', 'HOME'],  ['GSK', ['Jobs', 'HOME']] ] ]



    @classmethod
    def create_bread_crumbs(cls, category_ID) -> list:
        """
        Return a list of Category ID's together with token strings, providing directives for the HTML structure of
        the bread crumbs

        :param category_ID:
        :return:            EXAMPLE 1:  [1]
                            EXAMPLE 2:  ['START_CONTAINER', [1, 'ARROW', 799, 'ARROW', 876], 'END_CONTAINER']
                            EXAMPLE 3:
                                [
                                    'START_CONTAINER',
                                    ['START_BLOCK',
                                                    'START_LINE', [1, 'ARROW', 799, 'ARROW', 526], 'END_LINE', 'CLEAR_RIGHT',
                                                    'START_LINE', [1, 'ARROW', 61], 'END_LINE',
                                     'END_BLOCK', 'ARROW', 814],
                                    'END_CONTAINER'
                                ]
        """
        if category_ID == 1:    # If it is the root
            return [1]

        # If we get here, we're NOT at the root.

        parents_map = cls.create_parent_map(category_ID)
        #print("In create_bread_crumbs().  parents_map: ", parents_map)

        # Put together a block (to be turned into an HTML element by the front end) depicting all possible
        # breadcrumb paths from the ROOT to the current category
        return ["START_CONTAINER", cls.recursive(category_ID, parents_map) ,"END_CONTAINER"]


    @classmethod
    def recursive(cls, category_ID, parents_map) -> list:
        """

        :param category_ID:
        :param parents_map:
        :return:
        """
        if category_ID == 1:    # If it is the root
            return [1]

        parent_list = parents_map.get(category_ID, [])

        if len(parent_list) == 0:
            return []    # TODO: generate warning
        elif len(parent_list) == 1:     # If just one parent
            parent_id = parent_list[0]
            bc = cls.recursive(parent_id, parents_map)
            bc.append("ARROW")
            bc.append(category_ID)
            return bc
        else:                           # If multiple parents
            bc = ["START_BLOCK"]
            for parent_id in parent_list:
                bc.append("START_LINE")
                bc.append(cls.recursive(parent_id, parents_map))
                bc.append("END_LINE")
                if parent_id != parent_list[-1]:    # Skip if we're dealing with last element
                    bc.append("CLEAR_RIGHT")

            bc.append("END_BLOCK")
            bc.append("ARROW")
            bc.append(category_ID)
            return bc




    ##########  2. UPDATE  ##########

    @classmethod
    def add_subcategory(cls, post_data: dict) -> int:
        """
        Add a new Subcategory to a given Category
        :param post_data:   Dictionary with the following keys:
                                category_id                     To identify the Category to which to add a Subcategory
                                subcategory_name                The name to give to the new Subcategory
                                subcategory_remarks (optional)

        :return:                If successful, an integer with auto-increment "item_id" value of the node just created;
                                otherwise, an Exception is raised
        """
        category_id = post_data.get("category_id")
        if not category_id:
            raise Exception(f"category_id is missing")

        try:
            category_id = int(category_id)
        except Exception as ex:
            raise Exception(f"category_id is not an integer (value passed {category_id}). {ex}")

        subcategory_name = post_data.get("subcategory_name")
        if not subcategory_name:
            raise Exception(f"subcategory_name is missing")

        subcategory_remarks = post_data.get("subcategory_remarks")

        data_dict = {"name": subcategory_name}
        if subcategory_remarks:
            data_dict["remarks"] = subcategory_remarks

        return NeoSchema.add_data_point(class_name="Categories",
                                        data_dict=data_dict, labels="BA",
                                        connected_to_id=category_id, connected_to_labels="BA",
                                        rel_name="BA_subcategory_of", rel_dir="OUT"
                                        )



    @classmethod
    def delete_category(cls, category_id: int) -> None:
        """
        Delete the specified Category, provided that there are no Content Items linked to it.
        In case of error or failure, an Exception is raised.

        :param category_id: The "item_id" integer value identifying the desired Category
        :return:            None
        """

        if cls.is_root_category(category_id):
            raise Exception("Cannot delete the Root node")

        # First, make sure that there are no Content Items linked to this Category
        number_items_attached = Collections.collection_size(collection_id=category_id, membership_rel_name="BA_in_category")

        if number_items_attached > 0:
            raise Exception(f"Cannot delete the requested Category (ID {category_id}) because it has Content Items attached to it: {number_items_attached} item(s). "
                            f"You need to first untag or delete all Items associated to it")

        if cls.count_subcategories(category_id) > 0:
            raise Exception(f"Cannot delete the requested Category (ID {category_id}) because it has sub-categories. Use the Category manager to first sever those relationships")

        number_deleted = NeoSchema.delete_data_point(item_id=category_id, labels="BA")

        if number_deleted != 1:
            raise Exception(f"Failed to delete the requested Category (ID {category_id})")



    @classmethod
    def add_subcategory_relationship(cls, subcategory_id: int, category_id: int) -> None:
        """
        TODO: phase out.  Probably, no longer really needed (the new API takes care
        of this largely in the core module.)

        Add a sub-category ("BA_subcategory_of") relationship between the specified categories.
        If the requested new relationship cannot be created (for example, if it already exists),
        raise an Exception

        TODO: verify that the category ID's are legit

        :param subcategory_id:
        :param category_id:
        :return:            None.  If the requested new relationship could not be created, raise an Exception
        """
        # Notice that, because the relationship is called a SUB-category, the subcategory is the "parent"
        #   (the originator) of the relationship
        try:
            NeoSchema.add_data_relationship(from_id=subcategory_id, to_id=category_id,
                                            rel_name="BA_subcategory_of", id_type="item_id")
        except Exception as ex:
            raise Exception(f"Unable to create a subcategory relationship. {ex}")




    """
    NOTE: the next 2 methods, below, may be the future prototype of plugin-specific methods...
          Nothing is returned if all is good, but an Exception is raised in case of problems.
          The methods only handle the plugin-specific part; the "main action" is done by the core method,
          AFTER calling this method (if provided)
    """

    @classmethod
    def add_relationship(cls, from_id: int, to_id :int,
                        rel_name: str) -> None:
        """
        If any restriction would apply to adding the parent/child relationship between the specified categories,
        raise an Exception.

        The restriction are:
            1) the subcategory node cannot be the Root Category
            2) a category cannot be a subcategory of itself

        NOTE: the "BA_subcategory_of" relationship goes FROM the subcategory TO the parent category node

        :param from_id:     Integer with the item_id of the subcategory node
        :param to_id:       Integer with the item_id of the parent-category node
        :param rel_name:    NOT USED
        :return:            None.  If the requested new relationship should not be created, raise an Exception
        """
        # If the sub-category is the Root Category, raise an Exception
        if cls.is_root_category(from_id):
            raise Exception("Cannot add the relationship because the Root Category cannot be made a subcategory of something else")

        # If the parent and the child are the same, raise an Exception
        if from_id == to_id:
            raise Exception("Cannot add a relationship from a Category to itself")



    @classmethod
    def remove_relationship(cls, from_id: int, to_id :int,
                            rel_name: str) -> None:
        """
        If any restriction would apply to removing the parent/child relationship between the specified categories,
        raise an Exception.

        The restriction is:
            *) the subcategory node cannot become orphaned as a result of the deletion

        NOTE: the "BA_subcategory_of" relationship goes FROM the subcategory TO the parent category node

        :param from_id:     Integer with the item_id of the subcategory node
        :param to_id:       NOT USED.  Integer with the item_id of the parent-category node
        :param rel_name:    NOT USED
        :return:            None.  If the requested new relationship should not be deleted, raise an Exception
        """
        # If the sub-category has only one parent, raise an Exception
        #print(f"In Category.remove_relationship(). from_id = {from_id}  Parent categories : {cls.get_parent_categories(from_id)}")
        if len(cls.get_parent_categories(from_id)) == 1:
            raise Exception("Cannot sever the relationship because that would leave the sub-category orphaned (i.e. with no parent categories)")




    @classmethod
    def switch_parent_category_relationship(cls, child_id: int, old_parent_id: int, new_parent_id: int) -> None:
        """
        Switch a parent/child relationship between the specified categories.
        Take the child away from the old parent, and re-assign to the new one.

        :param child_id:
        :param old_parent_id:
        :param new_parent_id:
        :return:
        """
        #TODO: make use of cls.db.reattach_node()
        pass    # switchParentNode($childID, $oldParentID, $newParentID)


    @classmethod
    def switch_subcategory_relationship(cls, parent_id: int, old_child_id: int, new_child_id: int) -> None:
        """
        Switch a parent/child relationship between the specified categories.
        From the parent, take the old child away , and replace it with the new child.

        :param parent_id:
        :param old_child_id:
        :param new_child_id:
        :return:
        """
        #TODO: make use of cls.db.reattach_node()
        pass    # switchChildNode($parentID, $oldChildID, $newChildID)




    ########  ADDING ITEMS TO THE CATEGORY  ########

    @classmethod
    def add_content_media(cls, category_id:int, properties: dict, pos=None) -> None:
        """
        Update the database, to reflect the upload of an image file, and its linking to the specified Category.
        TODO: media is currently added to the END of the Category page.  Not using the "pos" argument
        TODO: superseded by add_content_at_end()

        :param category_id: The integer "item_ID" of the Category to which this new Content Media is to be attached
        :param properties:  A dictionary with keys "width", "height", "caption","basename", "suffix" (TODO: verify against schema)
        :param pos:         TODO: currently not in use
        :return:            None
        """
        print("In add_content_media().  properties: ", properties)
        print(f"    category_id: {category_id}")

        cls.add_content_at_end(category_id=category_id, item_class_name="Images", item_properties=properties)



    @classmethod
    def add_content_at_beginning(cls, category_id:int, item_class_name: str, item_properties: dict, new_item_id=None) -> int:
        """
        Add a new Content Item, with the given properties and Class, to the beginning of the specified Category.

        :param category_id:     The integer "item_ID" of the Category to which this new Content Media is to be attached
        :param item_class_name: For example, "Images"
        :param item_properties: A dictionary with keys such as "width", "height", "caption","basename", "suffix" (TODO: verify against schema)
        :return:                The auto-increment "item_ID" assigned to the newly-created data node
        """
        new_item_id = Collections.add_to_collection_at_beginning(collection_id=category_id, membership_rel_name="BA_in_category",
                                                                 item_class_name=item_class_name, item_properties=item_properties,
                                                                 new_item_id=new_item_id)
        return new_item_id



    @classmethod
    def add_content_at_end(cls, category_id:int, item_class_name: str, item_properties: dict, new_item_id=None) -> int:
        """
        Add a new Content Item, with the given properties and Class, to the end of the specified Category.

        :param category_id:     The integer "item_ID" of the Category to which this new Content Media is to be attached
        :param item_class_name: For example, "Images"
        :param item_properties: A dictionary with keys such as "width", "height", "caption","basename", "suffix" (TODO: verify against schema)
        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                The auto-increment "item_ID" assigned to the newly-created data node
        """
        new_item_id = Collections.add_to_collection_at_end(collection_id=category_id, membership_rel_name="BA_in_category",
                                                           item_class_name=item_class_name, item_properties=item_properties,
                                                           new_item_id=new_item_id)
        return new_item_id



    @classmethod
    def add_content_after_element(cls, category_id:int, item_class_name: str, item_properties: dict, insert_after: int, new_item_id=None) -> int:
        """
        Add a new Content Item, with the given properties and Class, inserted into the given Category after the specified Item
        (in the context of the positional order encoded in the relationship attribute "pos")

        :param category_id:     The integer "item_ID" of the Category to which this new Content Media is to be attached
        :param item_class_name: For example, "Images"
        :param item_properties: A dictionary with keys such as "width", "height", "caption","basename", "suffix" (TODO: verify against schema)
        :return:                The auto-increment "item_ID" assigned to the newly-created data node
        """
        new_item_id = Collections.add_to_collection_after_element(collection_id=category_id, membership_rel_name="BA_in_category",
                                                                  item_class_name=item_class_name, item_properties=item_properties,
                                                                  insert_after=insert_after,
                                                                  new_item_id=new_item_id)
        return new_item_id




    ######    POSITIONING WITHIN CATEGORIES    ######

    @classmethod
    def check_for_duplicates(cls, category_id) -> str:
        """
        Look for duplicates values in the "pos" attributes
        of the "BA_in_category" relationships ending in the specified Category node (specified by its item_id)

        :param category_id:
        :return:            In case of duplicates, return a text with an explanation;
                            if no duplicates, return an empty string
        """
        q = '''
            MATCH (i1:BA)-[r1:BA_in_category]->(:BA {schema_code:"cat", item_id: $item_id})<-[r2:BA_in_category]-(i2:BA) 
            WHERE r1.pos = r2.pos AND i1.item_id <> i2.item_id
            RETURN r1.pos AS pos, i1.item_id AS item1 ,i2.item_id AS item2
            LIMIT 1
            '''
        data_binding = {"item_id": category_id}
        duplicates = cls.db.query(q, data_binding)
        if duplicates == []:
            return ""
        else:
            first_record = duplicates[0]
            return f"Duplicate pos value ({first_record['pos']}, shared by relationships to items with IDs {first_record['item1']} and {first_record['item2']})"


    @classmethod
    def check_all_categories_for_duplicates(cls) -> str:
        """

        :return:            In case of duplicates, return a text with an explanation;
                            if no duplicates, return an empty string
        """
        all_category_ids = NeoSchema.data_points_of_class("Categories")

        duplicate_info = ""
        for category_id in all_category_ids:
            status = cls.check_for_duplicates(category_id)
            if status:
                duplicate_info += f"Duplicate found for Category {category_id}: {status}\n"

        return duplicate_info



    @classmethod
    def reposition_content(cls, category_id: int, item_id: int, move_after_n: int):
        """
        Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.

        Note: there's no harm (though it's wasteful) to move an item to a final sequence position where it already is;
              its "pos" value will change

        :param category_id:     An integer with the Category ID
        :param item_id:         An integer with the ID of the Content Item we're repositioning
        :param move_after_n:    The index (counting from 1) of the item after which we want to position the item being moved
                                    Use n=0 to indicate "move before anything else"
        :return:
        """
        assert type(category_id) == int, "ERROR: argument 'category_id' is not an integer"
        assert type(item_id) == int, "ERROR: argument 'item_id' is not an integer"
        assert type(move_after_n) == int, "ERROR: argument 'move_after_n' is not an integer"
        assert move_after_n >= 0, "ERROR: argument 'move_after_n' cannot be negative"

        # Collect a subset of the first sorted "pos" values: enough values to cover across the insertion point
        number_to_consider = move_after_n + 1
        q = f'''
            MATCH (c:BA {{schema_code: "cat", item_id: $category_id}}) <- [r:BA_in_category] - (:BA)
            WITH  r.pos AS pos
            ORDER by pos
            LIMIT {number_to_consider}
            WITH collect(pos) AS POS_LIST
            RETURN POS_LIST
            '''

        result = cls.db.query(q, {"category_id": category_id})  # If nothing found, this will be [{'POS_LIST': []}]
        pos_list = result[0].get("POS_LIST")    # A subset of the first sorted "pos" values
        print("pos_list: ", pos_list)

        if pos_list == []:
            # The Category is empty (or doesn't exist)
            raise Exception(f"Category (id {category_id}) not found, or empty")

        if move_after_n == 0:
            # Move to top
            print("Moving to the top")
            top_pos = pos_list[0]
            new_pos = top_pos - cls.DELTA_POS
        elif move_after_n >= len(pos_list):
            # Move to bottom
            print("Moving to the bottom")
            top_pos = pos_list[-1]      # The last element in the list
            new_pos = top_pos + cls.DELTA_POS
        else:
            pos_above = pos_list[move_after_n - 1]  # The "pos" value of the Item just above the insertion point
            pos_below = pos_list[move_after_n]      # The "pos" value of the Item just below
            print(f"pos_above: {pos_above} | pos_below: {pos_below}")
            if pos_below == pos_above + 1:
                # There's no room; shift everything that is past that position, by a count of DELTA_POS
                print(f"********* RELOCATING ITEMS (skipping the first {move_after_n}) ***********")
                cls.relocate_positions(category_id, n_to_skip=move_after_n, pos_shift=cls.DELTA_POS)
                new_pos = pos_above + int(cls.DELTA_POS/2)			# This will be now be the empty halfway point
            else:
                new_pos = int((pos_above + pos_below) / 2)		# Take the halfway point, rounded down


        # Change the "pos" attribute of the relationship to the Content Item being moved
        q = f'''
            MATCH (:BA {{schema_code: "cat", item_id: $category_id}}) <- [r:BA_in_category] - (:BA {{item_id: $item_id}})
            SET r.pos = {new_pos}
            '''

        print("q: ", q)

        result = cls.db.update_query(q, {"category_id": category_id, "item_id": item_id})
        number_props_set = result.get('properties_set')
        print("number_props_set: ", number_props_set)
        if number_props_set != 1:
            raise Exception(f"Content Item (id {item_id}) not found in Category (id {category_id}), or could not be moved")



    @classmethod
    def relocate_positions(cls, category_id: int, n_to_skip: int, pos_shift: int) -> int:
        """
        Shift the values of the "pos" attributes on the "BA_in_category" relationships
        from the given Category node, by the given amount;
        however, SKIP the first n_to_skip entries (as sorted by the "pos" attribute)

        EXAMPLE - given the following order of the relationships attached to the given Category:
            pos
        1:   45
        2:   84
        3:   91

        then relocate_positions(category_id, n_to_skip=1, pos_shift=100) will result in:
            pos
        1:   45     <- got skipped
        2:  184
        3:  191

        :param category_id: An integer with the Category ID
        :param n_to_skip:   The number of relationships (after sorting them by "pos") NOT to re-position
                                Must be an integer >= 1 (it'd be pointless to shift everything!)
        :param pos_shift:   The increment by which to shift the values of the "pos" attributes on the relationships

        :return:            The number of repositionings performed
        """
        assert type(category_id) == int, "ERROR: argument 'category_id' is not an integer"
        assert type(n_to_skip) == int, "ERROR: argument 'n_to_skip' is not an integer"
        assert type(pos_shift) == int, "ERROR: argument 'pos_shift' is not an integer"
        assert n_to_skip >= 1, "ERROR: argument 'n_to_skip' must be at least 1"

        q = f'''
            MATCH (c:BA {{schema_code: "cat", item_id: $category_id}}) <- [r:BA_in_category] - (:BA)
            WITH  r.pos AS pos, r
            ORDER by pos
            SKIP {n_to_skip}
            SET r.pos = r.pos + {pos_shift}
            '''

        result = cls.db.update_query(q, {"category_id": category_id})
        return result.get('properties_set')



    @classmethod
    def swap_content_items(cls, item_id_1: str, item_id_2: str, cat_id: str) -> str:
        """
        Swap the positions of the specified Content Items within the given Category

        :param item_id_1:   A string with the (integer) ID of the 1st Content Item
        :param item_id_2:   A string with the (integer) ID of the 2nd Content Item
        :param cat_id:      A string with the (integer) ID of the Category
        :return:            An empty string if successful, or an error message otherwise
        """

        # Validate the arguments
        if item_id_1 == item_id_2:
            return f"Attempt to swap a Content Item (ID {item_id_1}) with itself!"

        try:
            item_id_1 = int(item_id_1)
        except Exception:
            return f"The first Content Item ID ({item_id_1}) is missing or not an integer"

        try:
            item_id_2 = int(item_id_2)
        except Exception:
            return f"The second Content Item ID ({item_id_2}) is missing or not an integer"

        try:
            cat_id = int(cat_id)
        except Exception:
            return f"The Category ID ({cat_id}) is missing or not an integer"


        # Look for a Category node (c) that is connected to 2 Content Items (n1 and n2)
        #   thru "BA_in_category" relationships; then swap the "pos" attributes on those relationships
        q = '''
            MATCH (n1:BA {item_id: $item_id_1})
                        -[r1:BA_in_category]->(c:BA {schema_code:"cat", item_id: $cat_id})<-[r2:BA_in_category]-
                  (n2:BA {item_id: $item_id_2})
            WITH r1.pos AS tmp, r1, r2
            SET r1.pos = r2.pos, r2.pos = tmp
            '''

        data_binding = {"item_id_1": item_id_1, "item_id_2": item_id_2, "cat_id": cat_id}

        #print(q)
        #print(data_binding)

        stats = cls.db.update_query(q, data_binding)
        #print("stats of query: ", stats)

        if stats == {}:
            return f"The action had no effect : the specified Content Items ({item_id_1} and {item_id_2})" \
                   f" were not found attached to the given Category ({cat_id})"

        number_properties_set = stats.get("properties_set")

        if number_properties_set != 2:
            return f"Irregularity detected in swap action: {number_properties_set} properties were set," \
                   f" instead of the expected 2"

        return ""   # Normal termination, with no error message




##########################################################################################

#                                COLLECTIONS                                             #

##########################################################################################

class Collections:
    """
    A generalization of Categories.

    TODO: maybe turn into an instantiatable class, so as not to have to repeatedly pass "membership_rel_name"
    """

    # Class variables

    db = None   # MUST be set before using this class!
    #db = neo_access.NeoAccess()    # Saving database-interface object as a CLASS variable.
                                        # This will only be executed once

    DELTA_POS = 20                      # Arbitrary shift in "pos" value; best to be even, and not too small nor too large

    membership_rel_name = None          # NOT IN USE.   TODO: maybe use instantiation, and set at that time


    @classmethod
    def is_collection(cls, collection_id: int) -> bool:
        """
        Return True if the data node whose "item_id" has the given value is a Collection,
        that is, if its schema is a Class that is an INSTANCE_OF the "Collection" Class
        TODO: maybe allow the scenario where there's a longer chain of "INSTANCE_OF" relationships

        :param collection_id:   The item_id of a data node
        :return:                True if the given data node is a Collection, or False i
        """
        q = '''
        MATCH p=(n :BA {item_id: $collection_id}) -[:SCHEMA]-> (s :CLASS) -[:INSTANCE_OF]-> (coll :CLASS {name: "Collections"})
        RETURN count(p) AS number_paths
        '''
        data_binding = {"collection_id": collection_id}
        number_paths = cls.db.query(q, data_binding, single_cell="number_paths")

        return True if number_paths > 0 else False



    @classmethod
    def collection_size(cls, collection_id: int, membership_rel_name: str, skip_check=False) -> int:
        """
        Return the number of elements in the given Collection (i.e. Data Items linked to it thru the specified relationship)

        :param collection_id:       The item_id of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship from other Data Items to the given Collection node
        :param skip_check:          If True, no check is done to verify that the data node whose item_id matches collection_id
                                    is indeed a Collection.
                                    Without a check, this function will return a zero if given a bad collection_id;
                                    with a check, it'll raise an Exception
        :return:                    The number of elements in the given Collection (possibly zero)
        """
        if not skip_check:
            assert cls.is_collection(collection_id), f"The data node with item_id {collection_id} doesn't exist or is not a Collection"

        q = f'''
        MATCH (coll :BA {{item_id: $collection_id}}) <- [:{membership_rel_name}] - (i :BA) 
        RETURN count(i) AS node_count
        '''
        data_binding = {"collection_id": collection_id}

        number_items_attached = cls.db.query(q, data_binding, single_cell="node_count")
        return number_items_attached



    @classmethod
    def delete_collection(cls, collection_id: int) -> None:
        """
        Delete the specified Collection, provided that there are no Data Items linked to it.
        In case of error or failure, an Exception is raised.

        :param collection_id:   The "item_id" integer value identifying the desired Collection
        :return:                None
        """
        pass



    @classmethod
    def add_to_collection_at_beginning(cls, collection_id: int, membership_rel_name: str, item_class_name: str, item_properties: dict,
                                       new_item_id=None) -> int:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add it at the beginning of the specified Collection, linked by the specified relationship

        EXAMPLE:  new_item_id = add_to_collection_at_beginning(collection_id=708, membership_rel_name="BA_in_category",
                                                        item_class_name="Headers", item_properties={"text": "New Caption, at the end"})
        <SEE add_to_collection_at_end>

        :return:                    The auto-increment "item_ID" assigned to the newly-created data node
        """
        assert type(collection_id) == int, "The argument `collection_id` MUST be an integer"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"

        # TODO: this query and the one in add_data_point(), below, ought to be combined, to avoid concurrency problems
        q = f'''
            MATCH (n:BA) - [r :{membership_rel_name}] -> (c:BA {{item_id: $collection_id}}) 
            RETURN min(r.pos) AS min_pos
            '''
        data_binding = {"collection_id": collection_id}

        min_pos = cls.db.query(q, data_binding, single_cell="min_pos")  # This will be None if the Collection has no elements

        if min_pos is None:
            pos = 0                         # Arbitrary initial value for cases when the Collection has no elements
        else:
            pos = min_pos - cls.DELTA_POS   # Go some distance before the beginning

        data_binding = item_properties

        return NeoSchema.add_data_point(class_name=item_class_name,
                                        data_dict=data_binding,
                                        labels="BA",
                                        connected_to_id=collection_id, connected_to_labels="BA",
                                        rel_name=membership_rel_name,
                                        rel_prop_key="pos", rel_prop_value=pos,
                                        new_item_id=new_item_id
                                        )



    @classmethod
    def add_to_collection_at_end(cls, collection_id: int, membership_rel_name: str, item_class_name: str, item_properties: dict,
                                 new_item_id=None) -> int:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add it at the end of the specified Collection, linked by the specified relationship

        EXAMPLE:  new_item_id = add_to_collection_at_end(collection_id=708, membership_rel_name="BA_in_category",
                                                        item_class_name="Headers", item_properties={"text": "New Caption, at the end"})

        :param collection_id:       The item_id of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name:
        :param item_class_name:
        :param item_properties:
        :param new_item_id:         Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                    The auto-increment "item_ID" assigned to the newly-created data node
        """
        assert type(collection_id) == int, "The argument `collection_id` MUST be an integer"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"

        # TODO: this query and the one in add_data_point(), below, ought to be combined, to avoid concurrency problems
        q = f'''
            MATCH (n:BA) - [r :{membership_rel_name}] -> (c:BA {{item_id: $collection_id}}) 
            RETURN max(r.pos) AS max_pos
            '''
        data_binding = {"collection_id": collection_id}

        max_pos = cls.db.query(q, data_binding, single_cell="max_pos")  # This will be None if the Collection has no elements

        if max_pos is None:
            pos = 0                         # Arbitrary initial value for cases when the Collection has no elements
        else:
            pos = max_pos + cls.DELTA_POS   # Go some distance past the end

        data_binding = item_properties

        #cls.db.debug_print(q, data_binding, "add_to_collection_at_end", True)

        return NeoSchema.add_data_point(class_name=item_class_name,
                                        data_dict=data_binding,
                                        labels="BA",
                                        connected_to_id=collection_id, connected_to_labels="BA",
                                        rel_name=membership_rel_name,
                                        rel_prop_key="pos", rel_prop_value=pos,
                                        new_item_id=new_item_id
                                        )



    @classmethod
    def add_to_collection_after_element(cls, collection_id: int, membership_rel_name: str,
                                        item_class_name: str, item_properties: dict, insert_after: int,
                                        new_item_id=None) -> int:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add to the specified Collection, linked by the specified relationship and inserted after the given collection Item
        (in the context of the positional order encoded in the relationship attribute "pos")

        :param collection_id:       The item_id of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship to which the positions ("pos" attribute) apply
        :param item_class_name:     Name of the Class for the newly-created node
        :param item_properties:     Dictionary with the properties of the newly-created node
        :param insert_after:        The "item_id" of the element after which we want to insert
        :param new_item_id:         Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                    The auto-increment "item_ID" assigned to the newly-created data node
        """
        assert type(collection_id) == int, "The argument `collection_id` MUST be an integer"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"
        assert type(insert_after) == int, "The argument `insert_after` MUST be an integer"
        if new_item_id:
            assert type(new_item_id) == int, f"The argument `new_item_id`, when provided, MUST be an integer (it was `{new_item_id}`)"

        q = f'''
        MATCH (n_before :BA {{item_id: $insert_after}})-[r_before :{membership_rel_name}] 
                    -> (c :BA {{item_id: $collection_id}}) <-
                                            [r_after :{membership_rel_name}]-(n_after :BA)
        WHERE r_after.pos > r_before.pos
        RETURN r_before.pos AS pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''
        #EXAMPLE:
        '''
        MATCH (n_before :BA {item_id: 717})-[r_before :BA_in_category] -> (c :BA {item_id: 708}) <-[r_after :BA_in_category]-(n_after :BA)
        WHERE r_after.pos > r_before.pos
        RETURN r_before.pos AS pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''

        data_binding = {"collection_id": collection_id, "insert_after": insert_after}

        # ALTERNATE WAY OF PHRASING THE QUERY:
        '''
        MATCH (n_before:BA {item_id: 717})-[r_before :BA_in_category] -> (c:BA {item_id: 708}) <- [r_after :BA_in_category]-(n_after :BA)
        WITH r_before.pos AS pos_before, r_after
        WHERE r_after.pos > pos_before
        RETURN pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''

        result = cls.db.query(q, data_binding, single_row=True)
        print(result)
        if result == {}:
            # An empty find is indicative of either an "insert at the end" (no n_after found),
            #       or a bad insert_after value that matches no node
            node = NeoSchema.fetch_data_point(item_id = insert_after)
            if node == {}:
                raise Exception(f"There is no node with the `item_id` value ({insert_after}) passed by `insert_after`")

            print("It's case of insert AT THE END")
            return cls.add_to_collection_at_end(collection_id, membership_rel_name, item_class_name, item_properties,new_item_id=new_item_id)


        pos_before = result["pos_before"]
        pos_after = result["pos_after"]

        if pos_after == pos_before + 1:
            # There's no room; shift everything that is past that position, by a count of DELTA_POS
            print(f"********* SHIFTING DOWN ITEMS whose `pos` value is {pos_after} and above  ***********")
            cls.shift_down(collection_id=collection_id, membership_rel_name=membership_rel_name, first_to_move=pos_after)
            new_pos = pos_before + int(cls.DELTA_POS/2)			# This will be now be the empty halfway point
        else:
            new_pos = int((pos_before + pos_after) / 2)		# Take the halfway point, rounded down

        link_to = [{"labels": "BA", "key": "item_id", "value": collection_id,
                    "rel_name": membership_rel_name, "rel_attrs": {"pos": new_pos}}]

        new_neo_id = cls.db.create_node_with_relationships(labels="BA", properties=item_properties, connections=link_to)

        item_id = NeoSchema.register_existing_data_point(class_name=item_class_name, existing_neo_id=new_neo_id, new_item_id=new_item_id)

        return item_id



    @classmethod
    def shift_down(cls, collection_id: int, membership_rel_name: str, first_to_move) -> int:
        """
        Shift down the positions (values of the "pos" relationship attributes) by an arbitrary fixed amount,
        starting with nodes with the specified position value (and all greater values);
        this operation applies to nodes linked to the specified Collection thru a relationship with the given name.

        :param collection_id:       The item_id of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship to which the positions ("pos" attribute) apply
        :param first_to_move:       All position ("pos") values greater or equal to this one will get shifted down
        :return:                    The number of modified items
        """
        # Starting with a particular Collection node, look at all its relationships whose name is specified by membership_rel_name,
        #       and increase the value of the "pos" attributes on those relationships if their current values is at least first_to_move
        q = f'''
        MATCH (c:BA {{item_id: $collection_id}}) <- [r :{membership_rel_name}] - (n :BA)
        WHERE r.pos >= $first_to_move
        SET r.pos = r.pos + {cls.DELTA_POS}
        '''
        data_binding = {"collection_id": collection_id, "first_to_move": first_to_move}

        status = cls.db.update_query(q, data_binding)
        return status.get("properties_set", 0)
