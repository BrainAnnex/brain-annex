from typing import Union, List
from brainannex.neo_schema.neo_schema import NeoSchema
from neoaccess import NeoAccess


class Collections:
    """
    An ordered sequence of Data Nodes.

    We define a "Collection" as an entity to which a variety of Data Nodes
    are attached, with positional attributes in their links.

    In terms of implementation, it's a hub, with a central data node (the "Collection"),
    to which any number of Data Nodes (or "Collection Items") are linked;
    the relationship name can be anything (user-passed) but it gets assigned a property
    named "pos", which is managed by this class, to maintain and alter the sequential order.

    Example of use case: "pages" of "Content Items" attached to a "Category"
    """
    # TODO: maybe rename the class to OrderedCollections (or OrderedSequences)

    # Class variables

    db = None                       # MUST be set before using this class!

    DELTA_POS = 20                  # Arbitrary default shift in "pos" value between Collection Items that are adjacent
                                    # (i.e. next in sequence);
                                    # empirically shown best to be even, and not too small nor too large

    membership_rel_name = None      # NOT IN USE.   TODO: maybe use instantiation for this class, and set at that time



    @classmethod
    def set_database(cls, db :NeoAccess) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, created with the NeoAccess library
        :return:    None
        """

        assert type(db) == NeoAccess, \
            "Collections.set_database(): argument passed isn't a valid `NeoAccess` object"

        cls.db = db



    @classmethod
    def initialize_collections(cls) -> (int, str):
        """
        Create a new Schema Class node that represents a "Collection"

        :return:    An (int, str) pair of integers with the internal database ID
                        and the unique uri assigned to the node just created
        """
        return NeoSchema.create_class(name="Collections", strict = False)



    @classmethod
    def is_collection(cls, collection_uri :str) -> bool:
        """
        Return True if the Data Node with the given uri is a Collection,
        that is, if its schema is a Class that is an INSTANCE_OF the "Collections" Class

        :param collection_uri:  A string with the URI of a Data Node
        :return:                True if the given data node is a Collection, or False otherwise
        """

        #TODO: maybe allow the scenario where there's a longer chain of "INSTANCE_OF" relationships??
        q = '''
            MATCH p=({uri: $collection_uri}) -[:SCHEMA]-> (:CLASS) 
                    -[:INSTANCE_OF]-> 
                    (:CLASS {name: "Collections"})
            RETURN count(p) AS number_paths
            '''
        data_binding = {"collection_uri": collection_uri}
        number_paths = cls.db.query(q, data_binding, single_cell="number_paths")

        return True if number_paths > 0 else False



    @classmethod
    def collection_size(cls, collection_id :str, membership_rel_name: str, skip_check=False) -> int:
        """
        Return the number of elements in the given Collection (i.e. Data Items linked to it thru the specified relationship)

        :param collection_id:       The uri of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship from other Data Items to the given Collection node
        :param skip_check:          If True, no check is done to verify that the data node whose uri matches collection_id
                                    is indeed a Collection.
                                    Without a check, this function will return a zero if given a bad collection_id;
                                    with a check, it'll raise an Exception
        :return:                    The number of elements in the given Collection (possibly zero)
        """
        if not skip_check:
            assert cls.is_collection(collection_id), \
                    f"The data node with uri `{collection_id}` doesn't exist or is not a Collection"

        q = f'''
            MATCH ({{uri: $collection_id}}) <- [:{membership_rel_name}] - (i) 
            RETURN count(i) AS node_count
            '''
        data_binding = {"collection_id": collection_id}

        number_items_attached = cls.db.query(q, data_binding, single_cell="node_count")
        return number_items_attached



    @classmethod
    def delete_collection_NOT_IMPLEMENTED(cls, collection_uri :str) -> None:
        """
        #TODO: implement

        Delete the specified Collection, provided that there are no Data Items linked to it.
        In case of error or failure, an Exception is raised.

        :param collection_uri:  The "uri" string value identifying the desired Collection
        :return:                None
        """
        pass



    @classmethod
    def add_to_collection_at_beginning(cls, collection_uri :str, membership_rel_name: str, item_class_name: str, item_properties: dict,
                                       new_uri=None) -> str:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add it at the beginning of the specified Collection, linked by the specified relationship

        EXAMPLE:  new_uri = add_to_collection_at_beginning(collection_id=708, membership_rel_name="BA_in_category",
                                                        item_class_name="Headers", item_properties={"text": "New Caption, at the end"})
        <SEE add_to_collection_at_end>

        :return:                    The auto-increment "uri" assigned to the newly-created data node
        """
        #TODO:  the Data Node creation perhaps should be done ahead of time, and doesn't need to be the responsibility of this class!
        #TODO:  solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
        #       which can lead to incorrect values of the "pos" relationship attributes.
        #       -> Follow the new way it is handled in link_to_collection_at_end()

        assert NeoSchema.is_valid_uri(collection_uri), "The argument `collection_uri` isn't a valid URI string"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"

        # TODO: this query and the one in add_data_point(), below, ought to be combined, to avoid concurrency problems
        q = f'''
            MATCH (n:BA) - [r :{membership_rel_name}] -> (c:BA {{uri: $collection_id}}) 
            RETURN min(r.pos) AS min_pos
            '''
        data_binding = {"collection_id": collection_uri}

        min_pos = cls.db.query(q, data_binding, single_cell="min_pos")  # This will be None if the Collection has no elements

        if min_pos is None:
            pos = 0                         # Arbitrary initial value for cases when the Collection has no elements
        else:
            pos = min_pos - cls.DELTA_POS   # Go some distance before the beginning

        data_binding = item_properties

        return NeoSchema.add_data_point_OLD(class_name=item_class_name,
                                            data_dict=data_binding,
                                            labels=["BA", item_class_name],
                                            connected_to_id=collection_uri, connected_to_labels="BA",
                                            rel_name=membership_rel_name,
                                            rel_prop_key="pos", rel_prop_value=pos,
                                            new_uri=new_uri
                                            )



    @classmethod
    def link_to_collection_at_end(cls, item_uri :str, collection_uri :str, membership_rel_name :str) -> None:
        """
        Given an existing data node (meant to be a "Collection Item"),
        link it to the end of the specified Collection data node,
        using the requested relationship name.

        If a link already exists, an Exception is raised.

        :param item_uri:            The URI of an existing Data Node representing a "Collection Item"
        :param collection_uri:      The URI of an existing Collection Data Node
        :param membership_rel_name: The name to give to the relationship
                                        in the direction from the "Collection Item" to the Collection node
        :return:                    None
        """
        # TODO: use this function as a ***ROLE MODEL*** for linking at the start
        # TODO: (optionally?) enforce that the respective Classes of the Data Nodes are a relationship named membership_rel_name;
        #       use NeoSchema.class_relationship_exists()

        # TODO: validate more thoroughly the URI's
        assert item_uri, \
            "link_to_collection_at_end: Missing `item_uri` argument"

        assert collection_uri, \
            "link_to_collection_at_end: Missing `collection_uri` argument"

        assert membership_rel_name, \
            "link_to_collection_at_end: Missing `item_uri` membership_rel_name"

        # ATOMIC database update that locates the next-available "pos" number, and creates a relationship using it
        # The "OPTIONAL MATCH" is used to compute a new positional value
        q = f'''
            MATCH (ci), (collection) 
            WHERE ci.uri = $item_uri 
              AND collection.uri = $collection_uri
              AND NOT ( (ci) -[:`{membership_rel_name}`]-> (collection) )
            WITH ci, collection
            
            OPTIONAL MATCH (old_ci) -[r :`{membership_rel_name}`]-> (collection)
            WITH r.pos AS pos, collection, ci
            WITH 
                CASE WHEN pos IS NULL THEN
                    0
                ELSE
                    max(pos) + {cls.DELTA_POS}
                END AS new_pos, collection, ci
            
            MERGE (ci) -[:`{membership_rel_name}` {{pos: new_pos}}]-> (collection)
            '''
        #cls.db.debug_query_print(q, data_binding={"collection_uri": collection_uri, "item_uri": item_uri})

        status = cls.db.update_query(q,
                                     data_binding={"collection_uri": collection_uri, "item_uri": item_uri})
        #print("link_to_collection_at_end(): status is ", status)

        # status should be contain {'relationships_created': 1, 'properties_set': 1}

        assert status.get('relationships_created') == 1, \
            f"link_to_collection_at_end(): failed to create a new link " \
            f"to a Collection with URI '{collection_uri}'"

        assert status.get('properties_set') == 1, \
            f"link_to_collection_at_end(): failed to set the positional value to the new link " \
            f"to the Collection with URI '{collection_uri}'"



    @classmethod
    def relocate_to_other_collection_at_end(cls, item_uri :str, from_collection_uri :str, to_collection_uri :str, membership_rel_name :str):
        """
        Given an existing data node (representing a "Collection Item" of the specified "from" Collection),
        switch it to become a "Collection Item" of the "to" Collection, positioned at the end of it.

        The collection-membership relationship is severed from the "Collection Item" to the "from" Collection,
        and a new one is created from the "Collection Item" to the "to" Collection.

        In case no operation is performed, an Exception is raised.

        :param item_uri:            The URI of a Data Node representing a "Collection Item" of the "from" Collection below
        :param from_collection_uri: The URI of a Collection Data Node to which the above "Collection Item" is connected
        :param to_collection_uri:   The URI of a Collection Data Node to which the above "Collection Item" needs to be switched to
        :param membership_rel_name: The name to give to the relationship
                                        in the direction from the "Collection Item" to the Collection node
        :return:                    None
        """
        # TODO: perhaps to ditch, now that we have bulk_relocate_to_other_collection_at_end()

        # Use an ATOMIC operation.  If any of the matches fail, no operation is performed
        # The "OPTIONAL MATCH" is used to compute a new positional value
        q = f'''
            MATCH (collection_from) , (collection_to) ,
                  (moving_ci) -[old_r :`{membership_rel_name}`]-> (collection_from)
            WHERE collection_from.uri = $from_collection_uri
              AND collection_to.uri = $to_collection_uri
              AND moving_ci.uri = $item_uri
            WITH collection_from, collection_to, moving_ci, old_r
                        
            OPTIONAL MATCH (existing_ci) -[r :`{membership_rel_name}`]-> (collection_to)
            WITH r.pos AS pos, collection_from, collection_to, moving_ci, old_r
            WITH 
                CASE WHEN pos IS NULL THEN
                    0
                ELSE
                    max(pos) + {cls.DELTA_POS}
                END AS new_pos, collection_from, collection_to, moving_ci, old_r
            
            DELETE old_r
            MERGE (moving_ci)-[:`{membership_rel_name}` {{pos: new_pos}}]->(collection_to)
            '''
        #cls.db.debug_query_print(q, data_binding={"from_collection_uri": from_collection_uri,
                                                  #"to_collection_uri": to_collection_uri,
                                                  #"item_uri": item_uri})

        status = cls.db.update_query(q,
                                     data_binding={"from_collection_uri": from_collection_uri,
                                                   "to_collection_uri": to_collection_uri,
                                                   "item_uri": item_uri})
        #print("switch_to_other_collection_at_end(): status is ", status)

        # status should contain {'relationships_deleted': 1, 'relationships_created': 1, 'properties_set': 1}

        assert status.get('relationships_deleted') == 1, \
            f"relocate_to_other_collection_at_end(): failed to locate or delete the old '{membership_rel_name}' link " \
            f"that goes to a Collection with URI '{from_collection_uri}'"

        assert status.get('relationships_created') == 1, \
            f"relocate_to_other_collection_at_end(): failed to create a new link " \
            f"to a Collection with URI '{to_collection_uri}'"

        assert status.get('properties_set') == 1, \
            f"relocate_to_other_collection_at_end(): failed to set the positional value to the new link " \
            f"to a Collection with URI '{to_collection_uri}'"



    @classmethod
    def bulk_relocate_to_other_collection_at_end(cls, items :Union[List[str], str],
                                                 from_collection :str, to_collection :str, membership_rel_name :str) -> int:
        """
        Given an existing list of data nodes (representing "Collection Items" of the specified "from" Collection),
        switch each of them to become a "Collection Item" of the "to" Collection, positioned at the end of it.

        The collection-membership relationship is severed from each of the "Collection Items" to the "from" Collection,
        and a new one is created from that "Collection Item" to the "to" Collection.

        Return the number of Collection Items successfully relocated.

        :param items:               URI, or list of URI's, of Data Node(s)
                                        representing a "Collection Items" of the "from" Collection below
        :param from_collection:     The URI of a Collection Data Node to which the above Collection Item(s) are connected
        :param to_collection:       The URI of a Collection Data Node to which the above Collection Item(s) needs to be switched to
        :param membership_rel_name: The name to give to the relationship
                                        in the direction from the "Collection Item" to the Collection node
        :return:                    The number of Collection Items successfully relocated
        """
        # If a scalar was passed, turn into a list
        if type(items) == str:
            items = [items]
        else:
            assert type(items) == list, \
                "bulk_relocate_to_other_collection_at_end(): the argument `items` must be a string URI, or a list of them"


        # Use an ATOMIC operation.  If any of the matches fail, no operation is performed
        # The "OPTIONAL MATCH" is used to compute a new initial positional value to use on the to_collection
        q = f'''
            MATCH (collection_from) , (collection_to)                
            WHERE collection_from.uri = $from_collection
              AND collection_to.uri = $to_collection            
            WITH collection_from, collection_to
                        
            // Attempt to locate Items already on the "to" Collection
            OPTIONAL MATCH (existing_ci) -[r :`{membership_rel_name}`]-> (collection_to)
            WITH r.pos AS pos, collection_from, collection_to
            WITH 
                CASE WHEN pos IS NULL THEN
                    0                           // The "to" Collection is devoid of Items
                ELSE
                    max(pos) + {cls.DELTA_POS}  // A value greater than that of the last Item
                END AS new_start_pos, collection_from, collection_to
            
            WITH range(0, size($item_list)) AS ITEM_INDEX_LIST, 
                 new_start_pos, collection_from, collection_to
            
            UNWIND ITEM_INDEX_LIST AS i         // Used to process each Collection Item in turn
                MATCH (moving_ci) -[old_r :`{membership_rel_name}`]-> (collection_from)
                WHERE moving_ci.uri = $item_list[i]
                WITH moving_ci, old_r, collection_to, 
                     new_start_pos + i * {cls.DELTA_POS} AS new_pos
                
                DELETE old_r
                MERGE (moving_ci) -[:`{membership_rel_name}` {{pos: new_pos}}]-> (collection_to)
            '''

        data_binding={"from_collection": from_collection,
                      "to_collection": to_collection,
                      "item_list": items}

        #cls.db.debug_query_print(q, data_binding=data_binding)

        status = cls.db.update_query(q, data_binding=data_binding)
        #print("bulk_relocate_to_other_collection_at_end(): status is ", status)
        # status should contain, for example {'relationships_deleted': 8, 'relationships_created': 8, 'properties_set': 8}

        number_relationships_created = status.get('relationships_created', 0)

        assert number_relationships_created <= len(items), \
            f"bulk_relocate_to_other_collection_at_end(): " \
            f"The number of created links ({number_relationships_created}) exceeds " \
            f"the number of Collection Items to move ({len(items)})"

        assert status.get('relationships_deleted', 0) == number_relationships_created, \
            f"bulk_relocate_to_other_collection_at_end(): " \
            f"The number of links deleted doesn't match " \
            f"that of the links created ({number_relationships_created})"

        assert status.get('properties_set', 0) == number_relationships_created, \
            f"bulk_relocate_to_other_collection_at_end(): " \
            f"The number of properties set doesn't match " \
            f"that of the links deleted and created ({number_relationships_created})"

        return number_relationships_created



    @classmethod
    def add_to_collection_at_end(cls, collection_uri :str, membership_rel_name: str, item_class_name: str, item_properties: dict,
                                 new_uri=None) -> str:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add it at the end of the specified Collection, linked by the specified relationship

        EXAMPLE:  new_uri = add_to_collection_at_end(collection_id=708, membership_rel_name="BA_in_category",
                                                     item_class_name="Headers", item_properties={"text": "New Caption, at the end"}

        :param collection_uri:      The uri of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name:
        :param item_class_name:
        :param item_properties:
        :param new_uri:             Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                    The auto-increment "uri" assigned to the newly-created data node
        """
        #TODO:  DITCH!  The Data Node creation probably should be done ahead of time, and doesn't need to be the responsibility of this class!
        #TODO:  solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
        #       which can lead to incorrect values of the "pos" relationship attributes.
        #       -> Follow the new way it is handled in link_to_collection_at_end()

        assert NeoSchema.is_valid_uri(collection_uri), "The argument `collection_uri` isn't a valid URI string"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"

        # TODO: this query and the one in add_data_point(), below, ought to be combined, to avoid concurrency problems
        q = f'''
            MATCH (n:BA) -[r :{membership_rel_name}]-> (c:BA {{uri: $collection_id}}) 
            RETURN max(r.pos) AS max_pos
            '''
        data_binding = {"collection_id": collection_uri}

        max_pos = cls.db.query(q, data_binding, single_cell="max_pos")  # This will be None if the Collection has no elements

        if max_pos is None:
            pos = 0                         # Arbitrary initial value for cases when the Collection has no elements
        else:
            pos = max_pos + cls.DELTA_POS   # Go some distance past the end

        data_binding = item_properties

        #cls.db.debug_print(q, data_binding, "add_to_collection_at_end", True)

        return NeoSchema.add_data_point_OLD(class_name=item_class_name,
                                            data_dict=data_binding,
                                            labels=["BA", item_class_name],
                                            connected_to_id=collection_uri, connected_to_labels="BA",
                                            rel_name=membership_rel_name,
                                            rel_prop_key="pos", rel_prop_value=pos,
                                            new_uri=new_uri
                                            )



    @classmethod
    def add_to_collection_after_element(cls, collection_uri :str, membership_rel_name: str,
                                        item_class_name: str, item_properties: dict, insert_after :str,
                                        new_uri=None) -> str:
        """
        Create a new data node, of the class specified in item_class_name, and with the given properties -
        and add to the specified Collection, linked by the specified relationship and inserted after the given collection Item
        (in the context of the positional order encoded in the relationship attribute "pos")

        :param collection_uri:      The uri of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship to which the positions ("pos" attribute) apply
        :param item_class_name:     Name of the Class for the newly-created node
        :param item_properties:     Dictionary with the properties of the newly-created node
        :param insert_after:        The URI of the element after which we want to insert
        :param new_uri:             Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                    The auto-increment "uri" assigned to the newly-created data node
        """
        #TODO:  the Data Node creation perhaps should be done ahead of time, and doesn't need to be the responsibility of this class!
        #TODO: solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
        #       which can lead to incorrect values of the "pos" relationship attributes.
        #       -> Follow the new way it is handled in link_to_collection_at_end()

        assert NeoSchema.is_valid_uri(collection_uri), "The argument `collection_uri` isn't a valid URI string"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"
        assert type(insert_after) == str, "The argument `insert_after` MUST be a string"

        q = f'''
        MATCH (n_before :BA {{uri: $insert_after}})-[r_before :{membership_rel_name}] 
                    -> (c :BA {{uri: $collection_id}}) <-
                                            [r_after :{membership_rel_name}]-(n_after :BA)
        WHERE r_after.pos > r_before.pos
        RETURN r_before.pos AS pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''
        #EXAMPLE:
        '''
        MATCH (n_before :BA {uri: 717})-[r_before :BA_in_category] -> (c :BA {uri: 708}) <-[r_after :BA_in_category]-(n_after :BA)
        WHERE r_after.pos > r_before.pos
        RETURN r_before.pos AS pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''

        data_binding = {"collection_id": collection_uri, "insert_after": insert_after}

        # ALTERNATE WAY OF PHRASING THE QUERY:
        '''
        MATCH (n_before:BA {uri: 717})-[r_before :BA_in_category] -> (c:BA {uri: 708}) <- [r_after :BA_in_category]-(n_after :BA)
        WITH r_before.pos AS pos_before, r_after
        WHERE r_after.pos > pos_before
        RETURN pos_before, r_after.pos AS pos_after
        ORDER BY pos_after
        LIMIT 1
        '''

        result = cls.db.query(q, data_binding, single_row=True)
        print(result)
        if result is None:
            # An empty find is indicative of either an "insert at the end" (no n_after found),
            #       or a bad insert_after value that matches no node
            node = NeoSchema.search_data_node(uri = insert_after)
            if node is None:
                raise Exception(f"There is no node with the `uri` value ({insert_after}) passed by `insert_after`")

            print("It's case of insert AT THE END")
            return cls.add_to_collection_at_end(collection_uri, membership_rel_name, item_class_name, item_properties, new_uri=new_uri)


        pos_before = result["pos_before"]
        pos_after = result["pos_after"]

        if pos_after == pos_before + 1:
            # There's no room; shift everything that is past that position, by a count of DELTA_POS
            print(f"********* SHIFTING DOWN ITEMS whose `pos` value is {pos_after} and above  ***********")
            cls.shift_down(collection_id=collection_uri, membership_rel_name=membership_rel_name, first_to_move=pos_after)
            new_pos = pos_before + int(cls.DELTA_POS/2)			# This will be now be the empty halfway point
        else:
            new_pos = int((pos_before + pos_after) / 2)		    # Take the halfway point, rounded down


        return NeoSchema.add_data_point_OLD(class_name=item_class_name,
                                            data_dict=item_properties,
                                            labels=["BA", item_class_name],
                                            connected_to_id=collection_uri, connected_to_labels="BA",
                                            rel_name=membership_rel_name,
                                            rel_prop_key="pos", rel_prop_value=new_pos,
                                            new_uri=new_uri
                                            )

        #link_to = [{"labels": "BA", "key": "uri", "value": collection_id,
        #            "rel_name": membership_rel_name, "rel_attrs": {"pos": new_pos}}]

        #new_neo_id = cls.db.create_node_with_relationships(labels="BA", properties=item_properties, connections=link_to)

        #uri = NeoSchema.register_existing_data_node(class_name=item_class_name, existing_neo_id=new_neo_id, new_uri=new_uri)

        #return uri



    @classmethod
    def shift_down(cls, collection_id :str, membership_rel_name :str, first_to_move :int) -> int:
        """
        Shift down the positions (values of the "pos" relationship attributes) by an arbitrary fixed amount,
        starting with nodes with the specified position value (and all greater values);
        this operation applies to nodes linked to the specified Collection thru a relationship with the given name.

        :param collection_id:       The uri of a data node whose schema is an instance of the Class "Collections"
        :param membership_rel_name: The name of the relationship to which the positions ("pos" attribute) apply
        :param first_to_move:       All position ("pos") values greater or equal to this one will get shifted down
        :return:                    The number of modified items
        """
        # Starting with a particular Collection node, look at all its relationships whose name is specified by membership_rel_name,
        #       and increase the value of the "pos" attributes on those relationships if their current values is at least first_to_move
        q = f'''
        MATCH (c:BA {{uri: $collection_id}}) <- [r :{membership_rel_name}] - (n :BA)
        WHERE r.pos >= $first_to_move
        SET r.pos = r.pos + {cls.DELTA_POS}
        '''
        data_binding = {"collection_id": collection_id, "first_to_move": first_to_move}

        status = cls.db.update_query(q, data_binding)
        return status.get("properties_set", 0)
