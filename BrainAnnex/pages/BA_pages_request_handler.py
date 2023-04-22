from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


"""
    MIT License.  Copyright (c) 2021-2022 Julian A. West
"""



class PagesRequestHandler:
    """
    Used by the UI for Page Generation.

    This class does NOT get instantiated.

    Note: "Request Handlers" are the ONLY CLASSES THAT DIRECTLY COMMUNICATES WITH THE DATABASE INTERFACE
    """
    # The "db" property gets set by InitializeBrainAnnex.set_dbase()

    db = None       # Object of class "NeoAccess".  MUST be set before using this class!




    @classmethod
    def get_node_labels(cls) -> [str]:
        """
        Look up and return a list of all the node labels in the database.
        EXAMPLE: ["my_label_1", "my_label_2"]

        :return:    A list of strings
        """

        label_list = cls.db.get_labels()        # Fetch all the node labels in the database

        return label_list



    @classmethod
    def all_schema_classes(cls) -> [str]:
        """
        Return a list of all the existing Schema classes
        :return:
        """
        return NeoSchema.get_all_classes()




    #############################   CATEGORY-RELATED (TODO: being moved to categories.py)  #############################

    @classmethod
    def get_content_items_by_category(cls, category_id = 1) -> [{}]:        # TODO: move to Categories
        """
        Return the records for all nodes linked to the Category node identified by its item_id value

        :param category_id:
        :return:    A list of dictionaries
                    EXAMPLE:
                    [{'schema_code': 'i', 'item_id': 1,'width': 450, 'basename': 'my_pic', 'suffix': 'PNG', pos: 0, 'class_name': 'Images'},
                     {'schema_code': 'h', 'item_id': 1, 'text': 'Overview', pos: 10, 'class_name': 'Headers'},
                     {'schema_code': 'n', 'item_id': 1', basename': 'overview', 'suffix': 'htm', pos: 20, 'class_name': 'Notes'}
                    ]
        """

        # Locate all the Content Items linked to the given Category, and also extract the name of the schema Class they belong to
        # TODO: switch to using one of the Collections methods
        cypher = """
            MATCH (cl :CLASS)<-[:SCHEMA]-(n :BA)-[r :BA_in_category]->(category :BA {schema_code:"cat", item_id:$category_id})
            RETURN n, r.pos AS pos, cl.name AS class_name
            ORDER BY r.pos
            """

        result = cls.db.query(cypher, {"category_id": category_id})
        #print(result)


        content_item_list = []
        for elem in result:
            item_record = elem["n"]             # A dictionary with the various fields

            # TODO: eliminate possible conflict if the node happens to have
            #       attributes named "pos" or "class_name"!
            item_record["pos"] = elem["pos"]                # Inject into the record a positional value
            item_record["class_name"] = elem["class_name"]  # Inject into the record the name of its Class
            content_item_list.append(item_record)

        #print(content_item_list)
        return content_item_list



    @classmethod
    def get_subcategories(cls, category_id) -> [dict]:
        """
        Return all the (immediate) subcategories of the given category,
        as a list of dictionaries with keys 'id' and 'name' TODO: fix
        EXAMPLE:
            OLD -> [{'id': 2, 'name': 'Work'}, {'id': 3, 'name': 'Hobbies'}]
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :param category_id:
        :return:    A list of dictionaries
        """
        q =  '''
             MATCH (sub:BA {schema_code:"cat"})-[BA_subcategory_of]->(c:BA {schema_code:"cat", item_id:$category_id})
             RETURN sub.item_id AS id, sub.name AS name
             '''
        result = cls.db.query(q, {"category_id": category_id})

        '''
        new = cls.db.follow_links(labels="BA", key_name="item_id", key_value=category_id,
                                  rel_name="BA_subcategory_of", rel_dir="IN",
                                  neighbor_labels="BA")
        # OR: properties_condition = {"item_id": category_id, "schema_code": "cat"}
        '''

        return result



    @classmethod
    def get_parent_categories(cls, category_id) -> [dict]:
        """
        Return all the (immediate) parent categories of the given category,
        as a list of dictionaries with all the keys of the Category Class

        TODO: fix inconsistency.  This function uses item_id ; others use just id

        EXAMPLE:
            [{'item_id': 2, 'name': 'Work', remarks: 'outside employment'}, {'item_id': 3, 'name': 'Hobbies'}]

        :param category_id:
        :return:    A list of dictionaries
        """
        match = cls.db.match(labels="BA",
                            properties={"item_id": category_id, "schema_code": "cat"})

        result = cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="OUT",
                                         neighbor_labels="BA")

        return result



    @classmethod
    def get_all_categories(cls, exclude_root=True) -> [dict]:
        """
        TODO: phase out, in favor of Categories.get_all_categories (which uses 'item_id' instead of 'id')

        Return all the existing Categories - possibly except the root -
        as a list of dictionaries with keys 'id', 'name', 'remarks'
        sorted by name
        EXAMPLE:
            [{'id': 3, 'name': 'Hobbies'}, {'id': 2, 'name': 'Work', 'remarks': 'paid jobs'}]

        Note that missing "remarks" values are not in the dictionaries

        :param exclude_root:
        :return:                A list of dictionaries
        """
        clause = ""
        if exclude_root:
            clause = "WHERE cat.item_id <> 1"

        q =  f'''
             MATCH (cat:BA {{schema_code:"cat"}})
             {clause}
             RETURN cat.item_id AS id, cat.name AS name, cat.remarks AS remarks
             ORDER BY toLower(cat.name)
             '''
        # Notes: 1 is the ROOT
        # Sorting must be done across consistent capitalization, or "GSK" will appear before "German"!

        result = cls.db.query(q)

        # Ditch all the missing "remarks" values
        for cat in result:
            if cat["remarks"] is None:
                del cat["remarks"]

        return result
