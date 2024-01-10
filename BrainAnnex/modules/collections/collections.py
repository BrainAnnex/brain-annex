from BrainAnnex.modules.neo_schema.neo_schema import NeoSchema


class Collections:
    """
    An ordered sequence of Data Content Items.

    An entity to which a variety of nodes (e.g. representing records or media)
    is attached, with a positional attribute.

    In terms of implementation, it's a hub, with a central data node (the "Collection"),
    to which any number of "Content Items" (or "Collection Items") are linked;
    the relationship name can be anything (user-passed) but it is given a property
    named "pos", which is managed by this class, to maintain and alter the sequential order.

    A generalization of Categories.
    """

    # Class variables

    db = None                       # MUST be set before using this class!

    DELTA_POS = 20                  # Arbitrary shift in "pos" value;
                                    # empirically shown best to be even, and not too small nor too large

    membership_rel_name = None      # NOT IN USE.   TODO: maybe use instantiation for this class, and set at that time



    @classmethod
    def is_collection(cls, collection_uri :str) -> bool:
        """
        Return True if the data node whose "uri" has the given value is a Collection,
        that is, if its schema is a Class that is an INSTANCE_OF the "Collection" Class

        :param collection_uri:  A string with the URI of a data node
        :return:                True if the given data node is a Collection, or False otherwise
        """
        #TODO: maybe allow the scenario where there's a longer chain of "INSTANCE_OF" relationships

        q = '''
            MATCH p=(n :BA {uri: $collection_id}) -[:SCHEMA]-> (s :CLASS) -[:INSTANCE_OF]-> (coll :CLASS {name: "Collections"})
            RETURN count(p) AS number_paths
            '''
        data_binding = {"collection_id": collection_uri}
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
            assert cls.is_collection(collection_id), f"The data node with uri `{collection_id}` doesn't exist or is not a Collection"

        q = f'''
            MATCH (coll :BA {{uri: $collection_id}}) <- [:{membership_rel_name}] - (i :BA) 
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
        #       -> Follow the new way it is handled in add_content_at_end()

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
    def link_to_collection_at_end(cls, collection_dbase_id :int, item_dbase_id :int, membership_rel_name :str) -> None:
        """
        Given an EXISTING data node, link it to the end of the specified Collection,
        using the requested relationship name.

        If a connection to that Collection already exists, an Exception is raised. <- TODO: implement this part!

        :param collection_dbase_id: Internal database ID of an existing Collection
        :param item_dbase_id:       Internal database ID of an existing Data Node representing a "Collection Item"
        :param membership_rel_name: The name to give to the relationship
                                        between the "Collection Item" and the Collection node
        :return:                    None
        """

        # TODO: replicate this check to all functions??
        if cls.db is None:
            raise Exception("Collections.link_to_collection_at_end(): database not set")

        # ATOMIC database update that locates the next-available "pos" number, and creates a relationship using it
        q = f'''
            MATCH (collection) 
            WHERE id(collection) = $collection_dbase_id
            WITH collection
            OPTIONAL MATCH (old_ci) -[r :{membership_rel_name}]-> (collection)
            WITH r.pos AS pos, collection
            WITH 
                CASE WHEN pos IS NULL THEN
                    0
                ELSE
                    max(pos) + {cls.DELTA_POS}
                END AS new_pos, collection
            
            MATCH (new_ci)
            WHERE id(new_ci) = $item_dbase_id
            MERGE (new_ci)-[:{membership_rel_name} {{pos: new_pos}}]->(collection)
        '''
        #cls.db.debug_query_print(q, data_binding={"collection_dbase_id": collection_dbase_id, "item_dbase_id": item_dbase_id})

        status = cls.db.update_query(q,
                                     data_binding={"collection_dbase_id": collection_dbase_id, "item_dbase_id": item_dbase_id})
        #print("link_to_collection_at_end(): status is ", status)

        # status should be contain {'relationships_created': 1, 'properties_set': 1}

        assert status.get('relationships_created') == 1, \
            f"link_to_collection_at_end(): failed to create a new link " \
            f"to a Collection with internal database ID {collection_dbase_id}"

        assert status.get('properties_set') == 1, \
            f"link_to_collection_at_end(): failed to set the positional value to the new link " \
            f"to the Collection with internal database ID {collection_dbase_id}"



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
        #TODO:  the Data Node creation perhaps should be done ahead of time, and doesn't need to be the responsibility of this class!
        #TODO:  solve the concurrency issue - of multiple requests arriving almost simultaneously, and being handled by a non-atomic update,
        #       which can lead to incorrect values of the "pos" relationship attributes.
        #       -> Follow the new way it is handled in add_content_at_end()

        assert NeoSchema.is_valid_uri(collection_uri), "The argument `collection_uri` isn't a valid URI string"
        assert type(membership_rel_name) == str, "The argument `membership_rel_name` MUST be a string"
        assert type(item_class_name) == str, "The argument `item_class_name` MUST be a string"
        assert type(item_properties) == dict, "The argument `item_properties` MUST be a dictionary"

        # TODO: this query and the one in add_data_point(), below, ought to be combined, to avoid concurrency problems
        q = f'''
            MATCH (n:BA) - [r :{membership_rel_name}] -> (c:BA {{uri: $collection_id}}) 
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
        #       -> Follow the new way it is handled in add_content_at_end()

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
            node = NeoSchema.fetch_data_node(uri = insert_after)
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
