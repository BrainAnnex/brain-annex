from typing import Union, List
from brainannex import NeoAccess, NeoSchema, Collections
import pandas as pd



class Categories:
    """
    Library for Category-related operations.

    An entity to which a variety of nodes (e.g. representing records or media)
    is attached, with a positional attribute.

    Categories also have "subcategory" and "see_also" relationships with other categories.
    """

    db = None   # MUST be set before using this class!
                # Database-interface object is a CLASS variable, accessible as cls.db

    DELTA_POS = 20      # Arbitrary shift in "pos" value; best to be even, and not too small nor too large



    @classmethod
    def set_database(cls, db :NeoAccess) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, created with the NeoAccess library
        :return:    None
        """

        assert type(db) == NeoAccess, \
            "Categories.set_database(): argument passed isn't a valid NeoAccess object"

        cls.db = db     # Save the database object

        # Initialize dependencies
        NeoSchema.set_database(db)
        Collections.set_database(db)



    @classmethod
    def initialize_categories(cls) -> (int, str):
        """
        Create a new Schema Class node that represents "Categories",
        and make it an "INSTANCE_OF" of the "Collections" Class

        :return:    An (int, str) pair of integers with the internal database ID
                        and the unique uri assigned to the new Class node
        """
        (int_dbase_id, uri) = NeoSchema.create_class_with_properties(name="Category",
                                                        properties=["name", "remarks", "uri", "root"],
                                                        strict=True)

        NeoSchema.create_class_relationship(from_class="Category", to_class="Category",
                                            rel_name="BA_subcategory_of", use_link_node=False)

        NeoSchema.create_class_relationship(from_class="Category", to_class="Category",
                                            rel_name="BA_see_also", use_link_node=False)

        if not NeoSchema.class_name_exists("Collections"):
            Collections.initialize_collections()
            NeoSchema.create_class_relationship(from_class="Category", to_class="Collections",
                                                rel_name="INSTANCE_OF", use_link_node=False)

        return (int_dbase_id, uri)





    #####################################################################################################

    '''                                 ~   LOOKUP CATEGORY DATA   ~                                  '''

    def ________LOOKUP_CATEGORIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_category_info(cls, category_uri :str) -> dict:
        """
        Return the Name and Remarks field values attached to the given Category

        :param category_uri:    A string identifying the desired Category
        :return:                The Category's name (or a blank dictionary if not found)
                                    EXAMPLE:  {"uri": "123", "name": "Astronomy", "remarks": "except cosmology"}
        """
        # Note: since the category_uri is a primary key,
        #       specifying a value for the labels and the "schema_code" property is for redundancy
        return NeoSchema.get_data_node(class_name="Category", node_id=category_uri, id_key="uri")



    @classmethod
    def is_root_category(cls, category_uri :str) -> bool:
        """
        Return True if the given ID corresponds to the ROOT Category, or False otherwise

        :param category_uri:    A string identifying the desired Category
        :return:                True if the given ID corresponds to the ROOT Category, or False otherwise
        """
        assert NeoSchema.is_valid_uri(category_uri), \
            "is_root_category(): the argument `category_uri` is not a valid URI string"

        # NOTE: historically, "1" has been used for the ROOT Category; however, now that uri is shared
        #       among all types of plugins, maybe a different approach would be better (such as an attribute in the node)
        return True if category_uri == "1" else False    # TODO: this will eventually have to be managed differently



    @classmethod
    def get_all_categories(cls, exclude_root=True, include_remarks=False) -> [dict]:
        """
        Return all the existing Categories - optionally except the root Category -
        as a list of dictionaries with keys 'uri', 'name', 'pinned' and, optionally, 'remarks',
        sorted by name.

        :param exclude_root:    If True, the root Category is omitted
        :param include_remarks: If True, the 'remarks' property is included alongside all others

        :return:    A list of dictionaries.  EXAMPLE:
                        [{'uri': '2', 'name': 'Work', 'remarks': 'Current or past'},
                         {'uri': '3', 'name': 'Hobbies', pinned: True} ]
        """
        clause = ""
        if exclude_root:
            clause = "WHERE (cat.root <> true OR cat.root is NULL)"


        remarks_subquery = ", cat.remarks AS remarks"  if include_remarks else ""

        # TODO: switch to using the Schema library datanode operations
        q =  f'''
             MATCH (cat :Category {{`_SCHEMA`: "Category"}})
             {clause}
             RETURN cat.uri AS uri, cat.name AS name, cat.pinned AS pinned {remarks_subquery}
             ORDER BY toLower(cat.name)
             '''

        # Notes: Sorting must be done across names of consistent capitalization, or "GSK" will appear before "German"!

        result =  cls.db.query(q)

        # Ditch all the MISSING "pinned" values  (TODO: let the Schema layer handle this!)
        for item in result:
            if item["pinned"] is None:
                del item["pinned"]     # To avoid a dictionary entry of the type  'pinned': None

        # If remarks are being included, ditch all the MISSING "remarks" values
        if include_remarks:
            for item in result:
                if item["remarks"] is None:
                    del item["remarks"]     # To avoid a dictionary entry of the type  'remarks': None

        return result



    @classmethod
    def count_subcategories(cls, category_uri :str) -> int:
        """
        Return the number of (direct) Subcategories of the given Category
        TODO: maybe turn into a method of NeoSchema :  count_inbound_rels(labels="BA, uri=category_uri, class_name="Category")

        :param category_uri:A string identifying the desired Category
        :return:            The number of (direct) Subcategories of the given Category; possibly, zero
        """

        match = cls.db.match(labels="Category",
                             properties={"uri": category_uri})

        return cls.db.count_links(match, rel_name="BA_subcategory_of", rel_dir="IN")


    @classmethod
    def count_parent_categories(cls, category_uri :str) -> int:
        """
        Return the number of (direct) Subcategories of the given Category
        TODO: maybe turn into a method of NeoSchema :  count_outbound_rels(labels="BA, uri=category_uri, class_name="Category")

        :param category_uri:A string identifying the desired Category
        :return:            The number of (direct) parent categories of the given Category; possibly, zero
        """

        match = cls.db.match(labels="Category",
                             properties={"uri": category_uri})

        return cls.db.count_links(match, rel_name="BA_subcategory_of", rel_dir="OUT")



    @classmethod
    def get_subcategories(cls, category_uri :str) -> [dict]:
        """
        Return all the (immediate) subcategories of the given category,
        as a list of dictionaries with all the keys of the Category Class
        EXAMPLE:
            [{'uri': '2', 'name': 'Work', remarks: 'outside employment'},
             {'uri': '3', 'name': 'Hobbies'}]

        :param category_uri:A string identifying the desired Category
        :return:            A list of dictionaries
        """
        match = cls.db.match(labels="Category", key_name="uri", key_value=category_uri)

        return cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="IN",
                                   neighbor_labels="Category")



    @classmethod
    def get_parent_categories(cls, category_uri :str) -> [dict]:
        """
        Return all the (immediate) parent categories of the given Category,
        as a list of dictionaries with all the keys of the Category Class
        EXAMPLE:
            [{'uri': '2', 'name': 'Work', remarks: 'outside employment'},
             {'uri': '3', 'name': 'Hobbies'}]

        :param category_uri:A string identifying the desired Category
        :return:            A list of dictionaries
        """
        match = cls.db.match(labels="Category",
                             properties={"uri": category_uri})

        result = cls.db.follow_links(match, rel_name="BA_subcategory_of", rel_dir="OUT",
                                   neighbor_labels="Category")

        # Ditch unneeded attributes
        NeoSchema.remove_schema_info(result)    # Zap any low-level Schema-related data

        return result



    @classmethod
    def get_sibling_categories(cls, category_internal_id: int) -> [dict]:
        """
        Return the data of all the "siblings" nodes of the given Category

        :param category_internal_id:    The internal database ID of a "Category" data node
        :return:                        A list of dictionaries, with one element for each "sibling";
                                            each element contains the 'internal_id' and 'neo4j_labels' keys,
                                            plus whatever attributes are stored on that node.
                                            EXAMPLE of single element:
                                            {'name': 'French', 'internal_id': 123, 'neo4j_labels': ['Category', 'BA']}
        """

        #TODO: switch to this after the next update of NeoAccess
        #result = cls.db.get_siblings(internal_id=category_internal_id, rel_name="BA_subcategory_of", order_by="name")

        q = f"""
                MATCH (n) - [:BA_subcategory_of] -> (parent) <- [:BA_subcategory_of] - (sibling)
                WHERE id(n) = {category_internal_id}
                RETURN DISTINCT sibling
                ORDER BY toLower(sibling.name)
            """
        result = cls.db.query_extended(q, flatten=True)

        # Ditch unneeded attributes
        NeoSchema.remove_schema_info(result)    # Zap any low-level Schema-related data

        return result



    @classmethod
    def create_parent_map(cls, category_uri :str) -> dict:
        """
        Consider the set comprising the given Category and all its ancestors (i.e. all its super-categories),
        up to a maximum hop length.

        Create and return a dictionary that maps each of the uri in that set of Categories,
        to a list of the uri's of its parent Categories.

        :param category_uri:A string identifying the desired Category
        :return:            A dictionary mapping integers into lists of integers.
                            The keys are uri's of the given Category and any of its ancestors (super-categories),
                            up to a maximum hop length;
                            the values are lists of the uri's of the parent categories of the Category specified by the key
                            EXAMPLES:       {'123': ['1']}                                  # The given category (123) is a child of the root (1)
                                            {'823': ['709'], '709': ['544'], '544': ['1']}  # A simple 3-hop path from Category 823 to the root (1) :
                                                                                            #       823 is subcategory of 709,
                                                                                            #       which is subcategory of 544, which is subcategory of the root
                                            {'814': ['20', '30'], '20': ['1'], '30': ['79'], '79': ['1']}
                                                                                            # Two paths from Category 814 to the root;
                                                                                            #       814 is subcategory of 20 and 30;
                                                                                            #       20 is an subcategory of the root,
                                                                                            #       while with 30 we have to go thru an extra hop
        """

        # Based on the "BA_subcategory_of" relationship,
        #       extract a set of maps of the form child (c) -> all its parent categories,
        #       where the child c is any ancestor node of the given Category node.
        #       A limit is imposed on the max length of the path
        q = '''
            MATCH (start :BA:Category {uri:$category_uri})-[:BA_subcategory_of*0..9]->
                  (c :Category)-[:BA_subcategory_of]->(p :Category)
            WITH c, collect(DISTINCT p.uri) AS all_parents
            RETURN c.uri AS uri, all_parents
            '''
        result = cls.db.query(q, {"category_uri": category_uri})      # A list of dictionaries
        # EXAMPLE:  [{'uri': 823, 'all_parents': [709]},
        #            {'uri': 709, 'all_parents': [544]},
        #            {'uri': 544, 'all_parents': [1]}]

        parent_map = {}
        for entry in result:
            key = entry["uri"]
            value = entry["all_parents"]
            parent_map[key] = value

        # EXAMPLE of parent_map:   {823: [709], 709: [544], 544: [1]}
        return parent_map



    @classmethod
    def create_bread_crumbs(cls, category_uri :str) -> list:
        """
        Return a list of Category ID's together with token strings, providing directives for the HTML structure of
        the bread crumbs

        :param category_uri:A string with the URI of the Category whose "ancestry bread crumbs" we want to construct
        :return:            A list of Category URI's together with token strings,
                            providing directives for the HTML structure of the bread crumbs
                            EXAMPLE 1:  ['1']
                            EXAMPLE 2:  ['START_CONTAINER', ['1', 'ARROW', '799', 'ARROW', '876'], 'END_CONTAINER']
                            EXAMPLE 3:
                                [
                                    'START_CONTAINER',
                                    ['START_BLOCK',
                                                    'START_LINE', ['1', 'ARROW', '799', 'ARROW', '526'], 'END_LINE', 'CLEAR_RIGHT',
                                                    'START_LINE', ['1', 'ARROW', '61'], 'END_LINE',
                                     'END_BLOCK', 'ARROW', '814'],
                                    'END_CONTAINER'
                                ]
        """
        if category_uri == "1":    # If it is the root
            return ["1"]

        # If we get here, we're NOT at the root.

        parents_map = cls.create_parent_map(category_uri)
        #print("In create_bread_crumbs().  parents_map: ", parents_map)

        # Put together a block (to be turned into an HTML element by the front end) depicting all possible
        # breadcrumb paths from the ROOT to the current category
        return ["START_CONTAINER", cls.recursive(category_uri, parents_map) , "END_CONTAINER"]



    @classmethod
    def recursive(cls, category_uri :str, parents_map :dict) -> list:
        """

        :param category_uri:A string identifying the desired Category
        :param parents_map: The dict structure returned by create_parent_map()
        :return:
        """
        if cls.is_root_category(category_uri):
            return ["1"]    # TODO: this will eventually have to be managed differently

        parent_list = parents_map.get(category_uri, [])

        if len(parent_list) == 0:
            return []    # TODO: generate warning
        elif len(parent_list) == 1:     # If just one parent
            parent_id = parent_list[0]
            bc = cls.recursive(parent_id, parents_map)
            bc.append("ARROW")
            bc.append(category_uri)
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
            bc.append(category_uri)
            return bc





    #####################################################################################################

    '''                                 ~   MODIFY CATEGORY DATA   ~                                  '''

    def ________MODIFY_CATEGORIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def create_categories_root(cls, data_dict=None) -> (int, str):
        """
        Create a ROOT Category node;
        and return its internal database ID and its URI

        :param data_dict:   (OPTIONAL) Dict to specify alternate desired values
                                for the "name" and "remarks" fields of the Root Category
                                (by default, "HOME" and "top level", respectively)
        :return:            The pair (internal database ID, string URI)
                                of the new Data Node just created
        """
        if data_dict is None:
            data_dict = {"name": "HOME", "remarks": "top level"}

        data_dict["root"] = True        # Flag to mark this node as the root of the Category graph

        #new_uri = NeoSchema.reserve_next_uri(namespace="Category", prefix="cat-")
        new_uri = "cat-root"    # use a special URI

        internal_id = NeoSchema.create_data_node(class_name="Category",
                                                 properties = data_dict,
                                                 new_uri=new_uri)
        return (internal_id, new_uri)



    @classmethod
    def add_subcategory(cls, data_dict :dict, category_uri=None) -> str:
        """
        Add a new Subcategory to a given, already existing, Category

        :param data_dict:   Dictionary with the following keys:
                                category_uri            URI to identify the Category
                                                            to which to add the new Subcategory
                                subcategory_name        The name to give to the new Subcategory
                                subcategory_remarks     (OPTIONAL)  A comment field for the new Subcategory

        :param category_uri: Optional way to specify the parent Category

        :return:            A string with the "uri" of the Category node just created
                                (which makes use of an auto-increment value)
        """
        # TODO: complete switch to named arguments rather than the archaic data_dict

        # TODO: block the addition of multiple subcategories with the same name (i.e., prevent
        #       a Category to have multiple "children" with the same name)
        if category_uri is None:
            category_uri = data_dict.get("category_uri")
            assert category_uri is not None, \
                        "add_subcategory(): key `category_uri` in argument `data_dict` is missing"

        assert NeoSchema.is_valid_uri(category_uri), \
                    f"add_subcategory(): invalid category uri ({category_uri})"

        subcategory_name = data_dict.get("subcategory_name")

        #TODO: eliminate leading/trailing blanks

        if not subcategory_name:
            raise Exception(f"add_subcategory(): subcategory_name is missing")

        subcategory_remarks = data_dict.get("subcategory_remarks")  # This field is optional

        data_dict = {"name": subcategory_name}
        if subcategory_remarks:
            data_dict["remarks"] = subcategory_remarks

        parent_category_internal_id = NeoSchema.get_data_node_id(key_value=category_uri, key_name="uri")

        '''
        new_internal_id = NeoSchema.add_data_node_with_links(
                                class_name = "Category",
                                properties = data_dict, labels = ["BA", "Category"],
                                links = [{"internal_id": parent_category_internal_id, "rel_name": "BA_subcategory_of"}],
                                assign_uri=True)
        '''
        new_uri = NeoSchema.reserve_next_uri()      # Obtain (and reserve) the next auto-increment value
        NeoSchema.create_data_node(class_name="Category", extra_labels ="BA",
                                   properties = data_dict,
                                   links = [{"internal_id": parent_category_internal_id,
                                             "rel_name": "BA_subcategory_of"}],
                                   new_uri=new_uri)

        '''
        new_data_point = NeoSchema.search_data_node(internal_id = new_internal_id)
        assert new_data_point is not None, \
            "add_subcategory(): failure to fetch data node for the newly created subcategory"

        return new_data_point["uri"]
        '''
        return new_uri



    @classmethod
    def delete_category(cls, uri :str) -> None:
        """
        Delete the specified Category, provided that there are no Content Items linked to it.
        In case of error or failure, an Exception is raised.

        :param uri: The uri identifying the desired Category
        :return:    None
        """
        category_uri = uri

        if cls.is_root_category(category_uri):
            raise Exception("Cannot delete the Root node")       # TODO: this will eventually have to be managed differently

        # First, make sure that there are no Content Items linked to this Category
        number_items_attached = Collections.collection_size(collection_id=category_uri, membership_rel_name="BA_in_category")

        if number_items_attached > 0:
            raise Exception(f"Cannot delete the requested Category (URI '{category_uri}') because "
                            f"it has Content Items attached to it: {number_items_attached} item(s). "
                            f"You need to first untag or delete all Items associated to it")

        if cls.count_subcategories(category_uri) > 0:
            raise Exception(f"Cannot delete the requested Category (URI '{category_uri}') because it has sub-categories. Use the Category manager to first sever those relationships")

        #number_deleted = NeoSchema.delete_data_point(uri=category_uri, labels="BA")
        number_deleted = NeoSchema.delete_data_nodes(node_id=category_uri, id_key="uri", class_name="Category")

        if number_deleted != 1:
            raise Exception(f"Failed to delete the requested Category (URI '{category_uri}')")



    @classmethod
    def add_subcategory_relationship(cls, data_dict :dict) -> None:
        """
        Add a sub-category ("BA_subcategory_of") relationship
        between the specified 2 existing Categories.
        If the requested new relationship cannot be created (for example, if it already exists),
        raise an Exception

        :param data_dict:   Two keys are expected:
                                "sub"         URI to identify an existing Category node
                                                that is to be made a sub-category of another one
                                "cat"         URI to identify an existing Category node
                                                that is to be made the parent of the other Category

        :return:            None.  If the requested new relationship could not be created,
                                raise an Exception
        """

        subcategory_uri = data_dict["sub"]
        category_uri = data_dict["cat"]


        # Notice that, because the relationship is called a SUB-category, the subcategory is the "parent"
        #   (the originator) of the relationship
        try:
            NeoSchema.add_data_relationship(from_id=subcategory_uri, to_id=category_uri,
                                            rel_name="BA_subcategory_of", id_type="uri")
        except Exception as ex:
            raise Exception(f"add_subcategory_relationship(): Unable to create a subcategory relationship. {ex}")




    """
    NOTE: the next 2 methods, below, may be the future prototype of plugin-specific methods...
          Nothing is returned if all is good, but an Exception is raised in case of problems.
          The methods only handle the plugin-specific part; the "main action" is done by the core method,
          AFTER calling this method (if provided)
    """

    @classmethod
    def add_relationship_before(cls, from_id :str, to_id :str,
                                rel_name :str) -> None:
        """
        A handler to be invoked by the core module before a relationship involving Categories is called.

        If any restriction would apply to adding the parent/child relationship between the specified categories,
        raise an Exception.

        IMPORTANT: NO RELATIONSHIP IS ACTUALLY ADDED

        The restriction are:
            1) the subcategory node cannot be the Root Category
            2) a category cannot be a subcategory of itself

        NOTE: the "BA_subcategory_of" relationship goes FROM the subcategory TO the parent category node

        :param from_id:     String with the uri of the subcategory node
        :param to_id:       String with the uri of the parent-category node
        :param rel_name:    NOT USED
        :return:            None.  If the requested new relationship should not be created, raise an Exception
        """
        # If the sub-category is the Root Category, raise an Exception
        if cls.is_root_category(from_id):        # TODO: this will eventually have to be managed differently
            raise Exception("Cannot add the relationship because the Root Category cannot be made a subcategory of something else")

        # If the parent and the child are the same, raise an Exception
        assert from_id != to_id, \
            "Cannot add a relationship from a Category to itself"



    @classmethod
    def remove_relationship_before(cls, from_id: str, to_id :str,
                                   rel_name: str) -> None:
        """
        A handler to be invoked by the core module before a relationship involving Categories is called.

        If any restriction would apply to removing the parent/child relationship between the specified categories,
        raise an Exception.

        IMPORTANT: NO RELATIONSHIP IS ACTUALLY REMOVED

        The restriction is:
            *) the subcategory node cannot become orphaned as a result of the deletion

        NOTE: the "BA_subcategory_of" relationship goes FROM the subcategory TO the parent category node

        :param from_id:     String with the uri of the subcategory node
        :param to_id:       NOT USED.  String with the uri of the parent-category node
        :param rel_name:    NOT USED
        :return:            None.  If the requested new relationship should not be deleted, raise an Exception
        """
        # If the sub-category has only one parent, raise an Exception
        #print(f"In Category.remove_relationship(). from_id = {from_id}  Parent categories : {cls.get_parent_categories(from_id)}")
        assert len(cls.get_parent_categories(from_id)) != 1, \
            "Cannot sever the relationship because that would leave " \
            "the sub-category orphaned (i.e. with no parent categories)"




    @classmethod
    def switch_parent_category_relationship(cls, child_id :str, old_parent_id :str, new_parent_id :str) -> None:
        """
        TODO: not yet implemented

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
    def switch_subcategory_relationship(cls, parent_id :str, old_child_id :str, new_child_id :str) -> None:
        """
        TODO: not yet implemented

        Switch a parent/child relationship between the specified categories.
        From the parent, take the old child away , and replace it with the new child.

        :param parent_id:
        :param old_child_id:
        :param new_child_id:
        :return:
        """
        #TODO: make use of cls.db.reattach_node()
        pass    # switchChildNode($parentID, $oldChildID, $newChildID)



    @classmethod
    def pin_category(cls, uri, op :str) -> None:
        """
        Set or unset the "pinned" property of the specified Category

        :param uri: The URI of a data node representing a Category
        :param op:  Either "set" or "unset"
        :return:    None
        """
        # TODO: verify that the node is indeed a Category - or make sure that the Schema is enforced
        #       Maybe first locate the data node by multiple criteria

        if op == "set":
            number_set = NeoSchema.update_data_node(data_node=uri, set_dict={"pinned": True})
        elif op == "unset":
            number_set = NeoSchema.update_data_node(data_node=uri, set_dict={"pinned": False})
        else:
            raise Exception("pin_category(): the argument `op` must be equal to either 'set' or 'unset'")

        assert number_set == 1, "pin_category(): no change could be made to the database"



    @classmethod
    def is_pinned(cls, uri :str) -> bool:
        """
        Return True if the given Category has a "pinned" status; otherwise, False

        :param uri: The URI of a data node representing a Category
        :return:    True or False
        """
        all_props = NeoSchema.search_data_node(uri=uri)    # Returns a dict, or None.   # labels="Category"
        assert all_props, "is_pinned(): unable to locate the specified Category node"

        value = all_props.get("pinned", False)  # Unless specifically "pinned", all Categories aren't

        return value



    @classmethod
    def get_see_also(cls, from_category :str) -> [dict]:
        """
        From the given Category, follow all the "see also" links, and return data about
        the Categories that are on their receiving end

        :param from_category:   URI of the Category where the "see_also" relationship originates
        :return:                List (possibly empty) of dictionaries of data from Categories linked to
                                    by a "see_also" relationship.  They keys are "name", "remarks", "uri".
                                    EXAMPLE: [{'name': 'Quotes', 'uri': '823', 'remarks': None}]
        """
        # TODO: perhaps restore the old feature of also storing a "description" field on the relationships

        return NeoSchema.follow_links(class_name="Category", node_id=from_category, id_key="uri",
                                      link_name="BA_see_also", labels="Category", properties=["name", "remarks", "uri"])



    @classmethod
    def create_see_also(cls, from_category :str, to_category :str) -> None:
        """
        Create a "see_also" link between the given Categories, in the specified direction

        :param from_category:   URI of the Category where the "see_also" relationship originates
        :param to_category:     URI of the Category where the "see_also" relationship terminates
        :return:                None
        """
        NeoSchema.add_data_relationship(from_id=from_category, to_id=to_category, id_type="uri",
                                        rel_name="BA_see_also")



    @classmethod
    def remove_see_also(cls, from_category :str, to_category :str) -> None:
        """
        Remove a "see_also" link between the given Categories, in the specified direction.
        If not found, an Exception is raised.

        :param from_category:   URI of the Category where the "see_also" relationship originates
        :param to_category:     URI of the Category where the "see_also" relationship terminates
        :return:                None
        """
        NeoSchema.remove_data_relationship(from_id=from_category, to_id=to_category, id_type="uri",
                                           rel_name="BA_see_also", labels="Category")



    @classmethod
    def import_ontology(cls, df :pd.DataFrame, root_uri :str) -> int:
        """
        Import an ontology of Categories, from a Pandas dataframe whose columns, named "0", "1", "2", ...
        represent levels of increasing depth.
        Each row of the dataframe must have exactly 1 entry, representing a Category name;
        all other entries are expected to be NaN

        EXAMPLE of dataframe (NaN's not shown):
            0           1           2
            Chapter 1
                        Section 1
                                    Paragraph 1
                                    Paragraph 2
                                    Paragraph 3
                        Section 2
                                    Paragraph 1

        Note: the above dataframe may be imported from a header-free CSV file with operations such as
                    pd.read_csv('C:/my_folder/my_file.csv',
                                header=None, encoding = "ISO-8859-1")

        Note: all Category nodes get assigned a unique URI
              based on the namespace currently used by add_subcategory()

        :param df:          A Pandas dataframe with the data to import
        :param root_uri:    A string with the unique URI of an existing Category node that is to be
                                the parent of all the top-level (column "0") imported Categories
        :return:            The number of Category nodes created
        """
        n_cols = len(df.columns)            # Number of columns in the dataframe

        ancestry_name = [None] * n_cols     # A list with None repeated as many times as the number of columns
        ancestry_uri =  [None] * n_cols

        n_created = 0       # Number of new Category nodes created

        for ind in df.index:
            print("-- Row: ", ind, " --")
            s = df.loc[ind]      # a Pandas Series for the current row
            #print(s)

            # Find the first non-NaN index
            #TODO: skip blank entries alongside the NaN's
            level = int(s.first_valid_index())  # Note that the index will be either "0", "1", etc.

            # Get the value at the first non-NaN index
            category_name = s[level]

            print(f"Category: `{category_name}`, at level {level}")

            if level == 0:
                parent_name = "ROOT"
                parent_uri = root_uri
            else:
                parent_name = ancestry_name[level -1]
                parent_uri   = ancestry_uri[level -1]


            print(f"    CREATING `{category_name}` as a subcategory of `{parent_name}` (uri: '{parent_uri}')")
            #new_uri = "TEMP"
            new_uri = Categories.add_subcategory(category_uri=parent_uri,
                                                 data_dict={"subcategory_name": category_name} )
            n_created += 1
            print(f"        newly-assigned uri: '{new_uri}'")
            ancestry_name[level] = category_name
            ancestry_uri[level] = new_uri

            print()

        return n_created





    #####################################################################################################

    '''                                ~   VIEW ITEMS IN CATEGORIES   ~                                '''

    def ________VIEW_ITEMS_IN_CATEGORIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_categories_linked_to_content_item(cls, item_uri :str) -> [{}]:
        """
        Locate and return information about all the Categories
        that the given Content Item is linked to

        :param item_uri:    The URI of a data node representing a Content Item
        :return:            A list of dicts that have the keys "uri", "name", "remarks";
                                any missing value will appear as None
        """
        q = '''
            MATCH (:BA {uri: $item_uri}) - [:BA_in_category] -> (cat :Category)
            RETURN cat.uri AS uri, cat.name AS name, cat.remarks AS remarks
            '''
        result = cls.db.query(q, data_binding={"item_uri": item_uri})
        return result



    @classmethod
    def get_content_items_by_category(cls, uri) -> [{}]:
        """
        Return the records for all nodes linked
        to the Category node identified by its uri value

        :param uri: A string identifying the desired Category
        :return:    A list of dictionaries
                    EXAMPLE:
                    [{'schema_code': 'i', 'uri': '1','width': 450, 'basename': 'my_pic', 'suffix': 'PNG', pos: 0, 'class_name': 'Image'},
                     {'schema_code': 'h', 'uri': '1', 'text': 'Overview', pos: 10, 'class_name': 'Header'},
                     {'schema_code': 'n', 'uri': '1', 'basename': 'overview', 'suffix': 'htm', pos: 20, 'class_name': 'Note'},
                     {'schema_code': 'rs', 'class_name': 'Recordset', 'class_handler': 'recordsets', 'uri': '6965', 'pos': 86, 'n_group': '4', 'order_by': 'name', 'class': 'YouTube Channel'}
                    ]
        """

        # Locate all the Content Items linked to the given Category, and also extract the name of the schema Class they belong to
        # TODO: switch to using one of the Collections methods

        q = '''
            MATCH (n) -[r :BA_in_category]-> (:Category {uri:$category_id}),
            (cl :CLASS)
            WHERE cl.name = n.`_SCHEMA`
            RETURN n, r.pos AS pos, cl.name AS class_name, cl.handler AS class_handler, cl.code AS class_code
            ORDER BY r.pos
            '''

        # TODO: class_code is being phased out in favor of the new class_handler

        result = cls.db.query(q, data_binding={"category_id": uri})
        #cls.db.debug_query_print(q, data_binding={"category_id": uri})


        content_item_list = []
        for elem in result:
            item_record = elem["n"]             # A dictionary with the various fields

            # TODO: eliminate possible conflict if the node happens to have
            #       attributes named "pos" or "class_name"!
            #       Ought to return elements that are dictionaries such as:
            #           {"pos": 15, "class_name": "Recordset", "class_handler": "recordsets", data: {}}

            item_record["pos"] = elem["pos"]                # Inject into the record a positional value
            item_record["class_name"] = elem["class_name"]  # Inject into the record the name of its Class

            if elem.get("class_handler"):
                item_record["class_handler"] = elem["class_handler"]    # Inject into the record the handler of its Class (not always present)

            if elem.get("class_code"):
                item_record["schema_code"] = elem["class_code"]         # Inject into the record the Class code (renamed "schema_code")
                                                                        # TODO: temp, during phaseout of "schema_code" in favor of "class_handler"
            #if ("schema_code" in elem) and (elem["schema_code"]) and ("schema_code" not in item_record):
                #item_record["schema_code"] = elem["schema_code"]


            if "date_created" in item_record:   # TODO: this is a hack, to clean up!
                del item_record["date_created"] # Datetime objects aren't serializable and lead to Flask errors
                                                # TODO: let NeoAccess handle the conversion to string
                                                # TODO: utilize a "type" attribute in the Schema Property node,
                                                #       to inform of the "datetime" data type

            content_item_list.append(item_record)

        #print(f"****** content_item_list: ", content_item_list)
        NeoSchema.remove_schema_info(content_item_list)    # Zap any low-level Schema-related data

        return content_item_list




    #####################################################################################################

    '''                        ~   ADD/REMOVE ITEMS FROM CATEGORIES   ~                               '''

    def ________ADD_REMOVE_ITEMS_FROM_CATEGORIES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def add_content_at_beginning(cls, category_uri :str, item_class_name: str, item_properties: dict, new_uri=None, namespace="data_node") -> str:
        """
        Add a new Content Item, with the given properties and Class, to the beginning of the specified Category.

        TODO: solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
              which can lead to incorrect values of the "pos" relationship attributes.
              -> Follow the new way it is handled in add_content_at_end()

        :param category_uri:    The string "uri" of the Category to which this new Content Media is to be attached
        :param item_class_name: For example, "Image"
        :param item_properties: A dictionary with keys such as "width", "height", "caption","basename", "suffix" (TODO: verify against schema)
        :param new_uri:         Normally, if None (default) the Item ID is auto-generated,
                                    but it can also be provided (if provided, it MUST be unique)
        :param namespace:       Only applicable if new_uri is None : the namespace to use for automatically generating a URI
        :return:                The auto-increment "uri" assigned to the newly-created data node
        """
        if new_uri is None:
            # If a URI was not provided for the newly-created node,
            # then auto-generate it: obtain (and reserve) the next auto-increment value in the given namespace
            new_uri = NeoSchema.reserve_next_uri(namespace=namespace)    # Returns a string


        new_uri = Collections.add_to_collection_at_beginning(collection_uri=category_uri, membership_rel_name="BA_in_category",
                                                             item_class_name=item_class_name, item_properties=item_properties,
                                                             new_uri=new_uri)
        return new_uri



    @classmethod
    def link_content_at_end(cls, category_uri :str, item_uri :str) -> None:
        """
        Given an EXISTING data node, link it to the end of the specified Category.
        If a link to that Category already exists, an Exception is raised.

        :param category_uri:String to identify an existing Category
        :param item_uri:    String to identify an existing Content Item
        :return:            None
        """
        #TODO: verify that the item_uri is not referring to a Category!
        #      More generally, verify that its Class has a "BA_in_category" to
        #      the "Category" Class; this ought to be enforced by link_to_collection_at_end()

        # Link the Content Item to the end of the Category
        Collections.link_to_collection_at_end(item_uri=item_uri, collection_uri=category_uri,
                                              membership_link_name="BA_in_category")



    @classmethod
    def add_content_at_end(cls, category_uri :str, item_class_name: str, item_properties: dict, new_uri=None, namespace="data_node") -> str:
        """
        Add a NEW Content Item, with the given properties and Class, to the end of the specified Category collection.
        First, create a new Data Node, and then link it to the given Category, positioned at the end.

        :param category_uri:    A string to identify the Category
                                    to which this Content Media being newly-created is to be attached
        :param item_class_name: For example, "Image"
        :param item_properties: A dictionary with keys such as "width", "height", "caption","basename", "suffix"
                                    NOTE: if the Class was declared as "strict",
                                          then any key not declared in the Schema gets silently ignored
        :param new_uri:         Normally, if None (default) the Item ID is auto-generated,
                                    but it can also be provided (if provided, it MUST be unique)
        :param namespace:       Only applicable if new_uri is None : the namespace to use for automatically generating a URI
        :return:                The "uri" (passed or created) of the newly-created data node
        """
        if new_uri is None:
            # If a URI was not provided for the newly-created node,
            # then auto-generate it: obtain (and reserve) the next auto-increment value in the given namespace
            new_uri = NeoSchema.reserve_next_uri(namespace=namespace)    # Returns a string


        NeoSchema.create_data_node(class_name=item_class_name, properties=item_properties,
                                   extra_labels="BA", new_uri=new_uri,
                                   silently_drop=True)
        # NOTE: properties such as  "basename", "suffix" are stored with the Image or Document node,
        #       NOT with the Content Item node ;
        #       this is allowed by our convention about "INSTANCE_OF" relationships

        #print(f"add_content_at_end(): Created new Data Node with new_internal_id = {new_internal_id} and new_uri = '{new_uri}'")

        cls.link_content_at_end(category_uri=category_uri, item_uri=new_uri)

        return new_uri



    @classmethod
    def add_content_after_element(cls, category_uri :str, item_class_name: str, item_properties: dict, insert_after :str, new_uri=None, namespace="data_node") -> str:
        """
        Add a NEW Content Item, with the given properties and Class, inserted into the given Category after the specified Item
        (in the context of the positional order encoded in the relationship attribute "pos")

        :param category_uri:    String with a unique "uri" identified of the Category
                                    to which this new Content Media is to be attached
        :param item_class_name: For example, "Image"
        :param item_properties: A dictionary with keys specific to the new Content Item,
                                    such as "width", "height", "caption", "basename", "suffix" (TODO: verify against schema)
        :param insert_after:    The URI of the element after which we want to insert
        :param new_uri:         Normally, if None (default) the Item ID is auto-generated,
                                    but it can also be provided (if provided, it MUST be unique)
        :param namespace:       Only applicable if new_uri is None : the namespace to use for automatically generating a URI
        :return:                The auto-increment "uri" assigned to the newly-created data node
        """
        if new_uri is None:
            # If a URI was not provided for the newly-created node,
            # then auto-generate it: obtain (and reserve) the next auto-increment value in the given namespace
            new_uri = NeoSchema.reserve_next_uri(namespace=namespace)    # Returns a string


        # TODO: solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
        #       which can lead to incorrect values of the "pos" relationship attributes.
        #       -> Follow the new way it is handled in add_content_at_end()
        new_uri = Collections.add_to_collection_after_element(collection_uri=category_uri, membership_rel_name="BA_in_category",
                                                              item_class_name=item_class_name, item_properties=item_properties,
                                                              insert_after=insert_after,
                                                              new_uri=new_uri)
        return new_uri



    @classmethod
    def detach_from_category(cls, category_uri :str, item_uri :str) -> None:
        """
        Sever the link from the specified Content Item and the given Category.
        If it's the only Category that the Content Item is currently linked to,
        an Exception is raised (to avoid leaving that Content Item "stranded")

        :param category_uri:    The URI of a data node representing a Category
        :param item_uri:        The URI of a data node representing a Content Item
        :return:                None
        """
        match_from = cls.db.match(key_name="uri", key_value=item_uri)
        match_to = cls.db.match(labels="Category")
        assert cls.db.number_of_links(match_from=match_from, match_to=match_to, rel_name="BA_in_category") > 1, \
            f"detach_from_category(): Cannot delete the only remaining 'BA_in_category' link " \
            f"from Content Item (URI: '{item_uri}') to Categories"

        NeoSchema.remove_data_relationship(from_id=item_uri, to_id=category_uri,
                                           rel_name="BA_in_category", labels=None)



    @classmethod
    def relocate_across_categories(cls, items :Union[List[str], str], from_category :str, to_category :str):
        """
        Given an existing list of data nodes (representing "Content Items" attached to the specified "from" Category),
        switch each of them to become a "Content Item" of the "to" Category, positioned at the end of it.

        The category-membership relationships ("BA_in_category") is severed from each the "Content Items" to the "from" Category,
        and a new one is created from that "Content Item" to the "to" Collection.

        Return the number of Content Items successfully relocated.

        :param items:           URI, or list of URI's, of Data Node(s)
                                    representing a "Content Items" attached to the "from" Category below
        :param from_category:   The URI of a Category Data Node to which the above Content Item(s) are connected
        :param to_category:     The URI of a Category Data Node to which the above Content Item(s) needs to be switched to
        :return:                The number of Content Items successfully relocated
        """
        return Collections.bulk_relocate_to_other_collection_at_end(items=items,
                                                             from_collection=from_category, to_collection=to_category,
                                                             membership_rel_name="BA_in_category")





    #####################################################################################################

    '''                                  ~   SCHEMA-RELATED    ~                                      '''

    def ________SCHEMA_RELATED________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_items_schema_data(cls, category_uri :str, exclude_system=True) -> dict:
        """
        Locate all the schema Classes used by Content Items attached to the given Category,
        and return a dictionary with the Properties (in the Schema order) of each,
        including Properties of their "ancestor" Classes (ancestral thru "INSTANCE_OF" relationships)

        Properties marked as "system" are optionally excluded (default).

        :param category_uri:A string with the "uri" value to identify the desired Category
        :param exclude_system: [OPTIONAL] If True, Property nodes with the attribute "system" set to True will be excluded;
                                    default is True
        :return:            A dictionary whose keys are Class names (of Content Items attached to the given Category),
                            and whose values are the Properties (in their Schema order) of those Classes.
                            Properties declared in "ancestor" Classes (thru "INSTANCE_OF" relationships)
                            are also included.
                            Properties regarded as "system" ones, such as "uri", are excluded.
                            EXAMPLE:
                                {'Header': ['text'],
                                 'Site Link': ['url', 'name', 'date', 'comments', 'rating', 'read'],
                                 'Note': ['title', 'public', 'date_created', 'basename', 'suffix']
                                 'German Vocabulary': ['Gender', 'German', 'English', 'notes'],
                                 'Quote': ['quote', 'attribution', 'notes'],
                                 'Recordset': ['class', 'order_by', 'clause', 'n_group']
                                 }
        """
        # Locate the names of the Classes of all the Content Items attached to the given Category
        q = '''
            MATCH  (cat :Category {uri: $category_uri, `_SCHEMA`: "Category"}) 
                    <-[:BA_in_category]- (content_item),
                    (cl:CLASS)
            WHERE cl.name = content_item.`_SCHEMA`
            RETURN DISTINCT cl.name AS class_name
            '''
        #cls.db.debug_query_print(q, data_binding={"category_uri": category_uri})

        class_list = cls.db.query(q, data_binding={"category_uri": category_uri},
                                  single_column="class_name")
        # EXAMPLE: ["French Vocabulary", "Site Link"]


        # Now extract all the Property fields, in the schema-stored order, of the above Classes
        records_schema_data = {}
        for class_name in class_list:
            prop_list = NeoSchema.get_class_properties(class_node=class_name,
                                                       include_ancestors=True, sort_by_path_len="ASC",
                                                       exclude_system=exclude_system)
            records_schema_data[class_name] = prop_list

        return records_schema_data




    #####################################################################################################

    '''                          ~   POSITION WITHIN CATEGORIES    ~                                  '''

    def ________POSITIONING________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def check_for_duplicates(cls, category_name :str) -> [str]:
        """
        This is a diagnostic method to check for problems.

        Look for duplicates values in the "pos" attributes
        of the "BA_in_category" links ending in the specified Category node

        :param category_name:   To identifying the Category of interest
        :return:                In case of duplicates, return a list of texts with error reports;
                                    if no duplicates, return an empty list
        """
        q = '''
            MATCH (ci1)-[r1:BA_in_category] -> (:Category {name: $name}) <- [r2:BA_in_category]-(ci2) 
            WHERE r1.pos = r2.pos AND id(ci1) < id(ci2)
            RETURN r1.pos AS pos, ci1.uri AS item1, ci2.uri AS item2
            ORDER BY r1.pos
            '''

        data_binding = {"name": category_name}

        #cls.db.debug_query_print(q, data_binding)
        duplicates = cls.db.query(q, data_binding)

        if not duplicates:
            return []           # No problems found
        else:
            problem_list = []
            for record in duplicates:
                problem = f"Problem found: Duplicate 'pos' value ({record['pos']}), " \
                          f"shared by links to Content Items with URIs `{record['item1']}` and `{record['item2']}`"
                problem_list.append(problem)

            return problem_list



    @classmethod
    def check_all_categories_for_duplicates(cls) -> [dict]:
        """
        This is a diagnostic method to check for problems.

        :return:    A (possibly-empty) list of dicts, detailing all located duplicates
        """
        q = '''
            MATCH (ci1)-[r1 :BA_in_category]->(c :Category)<-[r2 :BA_in_category]-(ci2)
            WHERE r1.pos = r2.pos AND id(ci1) < id(ci2)
            RETURN c.name AS category_name, r1.pos AS pos, ci1.uri AS uri1, ci2.uri AS uri2
            ORDER BY category_name, pos
            '''
        return cls.db.query(q)



    @classmethod
    def reassign_positional_values(cls, category_name :str) -> None:
        """
        To re-assign positional values of Content Items within the given Category
        (starting at 0 and proceeding in increments of Collections.DELTA_POS):

        :param category_name:
        :return:                None
        """
        q = f'''       
            MATCH (ci)-[r :BA_in_category]->(n :Category {{name: $category_name}})           
            WITH r.pos AS POS, id(ci) AS NODE_ID           
            ORDER by r.pos
            
            WITH collect(NODE_ID) AS ID_LIST           
            WITH size(ID_LIST) AS TOT, ID_LIST           
            WITH range(0, TOT-1) AS INDEX_LIST, ID_LIST
            
            UNWIND INDEX_LIST AS i
            
            MATCH (x)-[newr :BA_in_category]->(n :Category {{name: $category_name}}) WHERE id(x) = ID_LIST[i]
            
            SET newr.pos = i * {Collections.DELTA_POS}
            
            RETURN x.uri, i, newr.pos
        '''
        cls.db.query(q, data_binding={"category_name": category_name})



    @classmethod
    def reposition_content(cls, category_uri :str, uri: str, move_after_n: int):
        """
        Reposition the given Content Item after the n-th item (counting starts with 1) in specified Category.

        Note: there's no harm (though it's wasteful) to move an item to a final sequence position where it already is;
              its "pos" value will change

        :param category_uri:    A string identifying the desired Category
        :param uri:             A string with the URI of the Content Item we're repositioning
        :param move_after_n:    The index (counting from 1) of the item after which we want to position the item being moved
                                    Use n=0 to indicate "move before anything else"
        :return:
        """
        assert NeoSchema.is_valid_uri(category_uri), "ERROR: argument 'category_uri' is invalid"
        assert NeoSchema.is_valid_uri(uri), "ERROR: argument 'uri' is not a valid string"
        assert type(move_after_n) == int, "ERROR: argument 'move_after_n' is not an integer"
        assert move_after_n >= 0, "ERROR: argument 'move_after_n' cannot be negative"

        # Collect a subset of the first sorted "pos" values: enough values to cover across the insertion point
        number_to_consider = move_after_n + 1
        q = f'''
            MATCH (c:BA:Category {{uri: $category_id}}) <- [r:BA_in_category] - (:BA)
            WITH  r.pos AS pos
            ORDER by pos
            LIMIT {number_to_consider}
            WITH collect(pos) AS POS_LIST
            RETURN POS_LIST
            '''

        result = cls.db.query(q, {"category_id": category_uri})  # If nothing found, this will be [{'POS_LIST': []}]
        pos_list = result[0].get("POS_LIST")    # A subset of the first sorted "pos" values
        #print("pos_list: ", pos_list)

        if pos_list == []:
            # The Category is empty (or doesn't exist)
            raise Exception(f"Category (id {category_uri}) not found, or empty")

        if move_after_n == 0:
            # Move to top
            #print("Moving to the top")
            top_pos = pos_list[0]
            new_pos = top_pos - cls.DELTA_POS
        elif move_after_n >= len(pos_list):
            # Move to bottom
            #print("Moving to the bottom")
            top_pos = pos_list[-1]      # The last element in the list
            new_pos = top_pos + cls.DELTA_POS
        else:
            pos_above = pos_list[move_after_n - 1]  # The "pos" value of the Item just above the insertion point
            pos_below = pos_list[move_after_n]      # The "pos" value of the Item just below
            #print(f"pos_above: {pos_above} | pos_below: {pos_below}")
            if pos_below == pos_above + 1:
                # There's no room; shift everything that is past that position, by a count of DELTA_POS
                #print(f"********* RELOCATING ITEMS (skipping the first {move_after_n}) ***********")
                cls.relocate_positions(category_uri, n_to_skip=move_after_n, pos_shift=cls.DELTA_POS)
                new_pos = pos_above + int(cls.DELTA_POS/2)			# This will be now be the empty halfway point
            else:
                new_pos = int((pos_above + pos_below) / 2)		# Take the halfway point, rounded down


        # Change the "pos" attribute of the relationship to the Content Item being moved
        q = f'''
            MATCH (:BA:Category {{uri: $category_id}}) <- [r:BA_in_category] - (:BA {{uri: $uri}})
            SET r.pos = {new_pos}
            '''

        #print("q: ", q)

        result = cls.db.update_query(q, {"category_id": category_uri, "uri": uri})
        number_props_set = result.get('properties_set')
        #print("number_props_set: ", number_props_set)
        if number_props_set != 1:
            raise Exception(f"Content Item (id {uri}) not found in Category (id {category_uri}), or could not be moved")



    @classmethod
    def relocate_positions(cls, category_uri :str, n_to_skip: int, pos_shift: int) -> int:
        """
        Shift the values of the "pos" attributes on the "BA_in_category" relationships
        from the given Category node, by the given amount;
        however, SKIP the first n_to_skip entries (as sorted by the "pos" attribute)

        EXAMPLE - given the following order of the relationships attached to the given Category:
            pos
        1:   45
        2:   84
        3:   91

        then relocate_positions(category_uri, n_to_skip=1, pos_shift=100) will result in:
            pos
        1:   45     <= got skipped
        2:  184
        3:  191

        :param category_uri:A string identifying the desired Category
        :param n_to_skip:   The number of relationships (after sorting them by "pos") NOT to re-position
                                Must be an integer >= 1 (it'd be pointless to shift everything!)
        :param pos_shift:   The increment by which to shift the values of the "pos" attributes on the relationships

        :return:            The number of repositionings performed
        """
        assert NeoSchema.is_valid_uri(category_uri), "ERROR: argument 'category_uri' is not a valid string"
        assert type(n_to_skip) == int, "ERROR: argument 'n_to_skip' is not an integer"
        assert type(pos_shift) == int, "ERROR: argument 'pos_shift' is not an integer"
        assert n_to_skip >= 1, "ERROR: argument 'n_to_skip' must be at least 1"

        q = f'''
            MATCH (c:BA:Category {{uri: $category_id}}) <- [r:BA_in_category] - (:BA)
            WITH  r.pos AS pos, r
            ORDER by pos
            SKIP {n_to_skip}
            SET r.pos = r.pos + {pos_shift}
            '''

        result = cls.db.update_query(q, {"category_id": category_uri})
        return result.get('properties_set')



    @classmethod
    def swap_content_items(cls, uri_1 :str, uri_2 :str, cat_id :str) -> None:
        """
        Swap the positions of the specified Content Items within the given Category

        :param uri_1:   A string with the uri of the 1st Content Item
        :param uri_2:   A string with the uri of the 2nd Content Item
        :param cat_id:  A string with the uri of the Category
        :return:        None
        """

        # Validate the arguments
        assert uri_1 != uri_2, \
            f"Attempt to swap a Content Item (URI `{uri_1}`) with itself!"


        # Look for a Category node (c) that is connected to 2 Content Items (n1 and n2)
        #   thru "BA_in_category" relationships; then swap the "pos" attributes on those relationships
        q = '''
            MATCH (n1 {uri: $uri_1})
                        -[r1:BA_in_category]->(c:BA:Category {uri: $cat_id})<-[r2:BA_in_category]-
                  (n2 {uri: $uri_2})
            WITH r1.pos AS tmp, r1, r2
            SET r1.pos = r2.pos, r2.pos = tmp
            '''

        data_binding = {"uri_1": uri_1, "uri_2": uri_2, "cat_id": cat_id}

        #print(q)
        #print(data_binding)

        stats = cls.db.update_query(q, data_binding)
        #print("stats of query: ", stats)

        assert stats != {},  \
            f"Irregularity detected in swap action: Unable to determine the success of the operation"

        number_properties_set = stats.get("properties_set")

        assert number_properties_set, \
            f"Failure to swap content items `{uri_1}` and `{uri_2}` within Category `{cat_id}`. Query: {q}"

        assert number_properties_set == 2, \
            f"Irregularity detected in swap action: {number_properties_set} properties were set," \
            f" instead of the expected 2"




    #####################################################################################################

    '''                                  ~   PAGE HANDLER   ~                                         '''

    def ________PAGE_HANDLER________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def viewer_handler(cls, category_uri :str):
        """
        Handler function for the Flask page generator "BA_pages_routing.py"

        :param category_uri: A string identifying the desired Category
        :return:             A list of dictionaries, with one element for each "sibling";
                                each element contains the 'internal_id' and 'neo4j_labels' keys,
                                plus whatever attributes are stored on that node.
                                EXAMPLE of single element:
                                {'name': 'French', 'internal_id': 123, 'neo4j_labels': ['Category', 'BA']}
        """
        # TODO: expand to cover all the data needs of BA_pages_routing.py
        # TODO: maybe move to DataManager layer

        category_internal_id = NeoSchema.get_data_node_internal_id(uri = category_uri)
        siblings_categories = Categories.get_sibling_categories(category_internal_id)

        return siblings_categories
