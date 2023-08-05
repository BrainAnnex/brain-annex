from typing import Union, List
from neoaccess.cypher_utils import CypherUtils, CypherMatch
import json


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


    SECTIONS IN THIS CLASS:
        * CLASS-related
            - RELATIONSHIPS AMONG CLASSES
        * PROPERTIES-RELATED
        * SCHEMA-CODE  RELATED
        * DATA NODES
        * DATA IMPORT
        * EXPORT SCHEMA
        * INTERNAL  METHODS



    OVERVIEW

        - "Class" nodes capture the abstraction of entities that share similarities.
          Example: "car", "star", "protein", "patient"

          In RDFS lingo, a "Class" node is the counterpart of a resource (entity)
                whose "rdf:type" property has the value "rdfs:Class"

        - The "Property" nodes linked to a given "Class" node, represent the attributes of the data nodes of that class

        - Data nodes are linked to their respective classes by a "SCHEMA" relationship.

        - Some classes contain an attribute named "schema_code" that identifies the UI code to display/edit them,
          as well as their descendants under the "INSTANCE_OF" relationships.
          Conceptually, the "schema_code" is a relationship to an entity consisting of software code.


    IMPLEMENTATION DETAILS

        - Every node used by this class has a unique attribute "schema_id",
          containing a non-negative integer.
          Similarly, data nodes have a separate unique attribute "item_id" (TODO: rename "uri" or "token")

        - The names of the Classes and Properties are stored in node attributes called "name".
          We also avoid calling them "label", as done in RDFS, because in Labeled Graph Databases
          like Neo4j, the term "label" has a very specific meaning, and is pervasively used.

        - For convenience, data nodes contain a redundant attribute named "schema_code"


    AUTHOR:
        Julian West


    ----------------------------------------------------------------------------------
	MIT License

        Copyright (c) 2021-2023 Julian A. West

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

    db = None           # MUST be set before using this class!
                        # Database-interface object is a CLASS variable, accessible as cls.db
                        # For use with the NeoAccess library


    class_label = "CLASS"               # Neo4j label to be used with Class nodes managed by this class;
                                        # TODO: maybe double label it with "SCHEMA", in part to avoid potential conflicts with other modules

    property_label = "PROPERTY"         # Neo4j label to be used with Property nodes managed by this class

    class_prop_rel = "HAS_PROPERTY"     # The name to use for the relationships from `Class` to `Property` nodes

    data_class_rel = "SCHEMA"           # The name to use for the relationships from data nodes to `Property` nodes
                                        #       Alt. name ideas: "IS", "HAS_CLASS", "HAS_SCHEMA", "TYPE", "TYPE_OF"

    debug = False                       # Flag indicating whether a debug mode is to be used by all methods of this class



    @classmethod
    def set_database(cls, db) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, to be used with the NeoAccess library
        :return:    None
        """
        cls.db = db     # TODO: perform some validation




    #####################################################################################################
    #                                                                                                   #
    #                                   ~ CLASS-related  ~                                              #
    #                                                                                                   #
    #####################################################################################################

    @classmethod
    def assert_valid_class_name(cls, class_name: str) -> None:
        """
        Raise an Exception if the passed argument is not a valid Class name

        :param class_name:
        :return:
        """
        assert type(class_name) == str, \
            f"NeoSchema.assert_valid_class_name(): The class name ({class_name}) must be a string (instead, it's of type {type(class_name)})"

        assert class_name != "", \
            "NeoSchema.assert_valid_class_name(): Class name cannot be an empty string"



    @classmethod
    def create_class(cls, name: str, code=None, strict= False, schema_type="L", no_datanodes = False) -> (int, int):
        """
        Create a new Class node with the given name and type of schema,
        provided that the name isn't already in use for another Class.

        Return a pair with the Neo4j ID of the new ID,
        and the auto-incremented unique ID assigned to the new Class.
        Raise an Exception if a class by that name already exists.

        NOTE: if you want to add Properties at the same time that you create a new Class,
              use the function create_class_with_properties() instead.

        TODO: offer the option to link to an existing Class, like create_class_with_properties() does
                  link_to=None, link_name="INSTANCE_OF", link_dir="OUT"
        TODO: maybe an option to add multiple Classes of the same type at once???
        TODO: maybe stop returning the schema_id ?

        :param name:        Name to give to the new Class
        :param code:        Optional string indicative of the software handler for this Class and its subclasses
        :param strict:      If True, the Class will be of the "S" (Strict) type;
                                otherwise, it'll be of the "L" (Lenient) type
        :param schema_type: Either "L" (Lenient) or "S" (Strict).  Explained under the class-wide comments
                            #TODO: phase out

        :param no_datanodes If True, it means that this Class does not allow data node to have a "SCHEMA" relationship to it;
                                typically used by Classes having an intermediate role in the context of other Classes

        :return:            A pair of integers with the Neo4j ID and the unique schema_id assigned to the node just created,
                                if it was created;
                                an Exception is raised if a class by that name already exists
        """
        if schema_type is not None:     # TODO: phase out this argument
            assert schema_type=="L" or schema_type=="S", "schema_type argument must be either 'L' or 'S'"

        if strict:
            schema_type="S"
        else:
            schema_type="L"

        name = name.strip()     # Strip any whitespace at the ends
        assert name != "", "NeoSchema.create_class(): Unacceptable Class name, either empty or blank"

        if cls.class_name_exists(name):
            raise Exception(f"A class named `{name}` ALREADY exists")

        schema_id = cls.next_available_schema_id()    # A schema-wide ID, also used for Property nodes

        attributes = {"name": name, "schema_id": schema_id, "type": schema_type}
        if code:
            attributes["code"] = code
        if no_datanodes:
            attributes["no_datanodes"] = True

        #print(f"create_class(): about to call db.create_node with parameters `{cls.class_label}` and `{attributes}`")
        neo_id = cls.db.create_node(cls.class_label, attributes)
        return (neo_id, schema_id)



    @classmethod
    def get_class_internal_id(cls, class_name: str) -> int:
        """
        Returns the Neo4j ID of the Class node with the given name,
        or raise an Exception if not found, or if more than one is found.
        Note: unique Class names are assumed.

        :param class_name:  The name of the desired class
        :return:            The Neo4j ID of the specified Class
        """
        cls.assert_valid_class_name(class_name)

        match = cls.db.match(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.get_nodes(match, return_internal_id=True)

        if not result:
            raise Exception(f"NeoSchema.get_class_internal_id(): no Class node named `{class_name}` was found")

        if len(result) > 1:
            raise Exception(f"NeoSchema.get_class_internal_id(): more than 1 Class node named `{class_name}` was found")

        return result[0]["internal_id"]



    @classmethod
    def get_class_id(cls, class_name: str, namespace=None) -> int:
        """
        Returns the Schema ID of the Class with the given name, or -1 if not found
        TODO: unique Class names are assumed.  Perhaps add an optional "namespace" attribute, to use in case
              multiple classes with the same name must be used
        TODO: maybe raise an Exception if more than one is found

        :param class_name:  The name of the desired class
        :param namespace:   EXPERIMENTAL - not yet in use
        :return:            The Schema ID of the specified Class, or -1 if not found
        """
        assert class_name is not None, "NeoSchema.get_class_id(): argument `class_name` cannot be None"
        assert type(class_name) == str, f"NeoSchema.get_class_id(): argument `class_name` must be a string (value passed was `{class_name}`)"
        assert class_name != "", "NeoSchema.get_class_id(): argument `class_name` cannot be an empty string"

        match = cls.db.match(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.get_nodes(match, single_cell="schema_id")

        if result is None:
            return -1

        return result



    @classmethod
    def get_class_id_by_neo_id(cls, internal_class_id: int) -> int:
        """
        Returns the Schema ID of the Class with the given internal database ID.

        :param internal_class_id:
        :return:            The Schema ID of the specified Class; raise an Exception if not found
        """

        result = cls.db.get_nodes(internal_class_id, single_cell="schema_id")

        if result is None:
            raise Exception(f"NeoSchema.get_class_id_by_neo_id(): no Class with internal id {internal_class_id} found")

        return result



    @classmethod
    def class_neo_id_exists(cls, neo_id: int) -> bool:
        """
        Return True if a Class by the given internal ID ID already exists, or False otherwise

        :param neo_id:
        :return:
        """
        cls.db.assert_valid_internal_id(neo_id)

        return cls.db.exists_by_internal_id(neo_id)



    @classmethod
    def class_id_exists(cls, schema_id: int) -> bool:
        """
        Return True if a Class by the given schema ID already exists, or False otherwise

        :param schema_id:
        :return:
        """
        assert type(schema_id) == int, \
            f"NeoSchema.class_id_exists(): argument `schema_id` must be an integer (value passed was `{schema_id}`)"

        return cls.db.exists_by_key(labels="CLASS", key_name="schema_id", key_value=schema_id)


    @classmethod
    def class_name_exists(cls, class_name: str) -> bool:
        """
        Return True if a Class by the given name already exists, or False otherwise

        :param class_name:  The name of the class of interest
        :return:            True if the Class already exists, or False otherwise
        """
        assert type(class_name) == str, \
            f"NeoSchema.class_name_exists(): argument `class_name` must be a string (value passed has type {type(class_name)})"

        return cls.db.exists_by_key(labels="CLASS", key_name="name", key_value=class_name)



    @classmethod
    def get_class_name(cls, schema_id: int) -> str:
        """
        Returns the name of the class with the given Schema ID, or "" if not found

        :param schema_id:   An integer with the unique ID of the desired class
        :return:            The name of the class with the given Schema ID, or "" if not found
        """
        assert type(schema_id) == int, "The schema id MUST be an integer"

        match = cls.db.match(labels="CLASS", key_name="schema_id", key_value=schema_id)
        result = cls.db.get_nodes(match, single_cell="name")

        if not result :
            return ""

        return result



    @classmethod
    def get_class_name_by_neo_id(cls, class_neo_id: int) -> str:
        """
        Returns the name of the class with the given Neo4j ID, or raise an Exception if not found

        :param class_neo_id:    An integer with the Neo4j ID of the desired class
        :return:                The name of the class with the given Schema ID;
                                    raise an Exception if not found
        """
        cls.db.assert_valid_internal_id(class_neo_id)

        result = cls.db.get_nodes(class_neo_id, single_cell="name")

        if not result :
            raise Exception(f"NeoSchema.get_class_name_by_neo_id(): no Class with a Neo4j ID of {class_neo_id} found")

        return result


    @classmethod
    def get_class_attributes(cls, class_internal_id: int) -> dict:
        """
        Returns all the attributes (incl. the name) of the Class node with the given internal database ID,
        or raise an Exception if the Class is not found.
        If no "name" attribute is found, an Exception is raised.

        :param class_internal_id:   An integer with the Neo4j ID of the desired class
        :return:                    A dictionary of attributed of the class with the given Schema ID;
                                        an Exception is raised if not found
                                        EXAMPLE:  {'name': 'MY CLASS', 'schema_id': 123, 'type': 'L'}
        """
        #cls.db.assert_valid_internal_id(class_internal_id)

        match = cls.db.match(labels="CLASS", internal_id=class_internal_id)
        result = cls.db.get_nodes(match, single_row=True)

        if not result :
            raise Exception(f"NeoSchema.get_class_attributes(): no Class with an internal database ID of {class_internal_id} found")

        if "name" not in result:
            raise Exception(f"get_class_attributes(): the expected attribute `name` wasn't found"
                            f" among the attributes of the Class node {class_internal_id}")

        return result



    @classmethod
    def get_all_classes(cls, only_names=True) -> [str]:
        """
        Fetch and return a list of all the existing Schema classes - either just their names (sorted alphabetically)
        (TODO: or a fuller listing - not yet implemented)

        TODO: disregard capitalization is sorting

        :return:    A list of all the existing Class names
        """
        match = cls.db.match(labels=cls.class_label)
        return cls.db.get_single_field(match=match, field_name="name", order_by="name")



    @classmethod
    def delete_class(cls, name: str, safe_delete=True) -> None:
        """
        Delete the given Class AND all its attached Properties.
        If safe_delete is True (recommended) delete ONLY if there are no data nodes of that Class
        (i.e., linked to it by way of "SCHEMA" relationships.)

        :param name:        Name of the Class to delete
        :param safe_delete: Flag indicating whether the deletion is to be restricted to
                            situations where no data node would be left "orphaned".
                            CAUTION: if safe_delete is False,
                                     then data nodes may be left without a Schema
        :return:            None.  In case of no node deletion, an Exception is raised
        """
        if safe_delete:     # A clause is added in this branch: "WHERE NOT EXISTS (()-[:SCHEMA]->(c))"
            q = '''
            MATCH (c :CLASS {name: $name})
            WHERE NOT EXISTS (()-[:SCHEMA]->(c))
            WITH c
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p :PROPERTY)         
            DETACH DELETE c, p
            '''
        else:
            q = '''
            MATCH (c :CLASS {name: $name})
            WITH c
            OPTIONAL MATCH (c)-[:HAS_PROPERTY]->(p :PROPERTY)
            DETACH DELETE c, p
            '''
        #print(q)

        result = cls.db.update_query(q, data_binding={"name": name})
        cls.debug_print("result of update query in delete_class(): ", result)
        number_nodes_deleted = result.get("nodes_deleted", 0)   # 0 is given as default value, if not present

        if number_nodes_deleted < 1:     # If no nodes were deleted
            if safe_delete:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist, or data nodes are attached to it")
            else:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist")


    @classmethod
    def is_strict_class(cls, class_internal_id: int, schema_cache=None) -> bool:    #TODO: phase out?
        """

        :param class_internal_id:   The internal ID of a Schema Class node
        :param schema_cache:        (OPTIONAL) "SchemaCache" object
        :return:                    True if the Class is "strict" or False if not (i.e., if it's "lax")
        """
        if schema_cache:
            class_attrs = schema_cache.get_cached_class_data(class_internal_id, request="class_attributes")
        else:
            class_attrs = NeoSchema.get_class_attributes(class_internal_id)

        return class_attrs['type'] == 'S'   # True if "Strict"



    @classmethod
    def allows_data_nodes(cls, class_name = None, class_neo_id = None, schema_cache=None) -> bool:
        """
        Determine if the given Class allows data nodes directly linked to it

        :param class_name:      Name of the Class
        :param class_neo_id :   (OPTIONAL) Alternate way to specify the class; if both specified, this one prevails
        :param schema_cache:    (OPTIONAL) "SchemaCache" object
        :return:                True if allowed, or False if not
                                    If the Class doesn't exist, raise an Exception
        """
        if class_neo_id is None:    # Note: class_neo_id might legitimately be zero
            class_neo_id = cls.get_class_internal_id(class_name)

        if schema_cache is None:
            class_node_dict = cls.db.get_nodes(match=class_neo_id, single_row=True)
        else:
            class_node_dict = schema_cache.get_cached_class_data(class_neo_id, request="class_attributes")

        if class_node_dict is None:
            raise Exception(f"NeoSchema.allows_data_nodes(): Class named `{class_name}` not found in the Schema")

        if "no_datanodes" in class_node_dict:
            return not class_node_dict["no_datanodes"]

        return True    # If key is not in dictionary, then it defaults to True



    #####################################################################################################

    '''                          ~   RELATIONSHIPS AMONG CLASSES   ~                                   '''

    def ________RELATIONSHIPS_AMONG_CLASSES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def assert_valid_class_identifier(cls, class_node: Union[int, str]) -> None:
        """
        Raise an Exception is the argument is not a valid "identifier" for a Class node,
        meaning either a valid name or a valid internal database ID

        :param class_node:    Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :return:
        """
        assert (type(class_node) == str) or CypherUtils.valid_internal_id(class_node), \
                "assert_valid_class_identifier(): the class identifier must be an integer or a string"
                # TODO: tighten checks
                #       see assert_valid_class_name()



    @classmethod
    def create_class_relationship(cls, from_class: Union[int, str], to_class: Union[int, str], rel_name="INSTANCE_OF") -> None:
        """
        Create a relationship (provided that it doesn't already exist) with the specified name
        between the 2 existing Class nodes (identified by their internal database ID's or name),
        in the ( from -> to ) direction.

        In case of error, an Exception is raised

        Note: multiple relationships by the same name between the same nodes are allowed by Neo4j,
              as long as the relationships differ in their attributes
              (but this method doesn't allow setting properties on the new relationship)

        TODO: add a method that reports on all existing relationships among Classes?
        TODO: allow properties on the relationship

        :param from_class:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node from which the new relationship originates.
        :param to_class:    Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node to which the new relationship terminates.
        :param rel_name:    Name of the relationship to create, in the from -> to direction
                                (blanks allowed)
        :return:            None
        """
        # Validate the arguments
        assert rel_name, "create_class_relationship(): A name must be provided for the new relationship"
        cls.assert_valid_class_identifier(from_class)
        cls.assert_valid_class_identifier(to_class)

        # Prepare the WHERE clause for a Cypher query
        if type(from_class) == int:
            from_clause = f"id(from) = {from_class}"
        else:
            from_clause = f'from.name = "{from_class}"'

        if type(to_class) == int:
            to_clause = f"id(to) = {to_class}"
        else:
            to_clause = f'to.name = "{to_class}"'

        q = f'''
            MATCH (from:CLASS), (to:CLASS)
            WHERE {from_clause} AND {to_clause}
            MERGE (from)-[:`{rel_name}`]->(to)
            '''

        result = cls.db.update_query(q, {"from_id": from_class, "to_id": to_class})
        #print("result of update_query in create_class_relationship(): ", result)
        if result.get("relationships_created") != 1:
            raise Exception(f"create_class_relationship: failed to create new relationship named `{rel_name}` "
                            f"from Class '{from_class}' to Class '{to_class}'")



    @classmethod
    def rename_class_rel(cls, from_class: int, to_class: int, new_rel_name) -> bool:
        """
        #### TODO: NOT IN CURRENT USE
        Rename the old relationship between the specified classes
        TODO: if more than 1 relationship exists between the given Classes,
              then they will all be replaced??  TO FIX!  (the old name ought be provided)

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
        #print("result of rename_class_rel in remove_property_from_class(): ", result)
        if (result.get("relationships_deleted") == 1) and (result.get("relationships_created") == 1):
            return True
        else:
            return False



    @classmethod
    def delete_class_relationship(cls, from_class: str, to_class: str, rel_name) -> int:
        """
        Delete the relationship(s) with the specified name
        between the 2 existing Class nodes (identified by their respective names),
        going in the from -> to direction direction.
        In case of error or if no relationship was found, an Exception is raised

        Note: there might be more than one - relationships with the same name between the same nodes
              are allowed, provided that they have different properties.
              If more than one is found, they will all be deleted.  (TODO: test)
              The number of relationships deleted will be returned

        :param from_class:  Name of one existing Class node (blanks allowed in name)
        :param to_class:    Name of another existing Class node (blanks allowed in name)
        :param rel_name:    Name of the relationship(s) to delete,
                                if found in the from -> to direction (blanks allowed in name)

        :return:            The number of relationships deleted.
                            In case of error, or if no relationship was found, an Exception is raised
        """
        assert from_class, "NeoSchema.delete_class_relationship(): A name must be provided for the 'from_class' argument"
        assert to_class, "NeoSchema.delete_class_relationship(): A name must be provided for the 'to_class' argument"
        assert rel_name, "NeoSchema.delete_class_relationship(): A name must be provided for the relationship to delete"

        try:
            # Define the criteria to identify the given Class nodes
            match_from = cls.db.match(labels="CLASS", key_name="name", key_value=from_class, dummy_node_name="from")
            match_to = cls.db.match(labels="CLASS", key_name="name", key_value=to_class, dummy_node_name="to")
            # Remove the specified relationship between them
            number_removed = cls.db.remove_links(match_from=match_from, match_to=match_to, rel_name=rel_name)
        except Exception as ex:
            raise Exception(f"delete_class_relationship(): failed to delete the `{rel_name}` relationship from Schema Class `{from_class}` to Schema Class `{to_class}`. {ex}")

        return number_removed



    @classmethod
    def unlink_classes(cls, class1: int, class2: int) -> bool:
        """
        Remove ALL relationships (in any direction) between the specified classes

        :param class1:  Integer ID to identify the first Class
        :param class2:  Integer ID to identify the second Class
        :return:        True if exactly one relationship (in either direction) was found, and successfully removed;
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
    def class_relationship_exists(cls, from_class: str, to_class: str, rel_name) -> bool:
        """     # TODO: pytest
        Return True if a relationship with the specified name exists between the two given Classes,
        in the specified direction

        :param from_class:  Name of one existing Class node (blanks allowed in name)
        :param to_class:    Name of another existing Class node (blanks allowed in name)
        :param rel_name:    Name of the relationship(s) to delete,
                                if found in the from -> to direction (blanks allowed in name)
        :return:
        """
        # Define the criteria to identify the given Class nodes
        match_from = cls.db.match(labels="CLASS", key_name="name", key_value=from_class, dummy_node_name="from")
        match_to = cls.db.match(labels="CLASS", key_name="name", key_value=to_class, dummy_node_name="to")
        return cls.db.links_exist(match_from=match_from, match_to=match_to, rel_name=rel_name)



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



    @classmethod
    def get_linked_class_names(cls, class_name: str, rel_name: str, enforce_unique=False) -> Union[str, List[str]]:
        """
        Given a Class, specified by its name, locate and return the name(s) of the other Class(es)
        that it's linked to by means of the relationship with the specified name.
        Typically, the result will contain no more than 1 name, but it could be more;
        it's probably a bad design to use the same relationship name to connect a class to multiple other classes
        (though currently allowed.)
        Relationships are followed in the OUTbound direction only.

        :param class_name:      Name of a Class in the schema
        :param rel_name:        Name of relationship to follow (in the OUTbound direction) from the above Class
        :param enforce_unique:  If True, it raises an Exception if the number of results isn't exactly one

        :return:                If enforce_unique is True, return a string with the class name;
                                otherwise, return a list of names (typically just one)
        """
        q = f'''
            MATCH (from :`CLASS` {{name: $class_name}})
                  -[:{rel_name}]
                  ->(to :`CLASS`)
            RETURN to.name AS related_class_name
        '''
        result = cls.db.query(q, data_binding={"class_name": class_name}, single_column="related_class_name")

        if enforce_unique:
            if len(result) == 0:
                raise Exception(f"This relationship (`{rel_name}`) doesn't connect to other classes in the Schema")
            if len(result) > 1:
                raise Exception(f"This relationship (`{rel_name}`) ambiguously leads to multiple other classes in the Schema: {result}")

            return result[0]    # If we get thus far, there's exactly one element in result


        return result       # This will be a list (though normally with just 1 element)



    @classmethod
    def get_class_relationships(cls, schema_id:int, link_dir="BOTH", omit_instance=False) -> Union[dict, list]:
        """
        Fetch and return the names of all the relationship (both inbound and outbound)
        attached to the given Class.
        Treat separately the inbound and the outbound ones.

        :param schema_id:       An integer to identify the desired Class
        :param link_dir:        Desired direction(s) of the relationships; one of "BOTH" (default), "IN" or "OUT"
        :param omit_instance:   If True, the common outbound relationship "INSTANCE_OF" is omitted

        :return:                If link_dir is "BOTH", return a dictionary of the form
                                    {"in": list of inbound-relationship names,
                                     "out": list of outbound-relationship names}
                                Otherwise, just return the inbound or outbound list, based on the value of link_dir
        """
        assert link_dir in ["BOTH", "IN", "OUT"], \
                f'The argument `link_dir` must be one of "BOTH", "IN" or "OUT" (value passed was {link_dir})'

        if link_dir == "IN":
            rel_out = []        # We only want the inbound relationships; disregard the outbound ones
        else:
            if omit_instance:
                q_out = '''
                    MATCH (n:CLASS {schema_id:$schema_id})-[r]->(cl:CLASS)
                    WHERE type(r) <> "INSTANCE_OF"
                    RETURN type(r) AS rel_name
                    '''
            else:
                q_out = '''
                    MATCH (n:CLASS {schema_id:$schema_id})-[r]->(cl:CLASS) 
                    RETURN type(r) AS rel_name
                    '''
            rel_out = cls.db.query(q_out, data_binding={"schema_id": schema_id}, single_column="rel_name")


        if link_dir == "OUT":
            rel_in = []        # We only want the outbound relationships; disregard the inbound ones
        else:
            q_in = '''
                    MATCH (n:CLASS {schema_id:$schema_id})<-[r]-(cl:CLASS) 
                    RETURN type(r) AS rel_name
                    '''
            rel_in = cls.db.query(q_in, data_binding={"schema_id": schema_id}, single_column="rel_name")

        if link_dir == "BOTH":
            return  {"in": rel_in, "out": rel_out}
        elif link_dir == "IN":
           return rel_in
        else:
            return rel_out



    @classmethod
    def get_class_outbound_data(cls, class_neo_id:int, omit_instance=False) -> dict:
        """
        Efficient all-at-once query to fetch and return the names of all the outbound relationship
        attached to the given Class, as well as the names of the other Classes on the other side of those links.

        IMPORTANT: it's probably a bad design to use the same relationship name to connect a class
        to multiple other classes.  Though currently allowed in the Schema, this particular method
        assumes - and enforces - uniqueness

        :param class_neo_id:    An integer to identify the desired Class
        :param omit_instance:   If True, the common outbound relationship "INSTANCE_OF" is omitted

        :return:                A (possibly empty) dictionary,
                                    where the keys are the name of outbound relationships,
                                    and the values are the names of the Class nodes on the other side of those links.
                                    An Exception will be raised if link names are not unique [though currently allowed by the Schema]
                                    EXAMPLE: {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}
        """

        if omit_instance:
            q_out = '''
                MATCH (from :CLASS)-[r]->(to :CLASS)
                WHERE id(from) = $class_neo_id AND type(r) <> "INSTANCE_OF"
                RETURN type(r) AS rel_name, to.name AS neighbor
                '''
        else:
            q_out = '''
                MATCH (from :CLASS)-[r]->(to :CLASS)
                WHERE id(from) = $class_neo_id
                RETURN type(r) AS rel_name, to.name AS neighbor
                '''

        results = cls.db.query(q_out, data_binding={"class_neo_id": class_neo_id})
        #print("********** get_class_outbound_data intermediate: ", results)


        outbound_link_map = {}
        for record in results:
            k, val = record['rel_name'], record['neighbor']
            if record['rel_name'] in outbound_link_map:
                raise Exception(f"NeoSchema.get_class_outbound_data: this function doesn't allow "
                                f"multiple outgoing links with same name ({k}) from a Class (neo_id {class_neo_id})")
            else:
                outbound_link_map[k] = val

        #print("********** get_class_outbound_data final: ", outbound_link_map)

        return outbound_link_map




    #####################################################################################################

    '''                                ~   PROPERTIES-RELATED   ~                                     '''

    def ________PROPERTIES_RELATED________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def get_class_properties_fast(cls, class_neo_id: int, include_ancestors=False, sort_by_path_len=False) -> [str]:
        """
        Faster version of get_class_properties()  [Using class_neo_id]

        Return the list of all the names of the Properties associated with the given Class
        (including those inherited thru ancestor nodes by means of "INSTANCE_OF" relationships,
        if include_ancestors is True),
        sorted by the schema-specified position (or, optionally, by path length)

        :param class_neo_id:        Integer with the Neo4j ID of a Class node
        :param include_ancestors:   If True, also include the Properties attached to Classes that are ancestral
                                    to the given one by means of a chain of outbound "INSTANCE_OF" relationships
                                    Note: the sorting by relationship index won't mean much if ancestral nodes are included,
                                          with their own indexing of relationships; if order matters in those cases, use the
                                          "sort_by_path_len" argument, below
        :param sort_by_path_len:    Only applicable if include_ancestors is True.
                                    If provided, it must be either "ASC" or "DESC", and it will sort the results by path length
                                    (either ascending or descending), before sorting by the schema-specified position for each Class.
                                    Note: with "ASC", the immediate Properties of the given Class will be listed first

        :return:                    A list of the Properties of the specified Class (including indirectly, if include_ancestors is True)
        """
        if include_ancestors:
            # Follow zero or more outbound "INSTANCE_OF" relationships from the given Class node;
            #   "zero" relationships means the original node itself (handy in situations when there are no such relationships)
            if sort_by_path_len:
                assert (sort_by_path_len == "ASC" or sort_by_path_len == "DESC"), \
                    "If the argument sort_by_path_len is provided, it must be either 'ASC' or 'DESC'"

                q = f'''
                    MATCH path=(c :CLASS)-[:INSTANCE_OF*0..]->(c_ancestor)
                                -[r:HAS_PROPERTY]->(p :PROPERTY)
                    WHERE id(c) = $class_neo_id
                    RETURN p.name AS prop_name
                    ORDER BY length(path) {sort_by_path_len}, r.index
                    '''
            else:
                q = '''
                    MATCH (c :CLASS)-[:INSTANCE_OF*0..]->(c_ancestor)
                          -[r:HAS_PROPERTY]->(p :PROPERTY) 
                    WHERE id(c) = $class_neo_id
                    RETURN p.name AS prop_name
                    ORDER BY r.index
                    '''

        else:
            # NOT including ancestor nodes
            q = '''
                MATCH (c :CLASS)-[r :HAS_PROPERTY]->(p :PROPERTY)
                WHERE id(c) = $class_neo_id
                RETURN p.name AS prop_name
                ORDER BY r.index
                '''

        name_list = cls.db.query(q, {"class_neo_id": class_neo_id}, single_column="prop_name")

        return name_list



    @classmethod
    def get_class_properties(cls, schema_id: int, include_ancestors=False, sort_by_path_len=False) -> list:
        """
        TODO: maybe phase out in favor of get_class_properties_fast()

        Return the list of all the names of the Properties associated with the given Class
        (including those inherited thru ancestor nodes by means of "INSTANCE_OF" relationships,
        if include_ancestors is True),
        sorted by the schema-specified position (or, optionally, by path length)

        :param schema_id:           Integer with the ID of a Class node
        :param include_ancestors:   If True, also include the Properties attached to Classes that are ancestral
                                    to the given one by means of a chain of outbound "INSTANCE_OF" relationships
                                    Note: the sorting by relationship index won't mean much if ancestral nodes are included,
                                          with their own indexing of relationships; if order matters in those cases, use the
                                          "sort_by_path_len" argument, below
        :param sort_by_path_len:    Only applicable if include_ancestors is True.
                                    If provided, it must be either "ASC" or "DESC", and it will sort the results by path length
                                    (either ascending or descending), before sorting by the schema-specified position for each Class.
                                    Note: with "ASC", the immediate Properties of the given Class will be listed first

        :return:                    A list of the Properties of the specified Class (including indirectly, if include_ancestors is True)
        """
        if include_ancestors:
            # Follow zero or more outbound "INSTANCE_OF" relationships from the given Class node;
            #   "zero" relationships means the original node itself (handy in situations when there are no such relationships)
            if sort_by_path_len:
                assert (sort_by_path_len == "ASC" or sort_by_path_len == "DESC"), \
                    "If the argument sort_by_path_len is provided, it must be either 'ASC' or 'DESC'"

                q = f'''
                    MATCH path=(c :CLASS {{schema_id: $schema_id}})-[:INSTANCE_OF*0..]->(c_ancestor)
                                -[r:HAS_PROPERTY]->(p :PROPERTY) 
                    RETURN p.name AS prop_name
                    ORDER BY length(path) {sort_by_path_len}, r.index
                    '''
            else:
                q = '''
                    MATCH (c :CLASS {schema_id: $schema_id})-[:INSTANCE_OF*0..]->(c_ancestor)
                          -[r:HAS_PROPERTY]->(p :PROPERTY) 
                    RETURN p.name AS prop_name
                    ORDER BY r.index
                    '''

        else:
            # NOT including ancestor nodes
            q = '''
                MATCH (c :CLASS {schema_id: $schema_id})-[r :HAS_PROPERTY]->(p :PROPERTY)
                RETURN p.name AS prop_name
                ORDER BY r.index
                '''

        result_list = cls.db.query(q, {"schema_id": schema_id})

        name_list = [item["prop_name"] for item in result_list]

        return name_list



    @classmethod
    def add_properties_to_class(cls, class_node = None, class_id = None, property_list = None) -> int:
        """
        Add a list of Properties to the specified (ALREADY-existing) Class.
        The properties are given an inherent order (an attribute named "index", starting at 1),
        based on the order they appear in the list.
        If other Properties already exist, the existing numbering gets extended.
        TODO: Offer a way to change the order of the Properties,
              maybe by first deleting all Properties and then re-adding them

        NOTE: if the Class doesn't already exist, use create_class_with_properties() instead;
              attempting to add properties to an non-existing Class will result in an Exception

        :param class_node:      Either an integer with the internal database ID of an existing Class node,
                                    (or a string with its name - TODO: add support for this option)
        :param class_id:        Integer with the schema_id of the Class to which attach the given Properties
                                TODO: remove

        :param property_list:   A list of strings with the names of the properties, in the desired order.
                                    Whitespace in any of the names gets stripped out.
                                    If any name is a blank string, an Exception is raised
                                    If the list is empty, an Exception is raised
        :return:                The number of Properties added
        """
        assert (class_node is not None) or (class_id is not None), \
            "add_properties_to_class(): class_internal_id and class_id cannot both be None"

        if class_node is not None and class_id is None:
            class_id = cls.get_class_id_by_neo_id(class_node)

        assert type(class_id) == int,\
            f"add_properties_to_class(): Argument `class_id` in add_properties_to_class() must be an integer; value passed was {class_id}"
        assert type(property_list) == list, \
            "add_properties_to_class(): Argument `property_list` in add_properties_to_class() must be a list"
        assert cls.class_id_exists(class_id), \
            f"add_properties_to_class(): No Class with ID {class_id} found in the Schema"



        clean_property_list = [prop.strip() for prop in property_list]
        for prop_name in clean_property_list:
            assert prop_name != "", "add_properties_to_class(): Unacceptable Property name, either empty or blank"
            assert type(prop_name) == str, "add_properties_to_class(): Unacceptable non-string Property name"

        # Locate the largest index of the Properties currently present (stored on the "HAS_PROPERTY" links)
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
            new_schema_id = cls.next_available_schema_id()
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
    def create_class_with_properties(cls, class_name: str, property_list: [str], code=None, strict=False,
                                     class_to_link_to=None, link_name="INSTANCE_OF", link_dir="OUT") -> (int, int):
        """
        Create a new Class node, with the specified name, and also create the specified Properties nodes,
        and link them together with "HAS_PROPERTY" relationships.

        Return the internal database ID and the auto-incremented unique ID ("scheme ID") assigned to the new Class.
        Each Property node is also assigned a unique "scheme ID";
        the "HAS_PROPERTY" relationships are assigned an auto-increment index,
        representing the default order of the Properties.

        If a class_to_link_to name is specified, link the newly-created Class node to that existing Class node,
        using an outbound relationship with the specified name.  Typically used to create "INSTANCE_OF"
        relationships from new Classes.

        If a Class with the given name already exists, nothing is done,
        and an Exception is raised.

        NOTE: if the Class already exists, use add_properties_to_class() instead

        :param class_name:      String with name to assign to the new class
                                TODO: change to "name" for consistency with create_class()

        :param property_list:   List of strings with the names of the Properties, in their default order (if that matters)
        :param code:            Optional string indicative of the software handler for this Class and its subclasses
        :param strict:          If True, the Class will be of the "S" (Strict) type;
                                    otherwise, it'll be of the "L" (Lenient) type

        :param class_to_link_to: If this name is specified, and a link_to_name (below) is also specified,
                                    then create an OUTBOUND relationship from the newly-created Class
                                    to this existing Class
        :param link_name:       Name to use for the above relationship, if requested.  Default is "INSTANCE_OF"
        :param link_dir:        Desired direction(s) of the relationships: either "OUT" (default) or "IN"

        :return:                If successful, the pair (internal ID, integer "schema_id" assigned to the new Class);
                                otherwise, raise an Exception
        """
        # TODO: it would be safer to use fewer Cypher transactions; right now, there's the risk of
        #       adding a new Class and then leaving it without properties or links, in case of mid-operation error

        if class_to_link_to:
            assert link_name, \
                "create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                "a valid value for the argument `link_to_name` must also be provided"

            assert (link_dir == "OUT") or (link_dir == "IN"), \
                f"create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                f"the argument `link_dir` must be either 'OUT' or 'IN' (value passed: {link_dir})"


        # Create the new Class
        new_class_int_id , new_class_uri = cls.create_class(class_name, code=code, strict=strict)
        cls.debug_print(f"Created new schema CLASS node (name: `{class_name}`, Schema ID: {new_class_uri})")

        number_properties_added = cls.add_properties_to_class(class_node=new_class_int_id, property_list = property_list)
        if number_properties_added != len(property_list):
            raise Exception(f"The number of Properties added ({number_properties_added}) does not match the size of the requested list: {property_list}")

        cls.debug_print(f"{number_properties_added} Properties added to the new Class: {property_list}")


        if class_to_link_to and link_name:
            # Create a relationship between the newly-created Class and an existing Class whose name is given by class_to_link_to
            #other_class_id = NeoSchema.get_class_id(class_name = class_to_link_to)
            #cls.debug_print(f"Internal database ID of the `{class_to_link_to}` class to link to: {other_class_id}")
            try:
                if link_dir == "OUT":
                    NeoSchema.create_class_relationship(from_class=new_class_int_id, to_class=class_to_link_to, rel_name =link_name)
                else:
                    NeoSchema.create_class_relationship(from_class=class_to_link_to, to_class=new_class_int_id, rel_name =link_name)
            except Exception as ex:
                raise Exception(f"New Class ({class_name}) created successfully, but unable to link it to the `{class_to_link_to}` class. {ex}")

        return new_class_int_id, new_class_uri



    @classmethod
    def remove_property_from_class(cls, class_id: int, property_id: int) -> None:
        """
        Take out the specified (single) Property from the given Class.
        If the Class or Property was not found, or if the Property could not be removed, an Exception is raised

        :param class_id:    The schema ID of the Class node
        :param property_id: The schema ID of the Property node
        :return:            None
        """
        assert NeoSchema.class_id_exists(class_id), f"The schema has no Class with the requested ID of {class_id}"

        q = f'''
            MATCH (c :CLASS {{ schema_id: {class_id} }})
                  -[:HAS_PROPERTY]
                  ->(p :PROPERTY {{ schema_id: {property_id}}})
            DETACH DELETE p
            '''

        result = cls.db.update_query(q)
        #print("result of update_query in remove_property_from_class(): ", result)

        # Validate the results of the query
        assert result.get("nodes_deleted") == 1, f"Failed to find or delete the Property node (with schema_id {property_id})"
        assert result.get("relationships_deleted") == 1, "Failed to find or delete the relationship"




    #####################################################################################################
    #                                                                                                   #
    #                                    ~ SCHEMA-CODE  RELATED ~                                       #
    #                                                                                                   #
    #####################################################################################################

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

        match = cls.db.match(labels="CLASS", key_name="code", key_value=schema_code)
        result = cls.db.get_nodes(match, single_cell="schema_id")

        if result is None:
            return -1

        return result




    #####################################################################################################

    '''                                      ~   DATA NODES   ~                                       '''

    def ________DATA_NODES________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def all_properties(cls, label, primary_key_name, primary_key_value) -> [str]:
        """
        Return the list of the names of all the Properties associated with the given DATA node,
        based on the Schema it is associated with, sorted their by schema-specified position.
        The desired node is identified by specifying which one of its attributes is a primary key,
        and providing a value for it

        :param label:
        :param primary_key_name:
        :param primary_key_value:
        :return:
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
    def get_data_node_internal_id(cls, item_id: int) -> int:
        """
        Returns the internal database ID of the given data node,
        specified by its value of the item_id attribute

        :param item_id: Integer to identify a data node by the value of its item_id attribute
        :return:        The internal database ID of the specified data node
        """
        match = cls.db.match(key_name="item_id", key_value=item_id)
        result = cls.db.get_nodes(match, return_internal_id=True)

        if not result:
            raise Exception(f"NeoSchema.get_data_node_internal_id(): no Data Node with the given item_id ({item_id}) was found")

        if len(result) > 1:
            raise Exception(f"NeoSchema.get_data_node_internal_id(): more than 1 Data Node "
                            f"with the given item_id ({item_id}) was found ({len(result)} were found)")

        return result[0]["internal_id"]



    @classmethod
    def fetch_data_node(cls, item_id = None, internal_id = None, labels=None, properties=None) -> Union[dict, None]:
        """
        Return a dictionary with all the key/value pairs of the attributes of given data node

        See also locate_node()

        :param item_id:     The "item_id" field to uniquely identify the data node
        :param internal_id: OPTIONAL alternate way to specify the data node;
                                if present, it takes priority
        :param labels:      OPTIONAL (generally, redundant) ways to locate the data node
        :param properties:  OPTIONAL (generally, redundant) ways to locate the data node

        :return:            A dictionary with all the key/value pairs, if found; or None if not
        """
        if internal_id is None:
            assert item_id is not None, \
                "NeoSchema.fetch_data_node(): arguments `item_id` and `internal_id` cannot both be None"

            match = cls.db.match(key_name="item_id", key_value=item_id,
                                 labels=labels, properties=properties)
        else:
            match = cls.db.match(internal_id=internal_id, labels=labels, properties=properties)

        return cls.db.get_nodes(match, single_row=True)



    @classmethod
    def locate_node(cls, node_id: Union[int, str], id_type=None, labels=None, dummy_node_name="n") -> CypherMatch:
        """
        EXPERIMENTAL - a generalization of fetch_data_node()

        Return the "match" structure to locate a node identified
        either by its internal database ID (default), or by a primary key (with optional label.)

        :param node_id: This is understood be the Neo4j ID, unless an id_type is specified
        :param id_type: For example, "item_id";
                            if not specified, the node ID is assumed to be Neo4j ID's
        :param labels:  (OPTIONAL) Labels - a string or list/tuple of strings - for the node
        :param dummy_node_name: (OPTIONAL) A string with a name by which to refer to the node (by default, "n")

        :return:        A "CypherMatch" object
        """
        if id_type:
            match_structure = cls.db.match(key_name=id_type, key_value=node_id, labels=labels)
        else:
            match_structure = cls.db.match(internal_id=node_id)

        return CypherUtils.process_match_structure(match_structure, dummy_node_name=dummy_node_name)



    @classmethod
    def data_nodes_of_class(cls, class_name) -> [int]:
        """
        Return the Item ID's of all the Data Nodes of the given Class
        TODO: offer to optionally use a label
        TODO: switch to returning the internal database ID's

        :param class_name:
        :return:            Return the Item ID's of all the Data Nodes of the given Class
        """
        q = '''
            MATCH (n)-[:SCHEMA]->(c:CLASS {name: $class_name}) RETURN n.item_id AS item_id
            '''

        res = cls.db.query(q, {"class_name": class_name}, single_column="item_id")

        # Alternate approach
        #match = cls.db.match(labels="CLASS", properties={"name": "Categories"})
        #cls.db.follow_links(match, rel_name="SCHEMA", rel_dir="IN", neighbor_labels="BA")

        return res



    @classmethod
    def count_data_nodes_of_class(cls, class_id: Union[int, str]) -> [int]:
        """
        Return the count of all the Data Nodes attached to the given Class

        :param class_id:    Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :return:            The count of all the Data Nodes attached to the given Class
        """
        # TODO: introduce new method assert_valid_class_id()

        if type(class_id) == int:
            assert cls.class_neo_id_exists(class_id), \
                f"NeoSchema.count_data_nodes_of_class(): no Class with an internal ID of {class_id} exists"

            q = f'''
                MATCH (n)-[:SCHEMA]->(cl :CLASS)
                WHERE id(cl) = {class_id}
                RETURN count(n) AS number_datanodes
                '''
        else:
            q = f'''
                MATCH (n)-[:SCHEMA]->(cl :CLASS)
                WHERE cl.name = "{class_id}"
                RETURN count(n) AS number_datanodes
                '''

        res = cls.db.query(q, single_cell="number_datanodes")

        return res



    @classmethod
    def allowable_props(cls, class_neo_id: int, requested_props: dict, silently_drop: bool, schema_cache=None) -> dict:
        """
        Return a pared-down version, or possibly raise an Exception, of the requested list of properties
        that are meant to be assigned to a new data node.
        A new data node gets created only if
        there's no other data node with the same allowed properties;
        TODO: possibly expand to handle REQUIRED properties

        :param class_neo_id:    The internal ID of a Schema Class node
        :param requested_props: A dictionary of properties one wishes to assign to a new data node, if the Schema allows
        :param silently_drop:   If True, any requested properties not allowed by the Schema are simply dropped;
                                    otherwise, an Exception is raised if any property isn't allowed
        :param schema_cache:    (OPTIONAL) "NeoSchemaExperimental" object

        :return:                A possibly pared-down version of the requested_props dictionary
        """
        if not cls.is_strict_class(class_neo_id, schema_cache=schema_cache):    #TODO: phase out?
            return requested_props      # Any properties are allowed if the Class isn't strict


        allowed_props = {}
        class_properties = cls.get_class_properties_fast(class_neo_id)  # List of Properties registered with the Class

        for requested_prop in requested_props.keys():
            # Check each of the requested properties
            if requested_prop in class_properties:
                allowed_props[requested_prop] = requested_props[requested_prop]     # Allowed
            else:
                # Not allowed
                if not silently_drop:
                    raise Exception(f"NeoSchema.allowable_props(): "
                                    f"the requested attribute `{requested_prop}` is not among the registered Properties "
                                    f"of the Class `{cls.get_class_name_by_neo_id(class_neo_id)}`")

        return allowed_props



    @classmethod    # TODO: unit test
    def create_data_node(cls, class_node: Union[int, str], properties = None, labels = None,
                         assign_uri=False, new_uri=None, silently_drop=False) -> int:
        """
        A newer version of the deprecated add_data_point_OLD() and add_data_point()

        Create a new data node, of the type indicated by specified Class,
        with the given (possibly none) attributes and label(s);
        if no labels are given, the name of the Class is used as a label.

        The new data node, if successfully created, will optionally be assigned
        a passed URI value, or a unique auto-gen value, for its field item_id.

        If the requested Class doesn't exist, an Exception is raised

        If the data node needs to be created with links to other existing data nodes,
        use add_data_node_with_links() instead

        :param class_node:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :param properties:  (Optional) Dictionary with the properties of the new data node.
                                EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:      (Optional) String, or list of strings, with label(s) to assign to the new data node;
                                if not specified, the Class name is used
        :param assign_uri:  If True, the new node is given an extra attribute named "item_id",
                                with a unique auto-increment value, as well an extra attribute named "schema_code"
        :param new_uri:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                If new_item_id is provided, then assign_item_id is automatically made True
        :param silently_drop: If True, any requested properties not allowed by the Schema are simply dropped;
                                otherwise, an Exception is raised if any property isn't allowed
                                TODO: only applicable for "Strict" schema - with a "Lax" schema anything goes

        :return:            The internal database ID of the new data node just created
        """
        cls.assert_valid_class_identifier(class_node)

        # TODO: simplify not having to lug around both name and internal ID
        if type(class_node) == str:
            class_name = class_node
            class_internal_id = cls.get_class_internal_id(class_node)
        else:
            class_name = cls.get_class_name_by_neo_id(class_node)
            class_internal_id = class_node

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if properties is None:
            properties = {}

        assert type(properties) == dict, \
            "NeoSchema.add_data_node(): The `properties` argument, if provided, MUST be a dictionary"

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_node(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        properties_to_set = cls.allowable_props(class_internal_id, requested_props=properties,
                                                silently_drop=silently_drop)


        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes:
        # "uri" and "schema_code";
        # if requested, expand properties_to_set accordingly
        if assign_uri or new_uri:
            if not new_uri:
                new_id = cls.next_available_datanode_id()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_uri
            #print("New ID assigned to new data node: ", new_id)
            properties_to_set["item_id"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                properties_to_set["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of properties_to_set at this stage:
            #       {"make": "Toyota", "color": "white", "item_id": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned item_id


        # Create a new data node, with a "SCHEMA" relationship to its Class node
        link_to_schema_class = {"internal_id": class_internal_id, "rel_name": "SCHEMA", "rel_dir": "OUT"}

        links = [link_to_schema_class]

        neo_id = cls.db.create_node_with_links(labels=labels,
                                               properties=properties_to_set,
                                               links=links)

        return neo_id



    @classmethod    # TODO: obsolete in favor of create_data_node()
    def add_data_point(cls, class_name=None, class_internal_id=None, properties = None, labels = None,
                       assign_item_id=False, new_item_id=None, silently_drop=False) -> int:
        """
        TODO: maybe rename create_data_node(), for consistency with create_class()
        TODO: merge class_name and class_internal_id
        A more "modern" version of the deprecated add_data_point_OLD()

        Add a new data node, of the specified Class,
        with the given (possibly none) attributes and label(s);
        if no labels are given, the name of the Class is used as a label.

        The new data node, if successfully created, will optionally be assigned
        a passed value, or a unique auto-gen value, for its field item_id.
        If the requested Class doesn't exist, an Exception is raised

        If the data point needs to be created with links to other existing data points, use add_data_node_with_links() instead

        :param class_name:      Name of the Class for the new data point
        :param class_internal_id: The internal database ID of the Class node for the new data point
                                NOTE: if both class_name and class_internal_id are specified, the latter prevails
        :param properties:      An optional dictionary with the properties of the new data point.
                                    EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          OPTIONAL string, or list of strings, with label(s) to assign to the new data node;
                                    if not specified, the Class name is used
        :param assign_item_id:  If True, the new node is given an extra attribute named "item_id",
                                    with a unique auto-increment value, as well an extra attribute named "schema_code"
        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                    If new_item_id is provided, then assign_item_id is automatically made True
        :param silently_drop:   If True, any requested properties not allowed by the Schema are simply dropped;
                                    otherwise, an Exception is raised if any property isn't allowed
                                    TODO: only true for "Strict" schema - with a "Lax" schema anything goes; but "Lax" schema
                                          will probably be phased out

        :return:                The internal database ID of the new data node just created
        """
        #schema_cache = SchemaCache()   # TODO: later restore the cached Schema data
        #class_attrs = schema_cache.get_cached_class_data(class_internal_id, request="class_attributes")
        #class_name = class_attrs["name"]
        if class_internal_id is None:
            if not class_name:
                raise Exception("add_data_point(): at least one of the arguments `class_name` or `class_internal_id` must be provided")
            else:
                cls.assert_valid_class_name(class_name)

            class_internal_id = cls.get_class_internal_id(class_name)
        else:
            class_name = cls.get_class_name_by_neo_id(class_internal_id)

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if properties is None:
            properties = {}

        assert type(properties) == dict, \
            "NeoSchema.add_data_point(): The `properties` argument, if provided, MUST be a dictionary"

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_point(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        properties_to_set = cls.allowable_props(class_internal_id, requested_props=properties,
                                                silently_drop=silently_drop)


        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes: "item_id" and "schema_code";
        # if requested, expand properties_to_set accordingly
        if assign_item_id or new_item_id:
            if not new_item_id:
                new_id = cls.next_available_datanode_id()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_item_id
            #print("New ID assigned to new data node: ", new_id)
            properties_to_set["item_id"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                properties_to_set["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of properties_to_set at this stage:
            #       {"make": "Toyota", "color": "white", "item_id": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned item_id


        # Create a new data node, with a "SCHEMA" relationship to its Class node
        link_to_schema_class = {"internal_id": class_internal_id, "rel_name": "SCHEMA", "rel_dir": "OUT"}

        links = [link_to_schema_class]

        neo_id = cls.db.create_node_with_links(labels=labels,
                                           properties=properties_to_set,
                                           links=links)

        return neo_id



    @classmethod
    def add_data_node_merge(cls, class_internal_id, properties = None, labels = None, silently_drop=False,
                            schema_cache=None) -> (int, bool):
        """
        Similar to add_data_point_new(), but a new data node gets created only if
        there's no other data node with the same labels and allowed properties

        :param class_internal_id:   The internal database ID of the Class node for the data node
        :param properties:          An optional dictionary with the properties of the new data node.
                                        EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:              OPTIONAL string, or list of strings, with label(s) to assign to the new data node;
                                        if not specified, the Class name is used
        :param silently_drop:       If True, any requested properties not allowed by the Schema are simply dropped;
                                        otherwise, an Exception is raised if any property isn't allowed
        :param schema_cache:        (OPTIONAL) "SchemaCache" object

        :return:                    A pair with:
                                        1) The internal database ID of either an existing data node or of a new one just created
                                        2) True if a new data node was created, or False if not (i.e. an existing one was found)
        """
        if schema_cache is None:
            schema_cache = SchemaCache()

        class_attrs = schema_cache.get_cached_class_data(class_internal_id, request="class_attributes")
        class_name = class_attrs["name"]

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if properties is None:
            properties = {}

        assert type(properties) == dict, \
            "NeoSchema.add_data_node_merge(): the `properties` argument, if provided, MUST be a dictionary"

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id, schema_cache=schema_cache):
            raise Exception(f"NeoSchema.add_data_node_merge(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        properties_to_set = cls.allowable_props(class_internal_id, requested_props=properties,
                                                silently_drop=silently_drop, schema_cache=schema_cache)

        result = cls.db.merge_node(labels=labels, properties=properties_to_set)
        datanode_neo_id = result["internal_id"]

        if result["created"]:
            # If a new data node was created, it must be linked to its Class node
            cls.db.add_links_fast(match_from=datanode_neo_id, match_to=class_internal_id, rel_name="SCHEMA")
        else:
            # Verify that is already has a SCHEMA link to its Class node
            if not cls.db.links_exist(match_from=datanode_neo_id, match_to=class_internal_id, rel_name="SCHEMA"):
                # This is an irregular situation where there's a match, but not to a legit data node
                raise Exception(f"NeoSchema.add_data_node_merge(): "
                                f"a node matching in attributes and labels already exists (internal ID {datanode_neo_id}), "
                                f"but it's NOT linked to its Schema Class (internal ID {class_internal_id})")

        return datanode_neo_id, result["created"]



    @classmethod
    def add_data_column_merge(cls, class_internal_id: int, property_name: str, value_list: list) -> dict:
        """
        Add a data column (i.e. a set of single-property data nodes).
        Individual nodes are created only if there's no other data node with the same property/value

        TODO: this is a simple approach; introduce a more efficient one, possibly using APOC

        :param class_internal_id:   The internal database ID of the Class node for the data nodes
        :param property_name:       The name of the data column
        :param value_list:          The data column as a list
        :return:                    A dictionary with 2 keys - "new_nodes" and "old_nodes"
                                        TODO: rename "old_nodes" to "present_nodes" (or "existing_nodes")
        """
        assert type(property_name) == str, \
            f"NeoSchema.add_col_data_merge(): argument `property_name` must be a string; " \
            f"value passed was of type {type(property_name)}"

        assert type(value_list) == list, \
            f"NeoSchema.add_col_data_merge(): argument `value_list` must be a list; " \
            f"value passed was of type {type(value_list)}"

        schema_cache = SchemaCache()

        new_id_list = []
        existing_id_list = []
        for value in value_list:
            new_id, created = cls.add_data_node_merge(class_internal_id,
                                                      properties={property_name: value},
                                                      schema_cache=schema_cache,
                                                      silently_drop=False)
            if created:
                new_id_list.append(new_id)
            else:
                existing_id_list.append(new_id)

        return {"new_nodes": new_id_list, "old_nodes": existing_id_list}



    @classmethod
    def add_data_node_with_links(cls, class_name = None, class_internal_id = None,
                                 properties = None, labels = None,
                                 links = None,
                                 assign_item_id=False, new_item_id=None) -> int:
        """
        This is NeoSchema's counterpart of NeoAccess.create_node_with_links()

        Add a new data node, of the Class specified by its name,
        with the given (possibly none) attributes and label(s),
        optionally linked to other, already existing, DATA nodes.

        If the specified Class doesn't exist, or doesn't allow for Data Nodes, an Exception is raised.

        The new data node, if successfully created:
            1) will be given the Class name as a label, unless labels are specified
            2) will optionally be assigned an "item_id" unique value
               that is either automatically assigned or passed.

        EXAMPLES:   add_data_node_with_links(class_name="Cars",
                                              properties={"make": "Toyota", "color": "white"},
                                              links=[{"internal_id": 123, "rel_name": "OWNED_BY", "rel_dir": "IN"}])

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: verify that all the requested links conform to the Schema
        TODO: invoke special plugin-code, if applicable
        TODO: maybe rename to add_data_node()

        :param class_name:  The name of the Class that this new data node is an instance of.
                                Also use to set a label on the new node, if labels isn't specified
        :param class_internal_id: OPTIONAL alternative to class_name.  If both specified,
                                class_internal_id prevails
        :param properties:  An optional dictionary with the properties of the new data node.
                                EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:      OPTIONAL string, or list of strings, with label(s) to assign to the new data node;
                                if not specified, use the Class name.  TODO: ALWAYS include the Class name
        :param links:       OPTIONAL list of dicts identifying existing nodes,
                                and specifying the name, direction and optional properties
                                to give to the links connecting to them;
                                use None, or an empty list, to indicate if there aren't any
                                Each dict contains the following keys:
                                    "internal_id"   REQUIRED - to identify an existing node
                                    "rel_name"      REQUIRED - the name to give to the link
                                    "rel_dir"       OPTIONAL (default "OUT") - either "IN" or "OUT" from the new node
                                    "rel_attrs"     OPTIONAL - A dictionary of relationship attributes

        :param assign_item_id:  If True, the new node is given an extra attribute named "item_id",
                                    with a unique auto-increment value, as well an extra attribute named "schema_code".
                                    Default is False
                                    TODO: rename to assign_token
        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                    If new_item_id is provided, then assign_item_id is automatically made True
                                    TODO: rename to new_token

        :return:                If successful, an integer with the internal database ID of the node just created;
                                    otherwise, an Exception is raised
        """
        if class_internal_id is None:                                # Note: zero could be a valid value
            class_internal_id = cls.get_class_internal_id(class_name)     # This call will also validate the class name

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if properties is None:
            properties = {}

        assert type(properties) == dict, "NeoSchema.add_data_node_with_links(): The `properties` argument, if provided, MUST be a dictionary"

        cypher_prop_dict = properties

        assert links is None or type(links) == list, \
            f"NeoAccess.add_data_node_with_links(): The argument `links` must be a list or None; instead, it's of type {type(links)}"

        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_node_with_links(): Addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes: "item_id" and "schema_code";
        # if requested, expand cypher_prop_dict accordingly
        if assign_item_id or new_item_id:
            if not new_item_id:
                new_id = cls.next_available_datanode_id()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_item_id
            #print("New ID assigned to new data node: ", new_id)
            cypher_prop_dict["item_id"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                cypher_prop_dict["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of cypher_prop_dict at this stage:
            #       {"make": "Toyota", "color": "white", "item_id": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned item_id


        # Create a new data node, with a "SCHEMA" relationship to its Class node and, possible, also relationships to another data nodes
        link_to_schema_class = {"internal_id": class_internal_id, "rel_name": "SCHEMA", "rel_dir": "OUT"}
        if links:
            links.append(link_to_schema_class)
        else:
            links = [link_to_schema_class]

        neo_id = cls.db.create_node_with_links(labels=labels,
                                               properties=cypher_prop_dict,
                                               links=links)
        return neo_id



    @classmethod
    def add_data_point_fast_OBSOLETE(cls, class_name="", schema_id=None,
                                     properties=None, labels=None,
                                     connected_to_neo_id=None, rel_name=None, rel_dir="OUT", rel_prop_key=None, rel_prop_value=None,
                                     assign_item_id=False, new_item_id=None) -> int:
        """
        TODO: OBSOLETED BY add_data_node_with_links() - TO DITCH *AFTER* add_data_node_with_links() gets link validation!
        A faster version of add_data_point()
        Add a new data node, of the Class specified by name or ID,
        with the given (possibly none) attributes and label(s),
        optionally linked to another, already existing, DATA node.

        The new data node, if successfully created, will be assigned a unique value for its field item_id
        If the requested Class doesn't exist, an Exception is raised

        NOTE: if the new node requires MULTIPLE links to existing data points, use add_and_link_data_point() instead

        EXAMPLES:   add_data_point(class_name="Cars", data_dict={"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     data_dict={"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with item_id = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param properties:      An optional dictionary with the properties of the new data point.   TODO: NEW - changed name
                                    EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to the new data node;
                                    if not specified, use the Class name

        :param connected_to_neo_id: Int or None.  To optionally specify another (already existing) DATA node
                                        to connect the new node to, specified by its Neo4j
                                        EXAMPLE: the item_id of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param assign_item_id:  If True, the new node is given an extra attribute named "item_id" with a unique auto-increment value
        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                    If new_item_id is provided, then assign_item_id is automatically made True

        :return:                If successful, an integer with the Neo4j ID
                                    of the node just created;
                                    otherwise, an Exception is raised
        """
        #print(f"In add_data_point().  rel_name: `{rel_name}` | rel_prop_key: `{rel_prop_key}` | rel_prop_value: {rel_prop_value}")

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("NeoSchema.add_data_point(): Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name(schema_id)      # Derive the Class name from its ID

        class_neo_id = cls.get_class_internal_id(class_name)

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if properties is None:
            properties = {}

        assert type(properties) == dict, "NeoSchema.add_data_point(): The properties argument, if provided, MUST be a dictionary"

        cypher_prop_dict = properties

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"NeoSchema.add_data_point(): Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes: "item_id" and "schema_code";
        # if requested, expand cypher_prop_dict accordingly
        if assign_item_id or new_item_id:
            if not new_item_id:
                new_id = cls.next_available_datanode_id()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_item_id
            #print("New ID assigned to new data node: ", new_id)
            cypher_prop_dict["item_id"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                cypher_prop_dict["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of cypher_prop_dict at this stage:
            #       {"make": "Toyota", "color": "white", "item_id": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned item_id


        # Create a new data node, with a "SCHEMA" relationship to its Class node and, if requested, also a relationship to another data node
        if connected_to_neo_id:     # if requesting a relationship to an existing data node
            if rel_prop_key and (rel_prop_value != '' and rel_prop_value is not None):  # Note: cannot just say "and rel_prop_value" or it'll get dropped if zero
                rel_attrs = {rel_prop_key: rel_prop_value}
            else:
                rel_attrs = None

            neo_id = cls.db.create_node_with_links(labels,
                                                   properties=cypher_prop_dict,
                                                   links=[  {"internal_id": class_neo_id,
                                                             "rel_name": "SCHEMA", "rel_dir": "OUT"},

                                                            {"internal_id": connected_to_neo_id,
                                                             "rel_name": rel_name, "rel_dir": rel_dir, "rel_attrs": rel_attrs}
                                                            ]
                                                   )
        else:                   # Simpler case : only a link to the Class node
            neo_id = cls.db.create_node_with_links(labels,
                                                   properties=cypher_prop_dict,
                                                   links=[{"internal_id": class_neo_id,
                                                            "rel_name": "SCHEMA", "rel_dir": "OUT"}
                                                          ]
                                                   )

        return neo_id



    @classmethod
    def add_data_point_OLD(cls, class_name="", schema_id=None,
                           data_dict=None, labels=None,
                           connected_to_id=None, connected_to_labels=None, rel_name=None, rel_dir="OUT", rel_prop_key=None, rel_prop_value=None,
                           new_item_id=None, return_item_ID=True) -> int:   # TODO: OBSOLETE.  Replace by add_data_node_with_links()
                                                                        # TO DITCH *AFTER* add_data_node_with_links() gets link validation!
        """
        Add a new data node, of the Class specified by name or ID,
        with the given (possibly none) attributes and label(s),
        optionally linked to another DATA node, already existing.

        The new data node, if successfully created, will be assigned a unique value for its field item_id
        If the requested Class doesn't exist, an Exception is raised

        EXAMPLES:   add_data_point(class_name="Cars", data_dict={"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     data_dict={"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with item_id = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable
        TODO: make the issuance of a new item_id optional

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param data_dict:       An optional dictionary with the properties of the new data point.
                                TODO: a better name might be "properties"
                                    EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to the new data node;
                                    if not specified, use the Class name.  TODO: the Class name ought to ALWAYS be added

        :param connected_to_id: Int or None.  To optionally specify another (already existing) DATA node
                                        to connect the new node to, specified by its item_id.
                                        TODO: --> for efficiency, use the Neo4j ID instead [and ditch the arg "connected_to_labels"]
                                        EXAMPLE: the item_id of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param connected_to_labels:     EXAMPLE: "salesperson"
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
        :param return_item_ID:  Default to True.    TODO: change to False
                                If True, the returned value is the auto-increment "item_id" value of the node just created;
                                    otherwise, it returns its Neo4j ID

        :return:                If successful, an integer with either the auto-increment "item_id" value or the Neo4j ID
                                    of the node just created (based on the flag "return_item_ID");
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

        if data_dict is None:
            data_dict = {}

        assert type(data_dict) == dict, "The data_dict argument, if provided, MUST be a dictionary"

        cypher_props_dict = data_dict

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes contain 2 special attributes: "item_id" and "schema_code";
        # expand cypher_props_dict accordingly
        # TODO: make this part optional
        if not new_item_id:
            new_id = cls.next_available_datanode_id()      # Obtain (and reserve) the next auto-increment value
        else:
            new_id = new_item_id
        #print("New ID assigned to new data node: ", new_id)
        cypher_props_dict["item_id"] = new_id               # Expand the dictionary

        schema_code = cls.get_schema_code(class_name)       # TODO: this may slow down execution
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

            neo_id = cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"},

                                                               {"labels": connected_to_labels, "key": "item_id", "value": connected_to_id,
                                                                "rel_name": rel_name, "rel_dir": rel_dir, "rel_attrs": rel_attrs}
                                                               ]
                                                  )
        else:                   # simpler case : only a link to the Class node
            neo_id = cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"}]
                                                  )

        if return_item_ID:
            return new_id
        else:
            return neo_id



    @classmethod
    def add_and_link_data_point_OBSOLETE(cls, class_name: str, connected_to_list: [tuple], properties=None, labels=None,
                                         assign_item_id=False) -> int:
        """
        TODO: OBSOLETED BY add_data_node_with_links() - TO DITCH *AFTER* add_data_node_with_links() gets link validation!
        Create a new data node, of the Class with the given name,
        with the specified optional labels and properties,
        and link it to each of all the EXISTING nodes
        specified in the (possibly empty) list connected_to_list,
        using the various relationship names specified inside that list.

        All the relationships are understood to be OUTbound from the newly-created node -
        and they must be present in the Schema, or an Exception will be raised.

        If the requested Class doesn't exist, an Exception is raised

        The new data node optionally gets assigned a unique "item_id" value (TODO: make optional)

        EXAMPLE:
            add_and_link_data_point(
                                class_name="PERSON",
                                properties={"name": "Julian", "city": "Berkeley"},
                                connected_to_list=[ (123, "IS_EMPLOYED_BY") , (456, "OWNS") ]
            )

        Note: this is the Schema layer's counterpart of NeoAccess.create_node_with_children()

        :param class_name:          Name of the Class specifying the schema for this new data point
        :param connected_to_list:   A list of pairs (Neo4j ID value, relationship name)
        :param properties:          A dictionary of attributes to give to the new node
        :param labels:              OPTIONAL string or list of strings with label(s) to assign to new data node;
                                        if not specified, use the Class name
        :param assign_item_id:      If True, the new node is given an extra attribute named "item_id" with a unique auto-increment value

        :return:                    If successful, an integer with Neo4j ID of the node just created;
                                        otherwise, an Exception is raised
        """
        new_neo_id = cls.add_data_point_fast_OBSOLETE(class_name=class_name, properties=properties, labels=labels,
                                                      assign_item_id=assign_item_id)
        # TODO: maybe expand add_data_point_fast(), so that it can link to multiple other data nodes at once
        for link in connected_to_list:
            node_neo_id, rel_name = link    # Unpack
            cls.add_data_relationship(from_id=new_neo_id, to_id=node_neo_id, rel_name=rel_name)

        return new_neo_id



    @classmethod
    def register_existing_data_node(cls, class_name="", schema_id=None,
                                    existing_neo_id=None, new_item_id=None) -> int:
        """
        Register (declare to the Schema) an existing data node with the Schema Class specified by its name or ID.
        An item_id is generated for the data node and stored on it; likewise, for a schema_code (if applicable).
        Return the newly-assigned item_id

        EXAMPLES:   register_existing_data_node(class_name="Chemicals", existing_neo_id=123)
                    register_existing_data_node(schema_id=19, existing_neo_id=456)

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data node is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param existing_neo_id: Internal ID to identify the node to register with the above Class.
                                TODO: expand to use the match() structure
        :param new_item_id:     OPTIONAL. Normally, the Item ID is auto-generated,
                                but it can also be provided (Note: MUST be unique)

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

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Verify that the data node doesn't already have a SCHEMA relationship
        q = f'''
            MATCH (n)-[:SCHEMA]->(:CLASS) WHERE id(n)={existing_neo_id} RETURN count(n) AS number_found
            '''
        number_found = cls.db.query(q, single_cell="number_found")
        if number_found:
            raise Exception(f"The given data node ALREADY has a SCHEMA relationship")

        if not new_item_id:
            new_item_id = cls.next_available_datanode_id()     # Generate, if not already provided

        cls.debug_print("register_existing_data_node(). New item_id to be assigned to the data node: ", new_item_id)

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

        cls.db.debug_query_print(q, data_binding, "register_existing_data_node") # Note: this is the special debug print for NeoAccess
        result = cls.db.update_query(q, data_binding)
        #print(result)

        number_new_rels = result.get('relationships_created')   # This ought to be 1
        if number_new_rels != 1:
            raise Exception("Failed to created the new relationship (`SCHEMA`)")

        return new_item_id



    @classmethod
    def delete_data_node(cls, node_id=None, uri=None, class_node=None, labels=None) -> None:
        """
        Delete the given data node.
        If no node gets deleted, or if more than 1 get deleted, an Exception is raised

        :param node_id:     An integer with the internal database ID of an existing data node
        :param uri:         An alternate way to refer to the node.  TODO: implement
        :param class_node:  NOT IN CURRENT USE.  Specify the Class to which this node belongs TODO: implement
        :param labels:      (OPTIONAL) String or list of strings.
                                If passed, each label must be present in the node, for a match to occur
                                (no problem if the node also includes other labels not listed here.)
                                Generally, redundant, as a precaution against deleting wrong node
        :return:            None
        """
        # Validate arguments
        CypherUtils.assert_valid_internal_id(node_id)

        cypher_labels = CypherUtils.prepare_labels(labels)

        q = f'''
            MATCH (:CLASS)<-[:SCHEMA]-(data {cypher_labels})
            WHERE id(data) = $node_id
            DETACH DELETE data
            '''
        #print(q)
        stats = cls.db.update_query(q, data_binding={"node_id": node_id})

        number_nodes_deleted = stats.get("nodes_deleted", 0)

        if number_nodes_deleted == 0:
            raise Exception("delete_data_node(): nothing was deleted")
        elif number_nodes_deleted > 1:
            raise Exception(f"delete_data_node(): more than 1 node was deleted.  Number deleted: {number_nodes_deleted}")



    @classmethod
    def delete_data_point(cls, item_id: int, labels=None) -> int:
        """
        Delete the given data point.  TODO: obsolete in favor of delete_data_node()

        :param item_id:
        :param labels:      OPTIONAL (generally, redundant)
        :return:            The number of nodes deleted (possibly zero)
        """
        match = cls.db.match(key_name="item_id", key_value=item_id, properties={"schema_code": "cat"},
                            labels=labels)
        return cls.db.delete_nodes(match)



    @classmethod
    def add_data_relationship_OLD(cls, from_id: Union[int, str], to_id: Union[int, str], rel_name: str, rel_props = None,
                                  labels_from=None, labels_to=None, id_type=None) -> None:
        """
        -> Maybe not really needed.  IF POSSIBLE, USE add_data_relationship() INSTEAD
        TODO: possibly ditch, in favor of add_data_relationship()

        Add a new relationship with the given name, from one to the other of the 2 given DATA nodes.
        The new relationship must be present in the Schema, or an Exception will be raised.

        The data nodes may be identified either by their Neo4j ID's, or by a primary key (with optional label.)

        Note that if a relationship with the same name already exists between the data nodes exists,
        nothing gets created (and an Exception is raised)

        :param from_id:     The ID of the data node at which the new relationship is to originate;
                                this is understood be the Neo4j ID, unless an id_type is specified
        :param to_id:       The ID of the data node at which the new relationship is to end;
                                this is understood be the Neo4j ID, unless an id_type is specified
        :param rel_name:    The name to give to the new relationship between the 2 specified data nodes
        :param rel_props:   TODO: not currently used.  Unclear what multiple calls would do in this case
        :param labels_from: (OPTIONAL) Labels on the 1st data node
        :param labels_to:   (OPTIONAL) Labels on the 2nd data node
        :param id_type:     For example, "item_id";
                            if not specified, all the node ID's are assumed to be Neo4j ID's

        :return:            None.  If the specified relationship didn't get created (for example,
                            in case the the new relationship doesn't exist in the Schema), raise an Exception
        """
        assert rel_name, f"add_data_relationship(): no name was provided for the new relationship"

        # Create "CypherMatch" objects later used to locate the two data node
        from_match = NeoSchema.locate_node(node_id=from_id, id_type=id_type, labels=labels_from, dummy_node_name="from")
        to_match   = NeoSchema.locate_node(node_id=to_id,   id_type=id_type, labels=labels_to,   dummy_node_name="to")

        # Get Cypher fragments related to matching the data nodes
        from_node = from_match.node
        to_node = to_match.node
        where_clause = CypherUtils.combined_where(from_match, to_match, check_compatibility=True)
        data_binding = CypherUtils.combined_data_binding(from_match, to_match)

        # Using the Cypher fragments from above, create a query that looks for a path
        # from the first to the second data nodes, passing thru their classes
        # and thru a link with the same relationship name between those classes;
        # upon finding such a path, join the data nodes with a relationship
        q = f'''
            MATCH   {from_node} 
                    -[:SCHEMA]-> (from_class :CLASS)-[:{rel_name}]->(to_class :CLASS) <-[:SCHEMA]- 
                    {to_node}
            {where_clause}
            MERGE (from)-[:{rel_name}]->(to)
            '''

        result = cls.db.update_query(q, data_binding)
        number_relationships_added = result.get("relationships_created", 0)   # If field isn't present, return a 0

        if number_relationships_added != 1:
            # The following 2 lines will raise an Exception if either data node doesn't exist or lacks a Class
            class_from = cls.class_of_data_node(node_id=from_id, id_type=id_type, labels=labels_from)
            class_to = cls.class_of_data_node(node_id=to_id, id_type=id_type, labels=labels_to)

            #TODO: maybe double-check that the following reported problem is indeed what caused the failure <-- INDEED, DO THAT!
            raise Exception(f"add_data_relationship(): cannot add the relationship `{rel_name}` between the data nodes, "
                            f"because no such relationship exists from Class `{class_from}` to Class `{class_to}`. "
                            f"The Schema needs to be modified first")



    @classmethod
    def add_data_relationship(cls, from_id:int, to_id: int, rel_name: str, rel_props = None) -> None:
        """
        Simpler (and possibly faster) version of add_data_relationship()

        Add a new relationship with the given name, from one to the other of the 2 given data nodes,
        identified by their Neo4j ID's.
        The requested new relationship MUST be present in the Schema, or an Exception will be raised.

        Note that if a relationship with the same name already exists between the data nodes exists,
        nothing gets created (and an Exception is raised)

        :param from_id: The Neo4j ID of the data node at which the new relationship is to originate
                                TODO: also allow primary keys, as done in class_of_data_node()
        :param to_id:   The Neo4j ID of the data node at which the new relationship is to end
                                TODO: also allow primary keys, as done in class_of_data_node()
        :param rel_name:    The name to give to the new relationship between the 2 specified data nodes
                                IMPORTANT: it MUST match an existing relationship in the Schema,
                                           between the respective Classes of the 2 data nodes
        :param rel_props:   TODO: not currently used.  Unclear what multiple calls would do in this case

        :return:            None.  If the specified relationship didn't get created (for example,
                                in case the the new relationship doesn't exist in the Schema), raise an Exception
        """
        assert rel_name, f"NeoSchema.add_data_relationship(): no name was provided for the new relationship"

        # Create a query that looks for a path
        # from the first to the second data nodes, passing thru their classes
        # and thru a link with the requested new relationship name between those classes;
        # upon finding such a path, join the data nodes with a relationship
        q = f'''
            MATCH   (from_node) -[:SCHEMA]-> (from_class :CLASS)
                    -[:`{rel_name}`]->
                    (to_class :CLASS) <-[:SCHEMA]- (to_node)
            WHERE id(from_node) = $from_neo_id AND id(to_node) = $to_neo_id
            MERGE (from_node)-[:`{rel_name}`]->(to_node)
            '''

        result = cls.db.update_query(q, {"from_neo_id": from_id, "to_neo_id": to_id})
        number_relationships_added = result.get("relationships_created", 0)   # If key isn't present, use a value of 0

        if number_relationships_added != 1:
            # The following 2 lines will raise an Exception if either data node doesn't exist or lacks a Class
            class_from = cls.class_of_data_node(node_id=from_id)
            class_to = cls.class_of_data_node(node_id=to_id)

            # TODO: double-check that the following reported problem is indeed what caused the failure
            raise Exception(f"NeoSchema.add_data_relationship(): Cannot add the relationship `{rel_name}` between the data nodes, "
                            f"because no such relationship exists from Class `{class_from}` to Class` {class_to}`. "
                            f"The Schema needs to be modified first")



    @classmethod
    def remove_data_relationship(cls, from_item_id: int, to_item_id: int, rel_name: str, labels=None) -> None:
        """
        Drop the relationship with the given name, from one to the other of the 2 given data nodes.
        Note: the data nodes are left untouched.
        If the specified relationship didn't get deleted, raise an Exception

        TODO: first verify that the relationship is optional in the schema???
        TODO: migrate from "item_id" values to also internal database ID's, as done in class_of_data_node()

        :param from_item_id:The "item_id" value of the data node at which the relationship originates
        :param to_item_id:  The "item_id" value of the data node at which the relationship ends
        :param rel_name:    The name of the relationship to delete
        :param labels:      OPTIONAL (generally, redundant).  Labels required to be on both nodes

        :return:            None.  If the specified relationship didn't get deleted, raise an Exception
        """
        assert rel_name != "", f"remove_data_relationship(): no name was provided for the relationship"

        match_from = cls.db.match(labels=labels, key_name="item_id", key_value=from_item_id,
                                  dummy_node_name="from")

        match_to =   cls.db.match(labels=labels, key_name="item_id", key_value=to_item_id,
                                  dummy_node_name="to")

        cls.db.remove_links(match_from, match_to, rel_name=rel_name)   # This will raise an Exception if no relationship is removed



    @classmethod
    def remove_multiple_data_relationships(cls, node_id: Union[int, str], rel_name: str, rel_dir: str, labels=None) -> None:
        """     TODO: test
        Drop all the relationships with the given name, from or to the given data node.
        Note: the data node is left untouched.

        IMPORTANT: this function cannot be used to remove relationship involving any Schema node

        :param node_id:     The internal database ID or name of the data node of interest
        :param rel_name:    The name of the relationship(s) to delete
        :param rel_dir:     Either 'IN', 'OUT', or 'BOTH'
        :param labels:      [OPTIONAL]
        :return:            None
        """
        assert rel_name, \
                f"remove_data_relationship(): no name was provided for the relationship to be removed"

        assert (rel_name != "SCHEMA") and (rel_name != "HAS_PROPERTY"), \
                f"remove_data_relationship(): cannot use this function to remove Schema relationships"

        if labels is None:
            labels = ""
        else:
            labels = f":`{labels}`"

        if rel_dir == "OUT":
            match = f"MATCH (n) -[r :{rel_name}]->({labels})"
        elif rel_dir == "IN":
            match = f"MATCH (n) <-[r :{rel_name}]-({labels})"
        elif rel_dir == "BOTH":
            match = f"MATCH (n) -[r :{rel_name}]-({labels})"
        else:
            raise Exception("remove_data_relationship(): the argument `rel_dir` must be either 'IN', 'OUT', or 'BOTH'")

        if type(node_id) == int:
            q = f'''
            {match} WHERE labels(n) <> ["CLASS", "PROPERTY" ]
            AND id(n) = {node_id}
            DELETE r
            '''
        else:
            q = f'''
            {match} WHERE labels(n) <> ["CLASS", "PROPERTY" ]
            AND n.name = "{node_id}"
            DELETE r
            '''

        #print(q)
        cls.db.update_query(q)



    @classmethod
    def class_of_data_node(cls, node_id: int, id_type=None, labels=None) -> str:
        """
        Return the name of the Class of the given data node: identified
        either by its Neo4j ID (default), or by a primary key (with optional label)

        :param node_id:     Either an internal database ID or a primary key value
        :param id_type:     OPTIONAL - name of a primary key used to identify the data node
        :param labels:      Optional string, or list/tuple of strings, with Neo4j labels
        :return:            A string with the name of the Class of the given data node
        """
        match = NeoSchema.locate_node(node_id=node_id, id_type=id_type, labels=labels)
        # This is an object of type "CypherMatch"

        node = match.node
        where_clause = CypherUtils.prepare_where([match.where])
        data_binding = match.data_binding

        q = f'''
            MATCH  {node} -[:SCHEMA]-> (class_node :CLASS)
            {where_clause}
            RETURN class_node.name AS name
            '''
        cls.db.debug_query_print(q, data_binding, "class_of_data_node")

        result = cls.db.query(q, data_binding)

        if len(result) == 0:    # TODO: separate the 2 scenarios leading to this
            raise Exception(f"The given data node (id: {node_id}) does not exist or is not associated to any schema class")
        elif len(result) > 1:
            raise Exception(f"The given data node (id: {node_id}) is associated to more than 1 schema class (forbidden scenario)")

        class_node = result[0]

        if "name" not in class_node:
            raise Exception("The associate schema class node lacks a name")

        return class_node["name"]


    @classmethod
    def data_nodes_lacking_schema(cls):
        """
        Locate and return all Data Nodes that aren't associated to any Class
        TODO: generalize the "BA" label
        TODO: test

        :return:
        """
        q = '''
            MATCH  (n:BA)
            WHERE  not exists ( (n)-[:SCHEMA]-> (:CLASS) )
            RETURN n
            '''

        return cls.db.query(q)



    @classmethod
    def get_data_node_id(cls, key_value, key_name="item_id") -> int:
        """
        Get the internal database ID of a data node given some other primary key

        :return:   An integer with the Neo4j ID of the data node
        """

        match = cls.db.match(key_name=key_name, key_value=key_value)
        result = cls.db.get_nodes(match, return_internal_id=True, single_cell="internal_id")

        if result is None:
            raise Exception(f"get_data_node_id(): unable to find a data node with the attribute `{key_name}={key_value}`")

        return result




    #####################################################################################################

    '''                                      ~   DATA IMPORT   ~                                       '''

    def ________DATA_IMPORT________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def import_json_data(cls, json_str: str, class_name: str, parse_only=False, provenance=None) -> Union[None, int, List[int]]:
        """
        Import the data specified by a JSON string into the database -
        but only the data that is described in the existing Schema;
        anything else is silently ignored.

        CAUTION: A "postorder" approach is followed: create subtrees first (with recursive calls), then create the root last;
        as a consequence, in case of failure mid-import, there's no top root, and there could be several fragments.
        A partial import might need to be manually deleted.
        TODO: maintain a list of all created nodes - so as to be able to delete them all in case of failure.

        :param json_str:    A JSON string representing (at the top level) an object or a list to import
        :param class_name:  Name of Schema class to use for the top-level element(s)
        :param parse_only:  Flag indicating whether to stop after the parsing (i.e. no database import)
        :param provenance:  Metadata (such as a file name) to store in the "source" attribute
                                of a special extra node ("Import Data")

        :return:
        """
        cls.debug_print(f"In import_json_data().  class_name: {class_name} | parse_only: {parse_only} | provenance: {provenance}")
        # Try to obtain Python data (which ought to be a dict or list) that corresponds to the passed JSON string
        try:
            python_data_from_json = json.loads(json_str)    # Turn the string (representing JSON data) into its Python counterpart;
                                                            # at the top level, it should be a dict or list
        except Exception as ex:
            raise Exception(f"Incorrectly-formatted JSON string. {ex}")

        #print("Python version of the JSON file:\n", python_data_from_json)     # A dictionary

        if parse_only:
            return      # Nothing else to do

        return cls.create_data_nodes_from_python_data(python_data_from_json, class_name, provenance)



    @classmethod
    def create_data_nodes_from_python_data(cls, data, class_name: str, provenance=None) -> [int]:
        """
        Import the data specified by the "data" python structure into the database -
        but only the data that is described in the existing Schema;
        anything else is silently ignored.
        For additional notes, see import_json_data()

        :param data:        A python dictionary or list, with the data to import
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param provenance:  Optional string to be stored in a "source" attribute
                                in a special "Import Data" node for metadata about the import

        :return:            List (possibly empty) of Neo4j ID's of the root node(s) created

        TODO:   * The "Import Data" Class must already be in the Schema; should automatically add it, if not already present
                * DIRECTION OF RELATIONSHIP (cannot be specified by Python dict/JSON)
                * LACK OF "Import Data" node (ought to be automatically created if needed)
                * LACK OF "BA" (or "DATA"?) labels being set
                * INABILITY TO LINK TO EXISTING NODES IN DBASE (try using: "item_id": some_int  as the only property in nodes to merge)
                * HAZY responsibility for "schema_code" (set correctly for all nodes); maybe ditch to speed up execution
                * OFFER AN OPTION TO IGNORE BLANK STRINGS IN ATTRIBUTES
                * INTERCEPT AND BLOCK IMPORTS FROM FILES ALREADY IMPORTED
                * issue some report about any part of the data that doesn't match the Schema, and got silently dropped
        """

        # Create a special `Import Data` node for the metadata of the import
        import_metadata = {}
        if provenance:
            import_metadata["source"] = provenance

        metadata_neo_id = cls.add_data_node_with_links(class_name="Import Data", properties=import_metadata)

        # Store the import date in the node with the metadata
        # Note: this is done as a separate step, so that the attribute will be a DATE (""LocalDate") field, not a text one
        q = f'''
            MATCH (n :`Import Data`) WHERE id(n) = {metadata_neo_id}
            SET n.date = date()
            '''
        cls.db.update_query(q)

        # TODO: catch Exceptions, and store the status and error message on the `Import Data` node;
        #       in particular, add "Import Data" to the Schema if not already present

        cache = SchemaCache()        # All needed Schema-related data will be automatically queried and cached here
        print("***************************** cache initialized ***************************** ")

        if type(data) == dict:      # If the top-level Python data structure is a dictionary
            # Create a single tree
            cls.debug_print("Top-level structure of the data to import is a Python dictionary")
            # Perform the import
            root_neo_id = cls.create_tree_from_dict(data, class_name, cache=cache) # This returns a Neo4j ID, or None

            if root_neo_id is None:
                cls.debug_print("None returned by create_tree_from_dict()")
                return []               # Zero new nodes were imported
            else:
                cls.debug_print(f"***Linking import node (Neo4j ID={metadata_neo_id}) with "
                                f"data root node (Neo4j ID={root_neo_id}), thru relationship `imported_data`")
                # Connect the root of the import to the metadata node
                cls.add_data_relationship(from_id=metadata_neo_id, to_id=root_neo_id, rel_name="imported_data")
                return [root_neo_id]

        elif type(data) == list:         # If the top-level Python data structure is a list
            # Create multiple unconnected trees
            cls.debug_print("Top-level structure of the data to import is a list")
            node_id_list = cls.create_trees_from_list(data, class_name, cache=cache)  # This returns a list of Neo4j ID's

            for root_item_id in node_id_list:
                cls.debug_print(f"***Linking import node (item_id={metadata_neo_id}) with "
                                f"data root node (Neo4j ID={root_item_id}), thru relationship `imported_data`")
                # Connect the root of the import to the metadata node
                cls.add_data_relationship(from_id=metadata_neo_id, to_id=root_item_id, rel_name="imported_data")

            return node_id_list

        else:                           # If the top-level data structure is neither a list nor a dictionary
            raise Exception(f"The top-level structure is neither a list nor a dictionary; instead, it's {type(data)}")



    @classmethod
    def create_tree_from_dict(cls, d: dict, class_name: str, level=1, cache=None) -> Union[int, None]:
        """
        Add a new data node (which may turn into a tree root) of the specified Class,
        with data from the given dictionary:
            1) literal values in the dictionary are stored as attributes of the node, using the keys as names
            2) other values (such as dictionaries or lists) are recursively turned into subtrees,
               linked from the new data node through outbound relationships using the dictionary keys as names

        Return the Neo4j ID of the newly created root node,
        or None is nothing is created (this typically arises in recursive calls that "skip subtrees")

        IMPORTANT:  any part of the data that doesn't match the Schema,
                    gets silently dropped.  TODO: issue some report about that

        EXAMPLES:
        (1) {"state": "California", "city": "Berkeley"}
            results in the creation of a new node, with 2 attributes, named "state" and "city"

        (2) {"name": "Julian", "address": {"state": "California", "city": "Berkeley"}}
            results in the creation of 2 nodes, namely the tree root (with a single attribute "name"), with
            an outbound link named "address" to another node (the subtree) that has the "state" and "city" attributes

        (3) {"headquarter_state": [{"state": "CA"}, {"state": "NY"}, {"state": "FL"}]}
            results in the creation of a node (the tree root), with no attributes, and 3 links named "headquarter_state" to,
            respectively, 3 nodes - each of which containing a "state" attribute

        (4) {"headquarter_state": ["CA", "NY", "FL"]}
            similar to (3), above, but the children nodes will use the default attribute name "value"

        :param d:           A dictionary with data from which to create a tree in the database
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param level:       The level of the recursive call (used for debug printing)
        :return:            The Neo4j ID of the newly created node,
                                or None is nothing is created (this typically arises in recursive calls that "skip subtrees")
        """
        assert cache is not None, "NeoSchema.create_tree_from_dict(): the argument `cache` cannot be None"
        assert type(d) == dict, f"NeoSchema.create_tree_from_dict(): the argument `d` must be a dictionary (instead, it's {type(d)})"

        #schema_id = cls.get_class_id(class_name)
        #assert schema_id != -1, \
        #            f"The value passed for the argument `class_name` ({class_name}) is not a valid Class name"  # If not found


        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")

        class_internal_id = NeoSchema.get_class_internal_id(class_name=class_name)

        cls.debug_print(f"{indent_str}Importing data dictionary, using class `{class_name}` (with internal id {class_internal_id})")

        # Determine the properties and relationships declared in (allowed by) the Schema
        #cached_data = cache_old.get_class_cached_data(class_name)
        #declared_outlinks = cached_data['out_links']
        out_neighbors_dict = cache.get_cached_class_data(class_internal_id, request="out_neighbors")
        declared_outlinks = list(out_neighbors_dict)    # Extract keys from dict
        cls.debug_print(f"{indent_str}declared_outlinks: {declared_outlinks}")


        #declared_properties = cached_data['properties']
        declared_properties = cache.get_cached_class_data(class_internal_id, request="class_properties")
        cls.debug_print(f"{indent_str}declared_properties: {declared_properties}")

        cls.debug_print(f"{indent_str}Input is a dict with {len(d)} keys: {list(d.keys())}")
        node_properties = {}
        children_info = []          # A list of pairs (Neo4j ID value, relationship name)

        skipped_properties = []
        skipped_relationships = []

        # Loop over all the dictionary entries
        for k, v in d.items():
            debug_info = f"{indent_str}*** KEY-> VALUE: {k} -> {v}"
            cls.debug_print(debug_info, trim=True)      # Abridge the info line if excessively long

            if v is None:
                cls.debug_print(f"{indent_str}Disregarding attribute (`{k}`) that has a None value")
                skipped_properties.append(k)
                continue

            if cls.db.is_literal(v):
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a literal of type {type(v)} ({v})",
                                trim=True)
                if k not in declared_properties:    # Check if the Property from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected attribute: `{k}`")
                    skipped_properties.append(k)
                    continue
                else:
                    node_properties[k] = v                  # Save attribute for use when the node gets created
                    cls.debug_print(f"{indent_str}Buffered properties for the new node so far: {node_properties}",
                                    trim=True)

            elif type(v) == dict:
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a dictionary (with {len(v)} keys)")

                if k not in declared_outlinks:       # Check if the Relationship from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected relationship: `{k}`")
                    skipped_relationships.append(k)
                    continue

                cls.debug_print(f"{indent_str}Examining the relationship `{k}`...")

                try:
                    # Locate which Class one finds in the Schema when following the relationship name stored in k
                    #subtree_root_class_name = cached_data['out_neighbors'][k]
                    subtree_root_class_name = out_neighbors_dict[k]
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above dictionary...")
                new_node_neo_id = cls.create_tree_from_dict(d=v, class_name=subtree_root_class_name, level=level + 1, cache=cache)

                if new_node_neo_id is not None:     # If a subtree actually got created
                    children_info.append( (new_node_neo_id, k) )    # Save relationship name (in k) for use when the node gets created
                    cls.debug_print(f"{indent_str}Buffered relationships for the new node so far: {children_info}")
                else:
                    cls.debug_print(f"{indent_str}No subtree was returned; so, skipping over this key (`{k}`)")

            elif type(v) == list:
                cls.debug_print(f"{indent_str}(key: `{k}`) Processing a list (with {len(v)} elements):")

                if k not in declared_outlinks:       # Check if the Relationship from the data is in the schema
                    cls.debug_print(f"{indent_str}Disregarding this unexpected relationship: `{k}`")
                    skipped_relationships.append(k)
                    continue

                if len(v) == 0:
                    cls.debug_print(f"{indent_str}The list is empty; so, ignoring it")
                    continue

                cls.debug_print(f"{indent_str}Examining the relationship `{k}`...")

                try:
                    # Locate which Class one finds in the Schema when following the relationship name stored in k
                    #subtree_root_class_name = cached_data['out_neighbors'][k]
                    subtree_root_class_name = out_neighbors_dict[k]
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above list...")
                new_node_id_list = cls.create_trees_from_list(l=v, class_name=subtree_root_class_name, level=level + 1, cache=cache)
                for child_id in new_node_id_list:
                    children_info.append( (child_id, k) )

            else:
                raise Exception(f"Unexpected type: {type(v)}")

        # End of loop over all the dictionary entries

        # A "postorder" approach is followed: the subtrees were created first (with recursive calls);
        # now, finally CREATE THE NEW NODE, the ROOT, with its attributes
        # and links to the previously-created children (the roots of all the sub-trees)
        if len(node_properties) == 0 and len(children_info) == 0:
            cls.debug_print(f"{indent_str}Skipping creating node of class `{class_name}` that has no properties and no children")
            return None   # Using None to indicate "skipped node/subtree"
        else:
            links = [{"internal_id": child[0], "rel_name": child[1], "rel_dir": "OUT"}
                            for child in children_info]
            # Note: a Neo4j ID is returned by the next call
            #return cls.add_data_node_with_links(class_internal_id=cached_data['neo_id'],
            return cls.add_data_node_with_links(class_internal_id=class_internal_id,
                                                labels=class_name,
                                                properties=node_properties,
                                                links=links,
                                                assign_item_id=False)



    @classmethod
    def create_trees_from_list(cls, l: list, class_name: str, level=1, cache=None) -> [int]:
        """
        Add a set of new data nodes (the roots of the trees), all of the specified Class,
        with data from the given list.
        Each list elements MUST be a literal, or dictionary or a list:
            - if a literal, it first gets turned into a dictionary of the form {"value": literal_element};
            - if a dictionary, it gets processed by create_tree_from_dict()
            - if a list, it generates a recursive call

        Return a list of the Neo4j ID of the newly created nodes.

        IMPORTANT:  any part of the data that doesn't match the Schema,
                    gets silently dropped.  TODO: issue some report about that

        EXAMPLE:
            If the Class is named "address" and has 2 properties, "state" and "city",
            then the data:
                    [{"state": "California", "city": "Berkeley"},
                     {"state": "Texas", "city": "Dallas"}]
            will give rise to 2 new data nodes with label "address", and each of them having a "SCHEMA"
            link to the shared Class node.

        :param l:           A list of data from which to create a set of trees in the database
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param level:       The level of the recursive call (used for debug printing)

        :return:            A list of the Neo4j values of the newly created nodes (each of which
                                might be a root of a tree)
        """
        assert type(l) == list, f"NeoSchema.create_trees_from_list(): the argument `l` must be a list (instead, it's {type(l)})"
        assert cache is not None, "NeoSchema.create_trees_from_list(): the argument `cache` cannot be None"

        #assert cls.class_name_exists(class_name), \
                #f"The value passed for the argument `class_name` ({class_name}) is not a valid Class name"

        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")

        cls.debug_print(f"{indent_str}Input is a list with {len(l)} items")

        list_of_root_neo_ids = []

        # Process each element of the list, in turn
        for i, item in enumerate(l):
            cls.debug_print(f"{indent_str}Processing the {i}-th list element...")
            if cls.db.is_literal(item):
                item_as_dict = {"value": item}
                new_node_id = cls.create_tree_from_dict(d=item_as_dict, class_name=class_name, level=level + 1, cache=cache)
                if new_node_id is not None:                      # If a subtree actually got created
                    list_of_root_neo_ids.append(new_node_id)

            elif type(item) == dict:
                new_node_id = cls.create_tree_from_dict(d=item, class_name=class_name, level=level + 1, cache=cache)
                if new_node_id is not None:                     # If a subtree actually got created
                    list_of_root_neo_ids.append(new_node_id)

            elif type(item) == list:
                cls.debug_print(f"{indent_str}Making recursive call")
                new_node_id_list = cls.create_trees_from_list(l=item, class_name=class_name, level=level + 1, cache=cache)   # Recursive call
                list_of_root_neo_ids += new_node_id_list        # Merge of lists

            else:
                raise Exception(f"NeoSchema.create_trees_from_list(): Unexpected type in list item: {type(item)}")


        return list_of_root_neo_ids





    #####################################################################################################

    '''                                     ~   EXPORT SCHEMA   ~                                     '''

    def ________EXPORT_SCHEMA________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def export_schema(cls) -> {}:
        """
        TODO: unit testing
        Export all the Schema nodes and relationships as a JSON string.

        IMPORTANT:  APOC must be activated in the database, to use this function.
                    Otherwise it'll raise an Exception

        :return:    A dictionary specifying the number of nodes exported,
                    the number of relationships, and the number of properties,
                    as well as a "data" field with the actual export as a JSON string
        """
        # Any Class or Property node
        nodes_query = "MATCH (n) WHERE (n:CLASS OR n:PROPERTY)"

        # Any relationship from a Class to another Class or to a Property
        rels_query = "MATCH (c:CLASS)-[r]->(n) WHERE (n:CLASS OR n:PROPERTY)"

        return cls.db.export_nodes_rels_json(nodes_query, rels_query)




    #####################################################################################################

    '''                                  ~   PRIVATE METHODS   ~                                      '''

    def ________PRIVATE_METHODS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


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



    # TODO: prefix "_" to name of private methods
    @classmethod
    def next_available_schema_id(cls) -> int:
        """
        Return the next available ID for nodes managed by this class
        For unique ID's to use on data nodes, use next_available_datanode_id() instead

        :return:     A unique auto-increment integer used for Schema nodes
        """
        return cls.next_autoincrement("schema_node")



    @classmethod
    def next_autoincrement(cls, kind: str) -> int:
        """
        This utilizes an ATOMIC database operation to both read and advance the autoincrement counter,
        based on a (single) node with label `Schema Autoincrement`
        and an attribute indicating the desired kind (group);
        if no such node exists (for example, after a new installation), it gets created, and 1 is returned

        :param kind:    A string used to maintain completely separate groups of auto-increment values
                            Currently used values: "data_node" and "schema_node"

        :return:        An integer that is a unique auto-increment for the specified group
        """
        q = '''
            MATCH (n: `Schema Autoincrement` {kind: $kind})
            SET n.last_id = n.last_id + 1
            RETURN n.last_id AS last_id
            '''
        last_id = cls.db.query(q, data_binding={"kind": kind}, single_cell="last_id")

        if last_id is None:
            cls.db.create_node(labels="Schema Autoincrement", properties={"kind": kind, "last_id": 1})
            return 1       # Start a new count for this group
        else:
            return last_id


    @classmethod
    def next_available_datanode_id(cls) -> int:
        """
        Reserve and return the next available auto-increment ID,
        in the separately-maintained group called "data_node".
        This value (currently often referred to as "item_id", and not to be confused
        with the internal ID assigned by Neo4j to each node),
        is meant as a permanent primary key, on which a URI could be based.

        For unique ID's to use on schema nodes, use next_available_schema_id() instead

        :return:    A unique auto-increment integer used for Data nodes
        """
        return cls.next_autoincrement("data_node")



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



    @classmethod
    def debug_print(cls, info: str, trim=False) -> None:
        """
        If the class' property "debug" is set to True,
        print out the passed info string,
        optionally trimming it, if too long

        :param info:
        :param trim:
        :return:        None
        """
        if cls.debug:
            if trim:
                info = cls.db.debug_trim(info)

            print(info)





######################################################################################################
######################################################################################################

class SchemaCache:
    """
    Cached by the Classes' internal database ID

    Used to improve the efficiency of methods that heavily interact with the Schema,
    such as JSON imports.

    Maintain a Python dictionary, whose keys are the internal database IDs of Schema Class nodes.
    Generally, it will be a subset of interest from all the Classes in the database.

    Note: this class gets instantiated, so that it's a local variable and won't cause
          trouble with multi-threading

    TODO:   add a "schema" argument to some NeoSchema methods that interact with the Schema,
            to provide an alternate manner of querying the Schema
            - as currently done by several method
    """
    def __init__(self):
        self._schema = {}   # The KEYS are the internal database IDs of the Schema Class nodes;
                            # the VALUES are dicts that contain the following keys:
                            #       1) "class_attributes"
                            #       2) "class_properties"
                            #       3) "out_neighbors"   [Note: "in_neighbors" not done for now]



    def get_all_cached_class_data(self, class_id: int) -> dict:
        """
        Return all existed cached data for the specified Class

        :param class_id:    An integer with the database internal ID of the desired Class node
        :return:            A (possibly empty) dict with keys that may include
                                "class_attributes", "class_properties", "out_neighbors"
        """
        if class_id not in self._schema:
            # No cached data info already exists for this Class... so, create it
            self._schema[class_id] = {}

        return self._schema[class_id]



    def get_cached_class_data(self, class_id: int, request: str) -> Union[dict, List[str]]:
        """
        Return the requested data for the specified Class.

        If cached values are available, they get used;
        otherwise, they get queried, then cached and returned.

        If request == "class_attributes":
            return the attributes of the requested Class,
            i.e. a dictionary of all the Class node's attributes
            EXAMPLE:  {'name': 'MY CLASS', 'schema_id': 123, 'type': 'L'}

        If request == "class_properties":
            return the properties of the requested Class,
            i.e. the  list of all the names of the Properties associated with the given Class
            EXAMPLE:  ["age", "gender", "weight"]

        If request == "out_neighbors":
            return a dictionary where the keys are the names of the outbound relationships from with the given Class,
            and the values are the names of the Classes on the other side of those relationships
            EXAMPLE:  {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}

        :param class_id:    An integer with the database internal ID of the desired Class node
        :param request:     A way to specify what to look up.
                                Permissible values: "class_attributes", "class_properties", "out_neighbors"
        :return:
        """
        assert request in ["class_attributes", "class_properties", "out_neighbors"], \
                "get_cached_class_data(): bad value for `request` argument.  Allowed values: " \
                "'class_attributes', 'class_properties', 'out_neighbors'"

        cached_data = self.get_all_cached_class_data(class_id)  # A dict

        if request == "class_attributes":
            if "class_attributes" not in cached_data:
                # The Class attributes hadn't been cached; so, retrieve them
                class_attributes = NeoSchema.get_class_attributes(class_id)
                cached_data["class_attributes"] = class_attributes

            return cached_data["class_attributes"]


        if request == "class_properties":
            if "class_properties" not in cached_data:
                # The Class properties hadn't been cached; so, retrieve them
                class_properties = NeoSchema.get_class_properties_fast(class_id, include_ancestors=False)
                cached_data["class_properties"] = class_properties

            return cached_data["class_properties"]


        if request == "out_neighbors":
            if "out_neighbors" not in cached_data:
                # The outbound links haven't been cached; so, retrieve them
                cached_data["out_neighbors"] = NeoSchema.get_class_outbound_data(class_id, omit_instance=True)
                '''
                    A (possibly empty) dictionary,where the keys are the name of outbound relationships,
                    and the values are the names of the Class nodes on the other side of those links.
                    EXAMPLE: {'IS_ATTENDED_BY': 'doctor', 'HAS_RESULT': 'result'}
                '''

            return cached_data["out_neighbors"]
