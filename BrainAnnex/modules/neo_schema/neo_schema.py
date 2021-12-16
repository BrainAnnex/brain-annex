from BrainAnnex.modules.neo_access import neo_access


class NeoSchema:
    """
    A layer above the class NeoAccess (or, in principle, another library providing a compatible interface)
    to provide an optional schema to the underlying database.

    Schemas may be used to either:
        1) acknowledge the existence of typical patterns in the data
        OR
        2) to enforce a mold for the data to conform to

    MOTIVATION

        Relational databases are suffocatingly strict for the real world.
        Neo4j by itself may be too anarchic.
        A schema (whether "lenient/lax/loose" or "strict") in conjunction with Neo4j may be the needed compromise.

    GOAL

        To infuse into Neo4j functionality that some people turn to RDF for.  However, carving out a new path
        rather than attempting to emulate RDF!


    OVERVIEW

        - "Class" nodes capture the abstraction of entities that share similarities.
          Example: "car", "star", "protein", "patient"

          In RDFS lingo, a "Class" node is the counterpart of a resource (entity)
                whose "rdf:type" property has the value "rdfs:Class"

        - The "Property" nodes linked to a given "Class" node, represent the attributes of the data points of that class

        - Data nodes are linked to their respective classes by a "SCHEMA" relationship.

        - Some classes contain an attribute named "schema_code" that identifies the UI code to display/edit them,
          as well as their descendants under the "INSTANCE_OF" relationships.
          Conceptually, the "schema_code" is a relationship to an entity consisting of software code.


    IMPLEMENTATION DETAILS

        - Every node used by this class has a unique attribute "schema_id",
          containing a non-negative integer.
          Similarly, data nodes have a separate unique attribute "item_id"

        - The names of the Classes and Properties are stored in node attributes called "name".
          We also avoid calling them "label", as done in RDFS, because in Labeled Graph Databases
          like Neo4j, the term "label" has a very specific meaning, and is pervasively used.

        - For convenience, data nodes contain a redundant attribute named "schema_code"


    AUTHOR:
        Julian West


    ----------------------------------------------------------------------------------
	MIT License

        Copyright (c) 2021 Julian A. West

        This file is part of the "Brain Annex" project (https://BrainAnnex.org)

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
	----------------------------------------------------------------------------------
    """

    db = neo_access.NeoAccess()         # Saving database-interface object as a CLASS variable, accessible as cls.db
                                        # This will only be executed once

    class_label = "CLASS"               # Neo4j label to be used with Class nodes managed by this class;
                                        #       change it, if you have conflicts with other modules
                                        #       Alt. name ideas: "SCHEMA"

    property_label = "PROPERTY"         # Neo4j label to be used with Property nodes managed by this class

    class_prop_rel = "HAS_PROPERTY"     # The name to use for the relationships from `Class` to `Property` nodes

    data_class_rel = "SCHEMA"           # The name to use for the relationships from data nodes to `Property` nodes
                                        #       Alt. name ideas: "IS", "HAS_CLASS", "HAS_SCHEMA", "TYPE", "TYPE_OF"




    ##################################################################################################
    #                                                                                                #
    #                                       CLASS-related                                            #
    #                                                                                                #
    ##################################################################################################

    @classmethod
    def create_class(cls, name: str, code=None, schema_type="L", no_datanodes = False) -> int:
        """
        Create a new Class node with the given name and type of schema,
        provided that the name isn't already in use for another Class.
        Return the auto-incremented unique ID assigned to the new Class,
        or -1 (which is not regarded as a valid schema ID) if nothing is created.

        TODO: offer the option to link to an existing Class.  link_to=None, link_name="INSTANCE_OF", link_dir="OUT"
        TODO: maybe an option to add multiple Classes of the same type at once???

        :param name:        Name to give to the new Class
        :param code:        Optional string indicative of the software handler for this Class and its subclasses
        :param schema_type: Either "L" (Lenient) or "S" (Strict).  Explained under the class-wide comments
        :param no_datanodes If True, it means that this Class does not allow data node to have a "SCHEMA" relationship to it;
                                typically used by Classes having an intermediate role in the context of other Classes.
        :return:            An integer with the unique schema_id assigned to the node just created, if it was created,
                                or -1 if nothing was created
        """
        assert schema_type=="L" or schema_type=="S", "schema_type argument must be either 'L' or 'S'"

        name = name.strip()     # Strip any whitespace at the ends
        assert name != "", "Unacceptable Class name, either empty or blank"

        if cls.db.exists_by_key(cls.class_label, key_name="name", key_value=name):
            return -1

        schema_id = cls.next_available_id()    # A schema-wide ID, also used for Property nodes

        attributes = {"name": name, "schema_id": schema_id, "type": schema_type}
        if code:
            attributes["code"] = code
        if no_datanodes:
            attributes["no_datanodes"] = True       # TODO: test this option

        cls.db.create_node(cls.class_label, attributes)
        return schema_id



    @classmethod
    def get_class_id(cls, class_name: str) -> int:
        """
        Returns the Schema ID of the Class with the given name, or -1 if not found

        :param class_name:  The name of the desired class
        :return:            The Schema ID of the specified Class, or -1 if not found
        """
        match = cls.db.find(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.fetch_nodes(match, single_cell="schema_id")

        if not result:
            return -1

        return result



    @classmethod
    def get_class_name(cls, schema_id: int) -> str:
        """
        Returns the name of the class with the given Schema ID, or "" if not found

        :param schema_id:   An integer with the unique ID of the desired class
        :return:            The name of the class with the given Schema ID, or "" if not found
        """
        assert type(schema_id) == int, "The schema id MUST be an integer"

        match = cls.db.find(labels="CLASS", key_name="schema_id", key_value=schema_id)
        result = cls.db.fetch_nodes(match, single_cell="name")

        if not result :
            return ""

        return result



    @classmethod
    def get_all_classes(cls, only_names=True):
        """
        Fetch and return a list of all existing classes - either just their names (sorted alphabetically),
        or a fuller listing (TODO: not yet implemented)
        :return:
        """
        return cls.db.get_single_field("name", labels = cls.class_label, order_by="name")



    @classmethod
    def create_class_relationship(cls, child: int, parent: int, rel_name ="INSTANCE_OF") -> bool:
        """
        Create a relationship (provided that it doesn't already exist) with the specified name
        between the 2 given Class nodes (identified by their schema_id),
        going in the direction FROM "child" node TO the "parent" one.
        TODO: add a method that reports on all existing relationships among Classes?
        TODO: allow to alternatively specify the child and parent by name

        :param child:       schema_id of the child Class
        :param parent:      schema_id of the parent Class
        :param rel_name:    Name of the relationship to create FROM the child TO the parent class
        :return:            True if a relationship was created, or False if not
        """
        q = f'''
            MATCH (c:CLASS {{schema_id: $child}}), (p:CLASS {{schema_id: $parent}})
            MERGE (c)-[:{rel_name}]-(p)
            '''

        result = cls.db.update_query(q, {"child": child, "parent": parent})
        #print("result of update_query in create_subclass_relationship(): ", result)
        if result.get("relationships_created") == 1:
            return True
        else:
            return False



    @classmethod
    def rename_class_rel(cls, from_class: int, to_class: int, new_rel_name) -> bool:
        """
        Rename the old relationship between the specified classes

        :param from_class:
        :param to_class:
        :param new_rel_name:
        :return:            True if another relationship was found, and successfully renamed;
                            otherwise, False
        """
        q = f'''
            MATCH (from :`{cls.class_label}` {{ schema_id: {from_class} }})
                  -[rel]
                  ->(to :`{cls.class_label}` {{ schema_id: {to_class} }})
            MERGE (from)-[:{new_rel_name}]->(to)
            DELETE rel 
            '''
        # EXAMPLE:
        '''
            MATCH (from :`CLASS` { schema_id: 4 })
                  -[rel]
                  ->(to :`CLASS` { schema_id: 19 })
            MERGE (from)-[:INSTANCE_OF]->(to)
            DELETE rel
        '''
        #print(q)
        result = cls.db.update_query(q)
        print("result of rename_class_rel in remove_property_from_class(): ", result)
        if (result.get("relationships_deleted") == 1) and (result.get("relationships_created") == 1):
            return True
        else:
            return False



    @classmethod
    def unlink_classes(cls, class1: int, class2: int) -> bool:
        """
        Remove all relationships (in any direction) between the specified classes

        :param class1:
        :param class2:
        :return:        True if a relationship (in either direction) was found, and successfully removed;
                        otherwise, False
        """
        q = f'''
            MATCH (c1: `{cls.class_label}` {{ schema_id: {class1} }})
                  -[r]
                  -(c2: `{cls.class_label}` {{ schema_id: {class2} }})
            DELETE r
            '''
        # EXAMPLE:
        '''
        MATCH (c1: `CLASS` { schema_id: 1 })
              -[r]
              -(c2: `CLASS` { schema_id: 15})
        DELETE r
        '''
        #print(q)

        result = cls.db.update_query(q)
        #print("result of unlink_classes in remove_property_from_class(): ", result)
        if result.get("relationships_deleted") == 1:
            return True
        else:
            return False



    @classmethod
    def delete_class(cls, class_name = "", schema_id:int = None) -> None:
        """
        Delete the given Class (specified by its name or schema_id) AND all its attached Properties -
        but ONLY if there are no data nodes of that Class (i.e., linked to it.)

        :param class_name:  Name of the Class to delete
        :param schema_id:
        :return:
        """
        pass    # TODO: implement



    @classmethod
    def allows_datanodes(cls, class_name: str) -> bool:
        """
        Determine if the given Class allows data nodes directly linked to it

        :param class_name:  Name of the Class
        :return:            True if allowed, or False if not
                            If the Class doesn't exist, raise an Exception
        """
        class_node_dict = cls.db.get_single_record_by_key(labels="CLASS", key_name="name", key_value=class_name)

        if class_node_dict == None:
            raise Exception(f"Class named {class_name} not found in the Schema")

        if "no_datanodes" in class_node_dict:
            return not class_node_dict["no_datanodes"]

        return True    # If key is not in dictionary, then it defaults to True



    @classmethod
    def get_class_instances(cls, class_name: str, leaf_only=False) -> [str]:
        """
        Get the names of all Classes that are, directly or indirectly, instances of the given Class,
        i.e. pointing to that node thru a series of 1 or more "INSTANCE_OF" relationships;
        if leaf_only is True, then only as long as they are leaf nodes (with no other Class
        that is an instance of them.)

        :param class_name:  Name of the Class for which we want to find
                            other Classes that are an instance of it
        :param leaf_only:   If True, only return the leaf nodes (those that
                            don't have other Classes that are instances of them)
        :return:            A list of Class names
        """
        if leaf_only:
            q = '''
                MATCH (leaf :CLASS)-[:INSTANCE_OF*1..]->(r :CLASS {name: $class_name})
                WHERE not exists( (:CLASS)-[:INSTANCE_OF]->(leaf) )
                RETURN leaf.name AS NAME
                ORDER BY NAME
                '''
        else:
            q = '''
                MATCH (c :CLASS)-[:INSTANCE_OF*1..]->(r :CLASS {name: $class_name})
                RETURN c.name AS NAME
                ORDER BY NAME
                '''

        return cls.db.query(q, data_binding={"class_name": class_name}, single_column="NAME")




    ###################################################
    #                PROPERTIES-RELATED               #
    ###################################################

    @classmethod
    def get_class_properties(cls, schema_id: int, include_ancestors=False) -> list:
        """
        Return the list of all the names of the Properties associated with the given Class
        (including those inherited thru ancestor nodes, if include_ancestors is True),
        sorted by schema-specified position.

        :param schema_id:           Integer with the ID of a Class node
        :param include_ancestors:   If True, also include the Properties attached to Classes that are ancestral
                                    to the given one by means of a chain of outbound "INSTANCE_OF" relationships
                                    Note: the sorting by relationship index won't mean much if ancestral nodes are included,
                                          with their own indexing of relationships  TODO: maybe also sort by path length??
        :return:                    A list of the Properties of the specified Class (including indirectly, if include_ancestors is True)
        """
        if include_ancestors:
            # Follow zero or more outbound "INSTANCE_OF" relationships from the given Class node;
            #   "zero" relationships means the original node itself (handy in situations when there are no such relationships)
            q = '''
                MATCH (c :CLASS {schema_id: $schema_id})-[:INSTANCE_OF*0..]->(c_ancestor)
                      -[r:HAS_PROPERTY]->(p :PROPERTY) 
                RETURN p.name AS prop_name
                ORDER BY r.index
                '''
        else:
            q = '''
                MATCH (c :CLASS {schema_id: $schema_id})-[r :HAS_PROPERTY]->(p :PROPERTY)
                RETURN p.name AS prop_name
                ORDER BY r.index
                '''

        result_list = cls.db.query(q, {"schema_id": schema_id})

        name_list = [item["prop_name"] for item in result_list]

        return name_list



    @classmethod
    def add_properties_to_class(cls, class_id: int, property_list: [str]) -> int:
        """
        Add a list of Properties to the specified (ALREADY-existing) Class.
        The properties are assigned an inherent order (an attribute named "index", starting at 1),
        based on the order they appear in the list.
        NOTE: if the Class doesn't already exist, use new_class_with_properties() instead
        TODO: raise an Exception if the class doesn't exit.
              Asser that all the items in property_list are strings.
              Offer option to specify the class by name.

        :param class_id:        Integer with the schema_id of the Class to which attach the given Properties
        :param property_list:   A list of strings with the names of the properties, in the desired default order
                                    Whitespace in any of the names gets stripped out.  If any name is a blank string, an Exception is raised
        :return:                The number of Properties added (might be zero if the Class doesn't exist)
        """

        assert type(class_id) == int, "Argument `class_id` in add_properties_to_class() must be an integer"
        assert type(property_list) == list, "Argument `property_list` in add_properties_to_class() must be a list"


        clean_property_list = [prop.strip() for prop in property_list]
        for prop_name in clean_property_list:
            assert prop_name != "", "Unacceptable Property name, either empty or blank"

        # Locate the largest index of the Properties currently present
        q = '''
            MATCH (:CLASS {schema_id: $schema_id})-[r:HAS_PROPERTY]-(:PROPERTY)
            RETURN MAX(r.index) AS MAX_INDEX
            '''
        max_index = cls.db.query(q, {"schema_id": class_id}, single_cell="MAX_INDEX")

        # Determine the index value to use for the next Property
        if max_index is None:
            new_index = 1               # Start a new Property count
        else:
            new_index = max_index + 1   # Continue an existing Property count

        number_properties_nodes_created = 0

        for property_name in clean_property_list:
            new_schema_id = cls.next_available_id()
            q = f'''
                MATCH (c: `{cls.class_label}` {{ schema_id: {class_id} }})
                MERGE (c)-[:{cls.class_prop_rel} {{ index: {new_index} }}]
                         ->(p: `{cls.property_label}` {{ schema_id: {new_schema_id}, name: $property_name }})
                '''
            # EXAMPLE:
            '''
            MATCH (c:`CLASS` {schema_id: 3})
            MERGE (c)-[:HAS_PROPERTY {index: 1}]->(p: `PROPERTY` {schema_id: 8, name: $property_name})
            '''
            #print(q)
            result = cls.db.update_query(q, {"property_name": property_name})
            number_properties_nodes_created += result.get("nodes_created")
            new_index += 1

        return number_properties_nodes_created



    @classmethod
    def new_class_with_properties(cls, class_name: str, property_list: [str], code=None, schema_type="L",
                                  class_to_link_to=None, link_to_name="INSTANCE_OF") -> int:
        """
        Create a new Class with the specified name and properties,
        and return the auto-incremented unique ID ("scheme ID") assigned to the new Class.
        Each Property node is also assigned a unique "scheme ID";
        the links are assigned an auto-increment index, representing the default order of the Properties.

        If a Class with the given name already exists, nothing is done,
        and -1 (not a valid schema ID) is returned.

        NOTE: if the Class already exists, use add_properties_to_class() instead

        :param class_name:      String with name to assign to the new class
        :param property_list:   List of strings with the names of the Properties, in their default order (if that matters)
        :param code:            Optional string indicative of the software handler for this Class and its subclasses
        :param schema_type      Either "L" (Lenient) or "S" (Strict).  Explained under the class-wide comments
        :param class_to_link_to If this name is specified, and a link_to_name (below) is also specified,
                                    then create a relationship from the newly-created Class to this existing one
        :param link_to_name     Name to use for the above relationship.  Default is "INSTANCE_OF"

        :return:                If successful, the integer "schema_id" assigned to the new Class; otherwise, -1
        """
        #TODO: it might be safer to use fewer Cypher transactions

        new_class_id = cls.create_class(class_name, code=code, schema_type=schema_type)
        if cls.valid_schema_id(new_class_id):
            number_properties_added = cls.add_properties_to_class(new_class_id, property_list)
            print("new_class_with_properties().  number_properties_added: ", number_properties_added)

        if class_to_link_to and link_to_name:
            # Create a relationship from the newly-created Class to an existing Class whose name is given by class_to_link_to
            parent_id = NeoSchema.get_class_id(class_name = class_to_link_to)
            print(f"parent_id (ID of `{class_to_link_to}` class): ", parent_id)
            status = NeoSchema.create_class_relationship(child=new_class_id, parent=parent_id, rel_name =link_to_name)
            assert status, f"New Class ({class_name}) created successfully, but unable to link it to the `{class_to_link_to}` class"

        return new_class_id



    @classmethod
    def remove_property_from_class(cls, class_id: int, property_id: int) -> bool:
        """
        Take out the specified Property from the given Class

        :param class_id:    The schema ID of the Class node
        :param property_id: The schema ID of the Property node
        :return:            True if a Property was found, and successfully removed; otherwise, False
        """
        q = f'''
            MATCH (c: `{cls.class_label}` {{ schema_id: {class_id} }})
                  -[r:{cls.class_prop_rel}]
                  ->(p: `{cls.property_label}` {{ schema_id: {property_id}}})
            DELETE r
            '''
        # EXAMPLE:
        '''
        MATCH (c: `CLASS` { schema_id: 4 })
              -[r:HAS_PROPERTY]
              ->(p: `PROPERTY` { schema_id: 13})
        DELETE r
        '''

        result = cls.db.update_query(q)
        #print("result of update_query in remove_property_from_class(): ", result)
        if result.get("relationships_deleted") == 1:
            return True
        else:
            return False




    #############   SCHEMA-CODE  RELATED   ###########

    @classmethod
    def get_schema_code(cls, class_name: str) -> str:
        """
        Obtain the schema code of a Class, specified by its name

        :return:    A string with the Schema code (empty string if not present)
        """
        q = '''
        MATCH (c:CLASS {name: $_CLASS_NAME})-[:INSTANCE_OF*0..]->(ancestor:CLASS)
        WHERE ancestor.code IS NOT NULL 
        RETURN ancestor.code AS code
        '''
        # Search 0 or more hops from the given Class node

        result = cls.db.query(q, {"_CLASS_NAME": class_name})
        if result == []:
            return ""

        return result[0]["code"]



    @classmethod
    def get_schema_id(cls, schema_code: str) -> int:
        """
        Get the Schema ID most directly associated to the given Schema Code

        :return:    An integer with the Schema ID (or -1 if not present)
        """

        result = cls.db.get_nodes("CLASS", properties_condition={"code": schema_code})

        if result == []:
            return -1

        return result[0].get("schema_id")




    ########################################################
    #                       DATA POINTS                    #
    ########################################################

    @classmethod
    def all_properties(cls, label, primary_key_name, primary_key_value) -> list:
        """
        Return the list of all the names of the Properties associated with the given DATA node,
        based on the Schema it is associated with, sorted by schema-specified position.
        The desired node is identified by specifying which one of its attributes is a primary key,
        and providing a value for it
        """
        q = f'''
            MATCH  (d :`{label}` {{ {primary_key_name}: $primary_key_value}})
                  -[:{cls.data_class_rel}]->(c :`{cls.class_label}`)
                  -[r :{cls.class_prop_rel}]->(p :`{cls.property_label}`)        
            RETURN p.name AS prop_name
            ORDER BY r.index
            '''

        # EXAMPLE:
        '''
        MATCH (d: `my data label` {item_id: $primary_key_value})
              -[:SCHEMA]->(c :`CLASS`)
              -[r :HAS_PROPERTY]->(p :`PROPERTY`)
        RETURN p.name AS prop_name
        ORDER BY r.index
        '''

        result_list = cls.db.query(q, {"primary_key_value": primary_key_value})

        name_list = [item["prop_name"] for item in result_list]

        return name_list



    @classmethod
    def fetch_data_point(cls, item_id: int, labels=None, properties=None) -> dict:
        """
        Return a dictionary with all the key/value pairs of the given data point
        TODO: test

        :param item_id:
        :param labels:      OPTIONAL (generally, redundant)
        :param properties:  OPTIONAL (generally, redundant)
        :return:            A dictionary with all the key/value pairs, if found; or {} if not
        """
        match = cls.db.find(key_name="item_id", key_value=item_id,
                            labels=labels, properties=properties)
        return cls.db.fetch_nodes(match, single_row=True)



    @classmethod
    def add_data_point(cls, class_name="", schema_id=None,
                       data_dict=None, labels=None,
                       connected_to_id=None, connected_to_labels=None, rel_name=None, rel_dir="OUT", rel_prop_key=None, rel_prop_value=None,
                       new_item_id=None) -> int:
        """
        Add a new data node, of the Class specified by name or ID,
        optionally linked to another, already existing, data node.
        The new data node, if successfully created, will be assigned a unique value for its field item_id

        EXAMPLES:   add_data_point(class_name="Cars", {"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     {"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with item_id = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails
        :param data_dict:       A dictionary with the properties of the new data point.  EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to new data node; if not specified, use the Class name

        :param connected_to_id: Int or None.  To optionally specify a data node to connect the new node to
                                        EXAMPLE: the item_id of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param connected_to_labels:     EXAMPLE: "salesperson"
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                If successful, an integer with auto-increment "item_id" value of the node just created;
                                otherwise, an Exception is raised
        """
        #print(f"In add_data_point().  rel_name: `{rel_name}` | rel_prop_key: `{rel_prop_key}` | rel_prop_value: {rel_prop_value}")

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name(schema_id)      # Derive the Class name from its ID

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        assert type(data_dict) == dict, "The data_dict argument MUST be a dictionary"

        cypher_props_dict = data_dict

        if not cls.allows_datanodes(class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes contain 2 special attributes: "item_id" and "schema_code";
        # expand cypher_props_dict accordingly
        if not new_item_id:
            new_id = cls.next_available_datapoint_id()
        else:
            new_id = new_item_id
        #print("New ID assigned to new data node: ", new_id)
        cypher_props_dict["item_id"] = new_id               # Expand the dictionary

        schema_code = cls.get_schema_code(class_name)
        if schema_code != "":
            cypher_props_dict["schema_code"] = schema_code  # Expand the dictionary

        # EXAMPLE of cypher_props_dict at this stage:
        #       {"make": "Toyota", "color": "white", "item_id": 123, "schema_code": "r"}
        #       where 123 is the next auto-assigned item_id

        # Create a new data node, with a "SCHEMA" relationship to its Class node and, if requested, also a relationship to another data node
        if connected_to_id:     # if requesting a relationship to an existing data node
            if rel_prop_key and (rel_prop_value != '' and rel_prop_value is not None):  # Note: cannot just say "and rel_prop_value" or it'll get dropped if zero
                rel_attrs = {rel_prop_key: rel_prop_value}
            else:
                rel_attrs = None

            cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"},

                                                               {"labels": connected_to_labels, "key": "item_id", "value": connected_to_id,
                                                                "rel_name": rel_name, "rel_dir": rel_dir, "rel_attrs": rel_attrs}
                                                               ]
                                                  )
        else:   # simpler case
            cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"}]
                                                  )

        return new_id



    @classmethod
    def add_existing_data_point(cls, class_name="", schema_id=None,
                                existing_neo_id=None, new_item_id=None) -> int:
        """
        Register an existing data node with the Schema Class specified by its name or ID.
        An item_id is generated for the data node and stored on it; likewise, for a schema_code (if applicable).
        Return the newly-assigned item_id

        EXAMPLES:   add_existing_data_point(class_name="Chemicals", existing_neo_id=123)
                    add_existing_data_point(schema_id=19, existing_neo_id=456)

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param existing_neo_id: Internal ID to identify the node to register with the above Class.
                                TODO: expand to use the find() structure
        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)

        :return:                If successful, an integer with the auto-increment "item_id" value of the node just created;
                                otherwise, an Exception is raised
        """
        if not existing_neo_id:
            raise Exception("Missing argument: existing_neo_id")

        assert type(existing_neo_id) == int, "The argument `existing_neo_id` MUST be an integer"

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name(schema_id)      # Derive the Class name from its ID
            if not class_name:
                raise Exception(f"Unable to locate a Class with schema ID {schema_id}")

        if not cls.allows_datanodes(class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Verify that the data point doesn't already have a SCHEMA relationship
        q = f'''
            MATCH (n)-[:SCHEMA]->(:CLASS) WHERE id(n)={existing_neo_id} RETURN count(n) AS number_found
            '''
        number_found = cls.db.query(q, single_cell="number_found")
        if number_found:
            raise Exception(f"The given data node ALREADY has a SCHEMA relationship")

        if not new_item_id:
            new_item_id = cls.next_available_datapoint_id()     # Generate, if not already provided

        print("add_existing_data_point(). New item_id to be assigned to the data node: ", new_item_id)

        data_binding = {"class_name": class_name, "new_item_id": new_item_id, "existing_neo_id": existing_neo_id}

        schema_code = cls.get_schema_code(class_name)
        if schema_code != "":
            data_binding["schema_code"] = schema_code   # Expand the dictionary

        # EXAMPLE of data_binding at this stage:
        #       {'class_name': 'Chemicals', 'new_item_id': 888, 'existing_neo_id': 123, 'schema_code': 'r'}
        #       where 888 is the next auto-assigned item_id

        # Link the existing data node, with a "SCHEMA" relationship, to its Class node, and also set some properties on the data node
        q = f'''
            MATCH (existing), (class :CLASS {{name: $class_name}}) WHERE id(existing) = $existing_neo_id
            MERGE (existing)-[:SCHEMA]->(class)
            SET existing.item_id = $new_item_id
            '''
        if schema_code != "":
            q += " , existing.schema_code = $schema_code"

        cls.db.debug_print(q, data_binding, "add_existing_data_point")
        result = cls.db.update_query(q, data_binding)
        #print(result)

        number_new_rels = result.get('relationships_created')   # This ought to be 1
        if number_new_rels != 1:
            raise Exception("Failed to created the new relationship (`SCHEMA`)")

        return new_item_id



    @classmethod
    def delete_data_point(cls, item_id: int, labels=None) -> int:
        """
        Delete the given data point
        TODO: test

        :param item_id:
        :param labels:      OPTIONAL (generally, redundant)
        :return:            The number of nodes deleted (possibly zero)
        """
        match = cls.db.find(key_name="item_id", key_value=item_id, properties={"schema_code": "cat"},
                            labels=labels)
        return cls.db.delete_nodes(match)



    @classmethod
    def add_data_relationship(cls, from_id: int, to_id: int, rel_name: str, rel_props = None, labels=None) -> bool:
        """
        Add a new relationship between 2 data nodes, from the "parent" to the "child".
        Return True if the requested new relationship got successfully created, or False otherwise.
        Note that if a relationship with the same name already exists, nothing gets created (and False is returned)

        :param from_id:     The "item_id" value of the data node at which the new relationship is to originate
        :param to_id:       The "item_id" value of the data node at which the new relationship is to end
        :param rel_name:    The name to give to the new relationship between the 2 specified data nodes
        :param rel_props:   TODO: not currently used.  Unclear what multiple calls would do in this case
        :param labels:      OPTIONAL (generally, redundant)
        :return:            True if the requested new relationship got successfully created, or False otherwise
                            In case the Schema forbids the new relationship, raise an Exception
                            TODO: maybe raise Exceptions (of different custom types?) in the case of any failure
        """

        # Verify that the relationship exists in the schema, i.e. that the Classes of the data nodes have a relationship with that name between them

        labels_str = cls.db.prepare_labels(labels)
        # Attempt to find a path from the "from" data node, to its Class in the schema, to another Class along a relationship
        #   with the same name as the one we're trying to add, and finally to the "to" data node that has that last Class as schema
        q = f'''
        MATCH p=(from {labels_str} {{item_id: $from_id}})-[:SCHEMA]-> 
        (from_class :CLASS)-[:{rel_name}]->(to_class :CLASS) 
        <-[:SCHEMA]- (to {labels_str} {{item_id: $to_id}})
        RETURN p
        '''

        data_binding = {"from_id": from_id, "to_id": to_id}
        path = cls.db.query(q, data_binding)
        if path == []:
            raise Exception(f"Cannot add the relationship `{rel_name}` between the data nodes, because no such relationship exists between their Classes")


        # Add the new relationship
        match_from = cls.db.find(labels=labels, key_name="item_id", key_value=from_id,
                                 dummy_node_name="from")

        match_to =   cls.db.find(labels=labels, key_name="item_id", key_value=to_id,
                                 dummy_node_name="to")

        return cls.db.add_edge(match_from, match_to, rel_name=rel_name)



    @classmethod
    def remove_data_relationship(cls, from_id: int, to_id: int, rel_name: str, labels=None):
        """
        Drop the specified relationship between the 2 given data nodes, from the "parent" to the "child".
        Note: the data nodes are left untouched.

        TODO: verify that the relationship is optional in the schema

        :param from_id:     The "item_id" value of the data node at which the relationship originates
        :param to_id:       The "item_id" value of the data node at which the relationship ends
        :param rel_name:    The name of the relationship to delete
        :param labels:      OPTIONAL (generally, redundant)
        :return:            True if the specified relationship got successfully deleted, or False otherwise
        """
        match_from = cls.db.find(labels=labels, key_name="item_id", key_value=from_id,
                                 dummy_node_name="from")

        match_to =   cls.db.find(labels=labels, key_name="item_id", key_value=to_id,
                                 dummy_node_name="to")

        return cls.db.remove_edge(match_from, match_to, rel_name=rel_name)




    ########################################################
    #                    EXPORT SCHEMA                     #
    ########################################################

    @classmethod
    def export_schema(cls) -> {}:      # TODO: unit testing
        """
        Export all the Schema nodes and relationships as a JSON string.

        :return:    A dictionary specifying the number of nodes exported,
                    the number of relationships, and the number of properties,
                    as well as a "data" field with the actual export as a JSON string
        """
        # Any Class or Property node
        nodes_query = "MATCH (n) WHERE (n:CLASS OR n:PROPERTY)"

        # Any relationship from a Class to another Class or to a Property
        rels_query = "MATCH (c:CLASS)-[r]->(n) WHERE (n:CLASS OR n:PROPERTY)"

        return cls.db.export_nodes_rels_json(nodes_query, rels_query)




    ###############   INTERNAL  METHODS   ###############

    @classmethod
    def valid_schema_id(cls, schema_id: int) -> bool:
        """
        Check the validity of the passed Schema ID

        :param schema_id:
        :return:
        """
        if schema_id >= 0:
            return True
        else:
            return False



    @classmethod
    def next_available_id(cls) -> int:
        """
        Return the next available ID for nodes managed by this class
        For the ID to use on data points, use next_available_datapoint_id() instead
        # TODO: *** THIS MAY FAIL IF MULTIPLE CALLS ARRIVE ALMOST SIMULTANEOUSLY

        :return:
        """
        return cls.next_available_id_general([cls.class_label, cls.property_label], "schema_id")


    @classmethod
    def next_available_datapoint_id(cls) -> int:
        # TODO: *** THIS MAY FAIL IF MULTIPLE CALLS ARRIVE ALMOST SIMULTANEOUSLY
        new_id = cls.next_available_id_general("BA", "item_id")
        # TODO: Save the above result (only produced if no class-variable value is available) as a class variable.
        return new_id


    @classmethod
    def next_available_id_general(cls, labels, attr_name: str) -> int:    # TODO: this belongs to NeoAccess
        """
        Return the next available value of the specified attribute, treated as an Auto-Increment value, for all nodes
        with the given label.
        If a list of labels is given, match ANY of them.
        If no matches are found, return 1 (arbitrarily used as the first Auto-Increment value.)

        :param labels:  Either a string or a list of strings
        :param attr_name:
        :return:    An integer with the next available ID
        """

        if type(labels) == str:
            label_list = [labels]
        else:
            label_list = labels

        where_clause = "WHERE n:`" + "` OR n:`".join(label_list) + "`"
        # EXAMPLE:  "WHERE n:`CLASS` OR n:`PROPERTY`"
        # See https://github.com/neo4j/neo4j/issues/5002
        #       and https://stackoverflow.com/questions/20003769/neo4j-match-multiple-labels-2-or-more

        cypher = f"MATCH (n) {where_clause} RETURN 1+max(n.`{attr_name}`) AS next_value"
        #print("\n", cypher)

        result_list = cls.db.query(cypher)
        # Note: if no node was matched in the query, the result of the 1+max will be None
        #print(result_list)
        result = result_list[0]["next_value"]        # Extract the single element from the list, and then get the "next_value" field
        #print("Next available ID: ", result)

        if result is None:
            return 1        # Arbitrarily use 1 as the first Auto-Increment value, if no other value is present

        return result
