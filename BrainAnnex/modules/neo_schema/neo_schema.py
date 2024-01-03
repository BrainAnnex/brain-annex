from typing import Union, List
from neoaccess.cypher_utils import CypherUtils, CypherMatch
import json
import math
from datetime import datetime
from neo4j.time import DateTime     # TODO: move to NeoAccess
import pandas as pd


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

        To infuse into Neo4j functionality that some people turn to RDF, or to relational databases, for.
        However, carve out a new path rather than attempting to emulate RDF or relational databases!


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

        - Class can be of the "S" (Strict) or "L" (Lenient) type.
            A "lenient" Class will accept data nodes with any properties, whether declared in the Class Schema or not;
            by contrast, a "strict" class will prevent data nodes that contains properties not declared in the Schema

            (TODO: also implement required properties and property data types)


    IMPLEMENTATION DETAILS

        - Every node used by this class has a unique attribute "schema_id",
          containing a non-negative integer.
          Similarly, data nodes have a separate unique attribute "uri" (formerly "item_id");
          note that this is actually a "token", i.e. a part of a URI - not a full URI

        - The names of the Classes and Properties are stored in node attributes called "name".
          We also avoid calling them "label", as done in RDFS, because in Labeled Graph Databases
          like Neo4j, the term "label" has a very specific meaning, and is pervasively used.

        - For convenience, data nodes contain a redundant attribute named "schema_code"


    AUTHOR:
        Julian West


    TODO:   - continue the process of making the methods more efficient,
              by directly generate Cypher code, rather than using high-level methods in NeoAccess;
              for example, as done by create_data_node()


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

    '''                                     ~   CLASS-related   ~                                     '''

    def ________CLASS_related________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def assert_valid_class_name(cls, class_name: str) -> None:
        """
        Raise an Exception if the passed argument is not a valid Class name

        :param class_name:  A string with the putative name of a Schema Class
        :return:            None
        """
        assert type(class_name) == str, \
            f"NeoSchema.assert_valid_class_name(): " \
            f"The class name ({class_name}) must be a string (instead, it's of type {type(class_name)})"

        assert class_name != "", \
            "NeoSchema.assert_valid_class_name(): Class name cannot be an empty string"


    @classmethod
    def is_valid_class_name(cls, class_name: str) -> bool:
        """
        Return True if the passed argument is a valid Class name, or False otherwise

        :param class_name:  A string with the putative name of a Schema Class
        :return:            None
        """
        if type(class_name) == str and class_name != "":
            return True
        else:
            return False



    @classmethod
    def assert_valid_class_identifier(cls, class_node: Union[int, str]) -> None:
        """
        Raise an Exception is the argument is not a valid "identifier" for a Class node,
        meaning either a valid name or a valid internal database ID

        :param class_node:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :return:            None (an Exception is raised if the validation fails)
        """
        if type(class_node) == int:
            assert CypherUtils.valid_internal_id(class_node)
        else:
            cls.assert_valid_class_name(class_node)



    @classmethod
    def create_class(cls, name :str, code = None, strict = False, no_datanodes = False) -> (int, int):
        """
        Create a new Class node with the given name and type of schema,
        provided that the name isn't already in use for another Class.

        Return a pair with the Neo4j ID of the new ID,
        and the auto-incremented unique ID assigned to the new Class.
        Raise an Exception if a class by that name already exists.

        NOTE: if you want to add Properties at the same time that you create a new Class,
              use the function create_class_with_properties() instead.

        :param name:        Name to give to the new Class
        :param code:        Optional string indicative of the software handler for this Class and its subclasses
        :param strict:      If True, the Class will be of the "S" (Strict) type;
                                otherwise, it'll be of the "L" (Lenient) type
                            Explained under the comments for the NeoSchema class

        :param no_datanodes If True, it means that this Class does not allow data node to have a "SCHEMA" relationship to it;
                                typically used by Classes having an intermediate role in the context of other Classes

        :return:            A pair of integers with the internal database ID and the unique schema_id assigned to the node just created,
                                if it was created;
                                an Exception is raised if a class by that name already exists
        """
        #TODO: offer the option to link to an existing Class, like create_class_with_properties() does
        #       link_to=None, link_name="INSTANCE_OF", link_dir="OUT"
        #TODO: maybe an option to add multiple Classes of the same type at once???
        #TODO: maybe stop returning the schema_id ?

        name = name.strip()     # Strip any whitespace at the ends
        assert name != "", "NeoSchema.create_class(): Unacceptable Class name that is empty or blank"

        if cls.class_name_exists(name):
            raise Exception(f"NeoSchema.create_class(): A class named `{name}` ALREADY exists")

        schema_id = cls.next_available_schema_id()    # A schema-wide ID, also used for Property nodes

        attributes = {"name": name, "schema_id": schema_id, "strict": strict}
        if code:
            attributes["code"] = code
        if no_datanodes:
            attributes["no_datanodes"] = True

        #print(f"create_class(): about to call db.create_node with parameters `{cls.class_label}` and `{attributes}`")
        neo_id = cls.db.create_node(cls.class_label, attributes)
        return (neo_id, schema_id)



    @classmethod
    def get_class_internal_id(cls, class_name :str) -> int:
        """
        Returns the internal database ID of the Class node with the given name,
        or raise an Exception if not found, or if more than one is found.
        Note: unique Class names are assumed.

        :param class_name:  The name of the desired class
        :return:            The internal database ID of the specified Class
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
    def get_class_id(cls, class_name :str, namespace=None) -> int:
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
        Return True if a Class by the given internal database ID already exists, or False otherwise

        :param neo_id:  Integer with internal database ID
        :return:        A boolean indicating whether the specified Class exists
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
    def get_class_name_by_schema_id(cls, schema_id :int) -> str:
        """
        Returns the name of the class with the given Schema ID, or "" if not found

        :param schema_id:   An integer with the unique ID of the desired class
        :return:            The name of the class with the given Schema ID, or "" if not found
        """
        # TODO: maybe phase out?
        assert type(schema_id) == int, \
            "get_class_name_by_schema_id(): The schema id MUST be an integer"

        match = cls.db.match(labels="CLASS", key_name="schema_id", key_value=schema_id)
        result = cls.db.get_nodes(match, single_cell="name")

        if not result :
            return ""

        return result



    @classmethod
    def get_class_name(cls, internal_id: int) -> str:
        """
        Returns the name of the class with the given internal database ID,
        or raise an Exception if not found

        :param internal_id: An integer with the internal database ID
                                of the desired class
        :return:            The name of the class with the given Schema ID;
                                raise an Exception if not found
        """
        cls.db.assert_valid_internal_id(internal_id)

        result = cls.db.get_nodes(internal_id, single_cell="name")

        if not result :
            raise Exception(f"NeoSchema.get_class_name_by_neo_id(): no Class with a Neo4j ID of {internal_id} found")

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
                                        EXAMPLE:  {'name': 'MY CLASS', 'schema_id': 123, 'strict': False}
        """
        #cls.db.assert_valid_internal_id(class_internal_id)

        match = cls.db.match(labels="CLASS", internal_id=class_internal_id)
        result = cls.db.get_nodes(match, single_row=True)

        if result is None :
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

        TODO: disregard capitalization in sorting

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
        # TODO: in case of failure, investigate further the problem
        #       (e.g. no class by that name vs. class has data points still attached to it)
        #       and give a more specific error message

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
    def is_strict_class(cls, class_internal_id: int, schema_cache=None) -> bool:
        """
        Return True if the given Class is of "Strict" type,
        or False otherwise (or if the information is missing)

        :param class_internal_id:   The internal ID of a Schema Class node
        :param schema_cache:        (OPTIONAL) "SchemaCache" object
        :return:                    True if the Class is "strict" or False if not (i.e., if it's "lax")
        """
        if schema_cache:
            class_attrs = schema_cache.get_cached_class_data(class_internal_id, request="class_attributes")
        else:
            class_attrs = NeoSchema.get_class_attributes(class_internal_id)

        return class_attrs.get('strict', False)    # True if a "Strict" Class



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
    def assert_valid_relationship_name(cls, rel_name :str) -> None:
        """

        :param rel_name:
        :return:
        """
        assert type(rel_name) == str, \
            "assert_valid_relationship_name(): the relationship name must be a string"
        assert rel_name != "", \
            "assert_valid_relationship_name(): the relationship name must be a non-empty string"



    @classmethod
    def create_class_relationship(cls, from_class: Union[int, str], to_class: Union[int, str],
                                  rel_name="INSTANCE_OF", use_link_node=False) -> None:
        """
        Create a relationship (provided that it doesn't already exist) with the specified name
        between the 2 existing Class nodes (identified by names or by their internal database IDs),
        in the ( from -> to ) direction.

        In case of error, an Exception is raised.

        Note: multiple relationships by the same name between the same nodes are allowed by Neo4j,
              as long as the relationships differ in their attributes
              (but this method doesn't allow setting properties on the new relationship)

        :param from_class:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node from which the new relationship originates.
        :param to_class:    Either an integer with the internal database ID of an existing Class node,
                                or a string with its name.
                                Used to identify the node to which the new relationship terminates.
        :param rel_name:    Name of the relationship to create, in the from -> to direction
                                (blanks allowed)
        :param use_link_node: EXPERIMENTAL feature - insert an intermediate "LINK" node in the newly-created
                                relationship
        :return:            None
        """
        #TODO: add a method that reports on all existing relationships among Classes?
        #TODO: allow properties on the relationship
        #TODO: provide more feedback in case of failure

        # Validate the arguments
        assert (type(rel_name) == str) and (rel_name != ""), \
            "create_class_relationship(): A name (non-empty string) must be provided for the new relationship"

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
            '''

        if use_link_node:
            q += f"MERGE (from)-[:`{rel_name}`]->(:LINK)-[:`{rel_name}`]->(to)"
            number_rel_expected = 2
        else:
            q += f"MERGE (from)-[:`{rel_name}`]->(to)"
            number_rel_expected = 1

        result = cls.db.update_query(q, {"from_id": from_class, "to_id": to_class})
        #print("result of update_query in create_class_relationship(): ", result)


        if result.get("relationships_created") != number_rel_expected:
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
        #TODO: provide more feedback in case of failure

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
        """
        Return True if a relationship with the specified name exists between the two given Classes,
        in the specified direction.
        The Schema allows several scenarios:
            - A direct relationship from one Class node to the other
            - A relationship that goes thru an intermediary "LINK" node
            - Either of the 2 above scenarios, but between "ancestors" of the two nodes;
              "ancestors" are defined by means of following
              any number of "INSTANCE_OF" hops to other Class nodes

        :param from_class:  Name of an existing Class node (blanks allowed in name)
        :param to_class:    Name of another existing Class node (blanks allowed in name)
        :param rel_name:    Name of the relationship(s) to delete,
                                if found in the from -> to direction (blanks allowed in name)
        :return:            True if the Class relationship exists, or False otherwise
        """

        assert (type(rel_name) == str) and (rel_name != ""), \
            "class_relationship_exists(): the argument `rel_name` must be a non-empty string"

        # Note: from_class and to_class get validated in the next 2 function calls
        from_id = cls.get_class_internal_id(from_class)
        to_id = cls.get_class_internal_id(to_class)

        common_query_end = f'''WHERE id(from) = {from_id} AND id(to) = {to_id}
            RETURN COUNT(r) AS number_links
            '''

        # First, try the simplest scenario: direct link between the Classes
        # For efficiency, we'll try to rule out the most common scenarios first,
        # rather than constructing one big query that looks at ll scenarios
        q = f'''
            MATCH (from :CLASS)-[r:`{rel_name}`]->(to :CLASS) 
            {common_query_end}
            '''
        #print(q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If unsuccessful, see if it's possible to find a link
        # between "ancestors" of the two nodes (thru "INSTANCE_OF" relationships)
        q = f'''
            MATCH (from :CLASS)-[:INSTANCE_OF*0..]->
            (left :CLASS)-[r:`{rel_name}`]->(right :CLASS)
            <-[:INSTANCE_OF*0..]-(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 2: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If still unsuccessful, see if it's possible to find a relationship by means of
        # an intermediary "LINK" node (NOTE: this is a new feature being rolled in)
        q = f'''
            MATCH (from :CLASS)-[r:`{rel_name}`]->(:LINK)-[:`{rel_name}`]->(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 3: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True

        # If still unsuccessful, see if it's possible to find a relationship by means of
        # a "LINK" intermediary node, as well as "INSTANCE_OF" ancestors
        q = f'''
            MATCH (from :CLASS)-[:INSTANCE_OF*0..]->
            (left :CLASS)-[r:`{rel_name}`]->(:LINK)-[:`{rel_name}`]->(right :CLASS)
            <-[:INSTANCE_OF*0..]-(to :CLASS) 
            {common_query_end}
            '''
        #print("Attempt 4: ", q)
        result = cls.db.query(q, single_cell="number_links")
        if result > 0:
            return True


        return False    # Connection could not be found under any scenario



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
    def get_class_relationships(cls, schema_id :int, link_dir="BOTH", omit_instance=False) -> Union[dict, list]:
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
    def get_class_outbound_data(cls, class_neo_id :int, omit_instance=False) -> dict:
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

    def ________CLASS_PROPERTIES________(DIVIDER):
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
    def get_class_properties(cls, class_node :Union[int, str], include_ancestors=False, sort_by_path_len=False) -> list:
        """
        TODO: maybe phase out in favor of get_class_properties_fast()

        Return the list of all the names of the Properties associated with the given Class
        (including those inherited thru ancestor nodes by means of "INSTANCE_OF" relationships,
        if include_ancestors is True),
        sorted by the schema-specified position (or, optionally, by path length)

        :param class_node:          Either an integer with the internal database ID of an existing Class node,
                                        or a string with its name
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
        if type(class_node) == str:
            schema_id = cls.get_class_id(class_name=class_node)
        elif type(class_node) == int:
            schema_id = class_node
        else:
            raise Exception("get_class_properties(): argument `class_node` must be either a string or an integer")

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
        :param class_id:        (OPTIONAL) Integer with the schema_id of the Class to which attach the given Properties
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
    def create_class_with_properties(cls, name :str, property_list: [str], code=None, strict=False,
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

        :param name:            String with name to assign to the new class
        :param property_list:   List of strings with the names of the Properties, in their default order (if that matters)
        :param code:            Optional string indicative of the software handler for this Class and its subclasses.
                                    TODO: deprecate

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

        # TODO: merge with create_class()

        # TODO: add argument 'extra_labels'

        if class_to_link_to:
            assert link_name, \
                "create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                "a valid value for the argument `link_to_name` must also be provided"

            assert (link_dir == "OUT") or (link_dir == "IN"), \
                f"create_class_with_properties(): if the argument `class_to_link_to` is provided, " \
                f"the argument `link_dir` must be either 'OUT' or 'IN' (value passed: {link_dir})"


        # Create the new Class
        new_class_int_id , new_class_uri = cls.create_class(name, code=code, strict=strict)
        cls.debug_print(f"Created new schema CLASS node (name: `{name}`, Schema ID: {new_class_uri})")

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
                raise Exception(f"New Class ({name}) created successfully, but unable to link it to the `{class_to_link_to}` class. {ex}")

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
        Obtain the "schema code" of a Class, specified by its name.
        The "schema code" is an optional but convenient text code,
        stored either on a Class node, or on any of its ancestors by way of "INSTANCE_OF" relationships

        :return:    A string with the Schema code (empty string if not found)
                    EXAMPLE: "i"
        """
        q = '''
        MATCH (c:CLASS {name: $_CLASS_NAME})-[:INSTANCE_OF*0..]->(ancestor:CLASS)
        WHERE ancestor.code IS NOT NULL 
        RETURN ancestor.code AS code
        '''
        # Search 0 or more hops from the given Class node

        result = cls.db.query(q, {"_CLASS_NAME": class_name})   # TODO: use the single_cell argument of query()
        if result == []:
            return ""       # not found

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
        Return the list of the *names* of all the Properties associated with the given DATA node,
        based on the Schema it is associated with, sorted their by schema-specified position.
        The desired node is identified by specifying which one of its attributes is a primary key,
        and providing a value for it.

        IMPORTANT : this function returns the NAMES of the Properties; not their values

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
        MATCH (d: `my data label` {uri: $primary_key_value})
              -[:SCHEMA]->(c :`CLASS`)
              -[r :HAS_PROPERTY]->(p :`PROPERTY`)
        RETURN p.name AS prop_name
        ORDER BY r.index
        '''

        result_list = cls.db.query(q, {"primary_key_value": primary_key_value})

        name_list = [item["prop_name"] for item in result_list]

        return name_list



    @classmethod
    def get_data_node_internal_id(cls, uri :str) -> int:
        """
        Returns the internal database ID of the given data node,
        specified by its value of the uri attribute

        :param uri: A string to identify a data node by the value of its "uri" attribute
        :return:    The internal database ID of the specified data node
        """
        match = cls.db.match(key_name="uri", key_value=uri)
        result = cls.db.get_nodes(match, return_internal_id=True)

        if not result:
            raise Exception(f"NeoSchema.get_data_node_internal_id(): no Data Node with the given uri ({uri}) was found")

        if len(result) > 1:
            raise Exception(f"NeoSchema.get_data_node_internal_id(): more than 1 Data Node "
                            f"with the given uri ({uri}) was found ({len(result)} were found)")

        return result[0]["internal_id"]



    @classmethod
    def get_data_node_id(cls, key_value :str, key_name="uri") -> int:
        """
        Get the internal database ID of a data node, given some other primary key

        :return:   An integer with the internal database ID of the data node
        """

        match = cls.db.match(key_name=key_name, key_value=key_value)
        result = cls.db.get_nodes(match, return_internal_id=True, single_cell="internal_id")

        if result is None:
            raise Exception(f"get_data_node_id(): unable to find a data node with the attribute `{key_name}={key_value}`")

        return result



    @classmethod
    def data_node_exists(cls, data_node: Union[int, str]) -> bool:
        """
        Return True if the specified Data Node exists, or False otherwise.

        :param data_node:   Either an integer (representing an internal database ID),
                                or a string (representing the value of the "uri" field)
        :return:            True if the specified Data Node exists, or False otherwise
        """
        # Prepare the clause part of a Cypher query
        if type(data_node) == int:
            clause = "WHERE id(dn) = $data_node"
        elif type(data_node) == str:
            clause = "WHERE dn.uri = $data_node"

        else:
            raise Exception(f"data_node_exists(): "
                            f"argument `data_node` must be an integer or a string; "
                            f"instead, it is {type(data_node)}")

        # Prepare a Cypher query to locate the number of the data nodes
        q = f'''
            MATCH (:CLASS)<-[:SCHEMA]-(dn) 
            {clause} 
            RETURN COUNT(dn) AS number_found
            '''

        number_found = cls.db.query(q, {"data_node" : data_node}, single_cell="number_found")

        if number_found == 0:
            return False
        elif number_found == 1:
            return True
        else:
            raise Exception(f"data_node_exists(): more than 1 node was found "
                            f"with the same URI ({data_node}), which ought to be unique")



    @classmethod
    def fetch_data_node(cls, uri = None, internal_id = None, labels=None, properties=None) -> Union[dict, None]:
        """
        Return a dictionary with all the key/value pairs of the attributes of given data node

        See also locate_node()

        :param uri:         The "uri" field to uniquely identify the data node
        :param internal_id: OPTIONAL alternate way to specify the data node;
                                if present, it takes priority
        :param labels:      OPTIONAL (generally, redundant) ways to locate the data node
        :param properties:  OPTIONAL (generally, redundant) ways to locate the data node

        :return:            A dictionary with all the key/value pairs, if found; or None if not
        """
        # TODO: add function that only returns a specified single Property, or specified list of Properties
        if internal_id is None:
            assert uri is not None, \
                "NeoSchema.fetch_data_node(): arguments `uri` and `internal_id` cannot both be None"

            match = cls.db.match(key_name="uri", key_value=uri,
                                 labels=labels, properties=properties)
        else:
            match = cls.db.match(internal_id=internal_id, labels=labels, properties=properties)

        return cls.db.get_nodes(match, single_row=True)



    @classmethod
    def locate_node(cls, node_id: Union[int, str], id_type=None, labels=None, dummy_node_name="n") -> CypherMatch:
        """
        EXPERIMENTAL - a generalization of fetch_data_node()

        Return the "match" structure to later use to locate a node identified
        either by its internal database ID (default), or by a primary key (with optional label.)

        NOTE: No database operation is actually performed.

        :param node_id: This is understood be the Neo4j ID, unless an id_type is specified
        :param id_type: For example, "uri";
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
    def class_of_data_node(cls, node_id: int, id_type=None, labels=None) -> str:
        """
        Return the name of the Class of the given data node: identified
        either by its internal database ID (default), or by a primary key (with optional label)

        :param node_id:     Either an internal database ID or a primary key value
        :param id_type:     OPTIONAL - name of a primary key used to identify the data node;
                                leave blank to use the internal database ID
        :param labels:      Optional string, or list/tuple of strings, with Neo4j labels
                                (DEPRECATED)

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
        #cls.db.debug_query_print(q, data_binding, "class_of_data_node")

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
    def data_nodes_of_class(cls, class_name) -> [int]:
        """
        Return the Item ID's of all the Data Nodes of the given Class
        TODO: offer to optionally use a label
        TODO: switch to returning the internal database ID's

        :param class_name:
        :return:            Return the Item ID's of all the Data Nodes of the given Class
        """
        q = '''
            MATCH (n)-[:SCHEMA]->(c:CLASS {name: $class_name}) RETURN n.uri AS uri
            '''

        res = cls.db.query(q, {"class_name": class_name}, single_column="uri")

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
    def allowable_props(cls, class_internal_id: int, requested_props: dict, silently_drop: bool, schema_cache=None) -> dict:
        """
        If any of the properties in the requested list of properties is not a declared (and thus allowed) Schema property,
        then:
            1) if silently_drop is True, drop that property from the returned pared-down list
            2) if silently_drop is False, raise an Exception

        TODO: possibly expand to handle REQUIRED properties

        :param class_internal_id:    The internal ID of a Schema Class node
        :param requested_props: A dictionary of properties one wishes to assign to a new data node, if the Schema allows
        :param silently_drop:   If True, any requested properties not allowed by the Schema are simply dropped;
                                    otherwise, an Exception is raised if any property isn't allowed
        :param schema_cache:    (OPTIONAL) "SchemaCache" object

        :return:                A possibly pared-down version of the requested_props dictionary
        """
        if requested_props == {} or requested_props is None:
            return {}     # It's a moot point, if not attempting to set any property

        if not cls.is_strict_class(class_internal_id, schema_cache=schema_cache):
            return requested_props      # Any properties are allowed if the Class isn't strict


        allowed_props = {}
        class_properties = cls.get_class_properties_fast(class_internal_id)  # List of Properties registered with the Class

        for requested_prop in requested_props.keys():
            # Check each of the requested properties
            if requested_prop in class_properties:
                allowed_props[requested_prop] = requested_props[requested_prop]     # Allowed
            else:
                # Not allowed
                if not silently_drop:
                    raise Exception(f"NeoSchema.allowable_props(): "
                                    f"the requested property `{requested_prop}` is not among the registered Properties "
                                    f"of the Class `{cls.get_class_name(class_internal_id)}`")

        return allowed_props



    @classmethod
    def create_data_node(cls, class_node :Union[int, str], properties = None, extra_labels = None,
                         assign_uri=False, new_uri=None, silently_drop=False) -> int:
        """
        Create a new data node, of the type indicated by specified Class,
        with the given (possibly none) properties and extra label(s);
        the name of the Class is always used as a label.

        The new data node, if successfully created, will optionally be assigned
        a passed URI value, or a unique auto-gen value, for its field uri.

        If the requested Class doesn't exist, an Exception is raised

        If the data node needs to be created with links to other existing data nodes,
        use add_data_node_with_links() instead

        Note: the responsibility for picking a URI belongs to the calling function
              (which will typically make use of a namespace)

        Not: if creating multiple data nodes at once, one might use import_pandas_nodes()

        :param class_node:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :param properties:  (OPTIONAL) Dictionary with the properties of the new data node.
                                EXAMPLE: {"make": "Toyota", "color": "white"}
        :param extra_labels:(OPTIONAL) String, or list/tuple of strings, with label(s) to assign to the new data node,
                                IN ADDITION TO the Class name (which is always used as label)

        :param assign_uri:  (DEPRECATED) If True, the new node is given an extra attribute named "uri",
                                with a unique auto-increment value in the "data_node" namespace,
                                as well an extra attribute named "schema_code"
                                (TODO: drop)

        :param new_uri:     If new_uri is provided, then a field called "uri"
                                is set to that value;
                                also, an extra attribute named "schema_code" gets set
                                # TODO: "schema_code" should perhaps be responsibility of the higher layer

        :param silently_drop: If True, any requested properties not allowed by the Schema are simply dropped;
                                otherwise, an Exception is raised if any property isn't allowed
                                Note: only applicable for "Strict" schema - with a "Lenient" schema anything goes

        :return:            The internal database ID of the new data node just created
        """
        # TODO: consider allowing creation of multiple nodes from one call

        # Do various validations
        cls.assert_valid_class_identifier(class_node)

        assert (extra_labels is None) or isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema.create_data_node(): argument `extra_labels`, if passed, must be a string, or list/tuple of strings"

        if properties:
            assert type(properties) == dict, \
                "NeoSchema.create_data_node(): The `properties` argument, if provided, MUST be a dictionary"


        # Obtain both the Class name and its internal database ID
        if type(class_node) == str:
            class_name = class_node
            class_internal_id = cls.get_class_internal_id(class_node)
        else:
            class_name = cls.get_class_name(class_node)
            class_internal_id = class_node


        labels = class_name     # By default, use the Class name as a label

        if type(extra_labels) == str and extra_labels.strip() != class_name:
            labels = [extra_labels, class_name]

        elif isinstance(extra_labels, (list, tuple)):
            # If we get thus far, labels is a list or tuple
            labels = list(extra_labels)
            if class_name not in extra_labels:
                labels += [class_name]


        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.create_data_node(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Verify whether all properties are allowed, and possibly trim them down
        properties = cls.allowable_props(class_internal_id=class_internal_id, requested_props=properties,
                                         silently_drop=silently_drop)


        # Prepare the properties to add
        if properties is None:
            properties = {}

        properties_to_set = cls.allowable_props(class_internal_id, requested_props=properties,
                                                silently_drop=silently_drop)


        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes:
        # "uri" and "schema_code";
        # if requested, expand properties_to_set accordingly
        if assign_uri or new_uri:
            if not new_uri:
                # TODO: phase out this branch
                new_id = cls.next_available_datanode_uri()      # Obtain (and reserve) the next auto-increment value
                                                                # in the "data_node" namespace
            else:
                new_id = new_uri

            #print("New ID assigned to new data node: ", new_id)
            properties_to_set["uri"] = new_id                   # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                properties_to_set["schema_code"] = schema_code      # Expand the dictionary

            # EXAMPLE of properties_to_set at this stage:
            #       {"make": "Toyota", "color": "white", "uri": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned uri


        new_internal_id = cls._create_data_node_helper(class_internal_id=class_internal_id,
                                                       labels=labels, properties_to_set=properties_to_set)

        return new_internal_id



    @classmethod
    def _create_data_node_helper(cls, class_internal_id :int,
                                 labels=None, properties_to_set=None) -> int:
        """
        Helper function.
        IMPORTANT: all validations/schema checks are assumed to have been performed by the caller functions.

        Create a new data node, of the type indicated by specified Class,
        with the given (possibly none) properties and extra label(s);
        the name of the Class is always used as a label.

        :param class_internal_id:   The internal database ID of the above class
        :param labels:              String, or list/tuple of strings, with label(s)
                                        to assign to the new data node,
                                        (note: the Class name is expected to be among them)
        :param properties_to_set:   (OPTIONAL) Dictionary with the properties of the new data node.
                                        EXAMPLE: {"make": "Toyota", "color": "white"}

        :return:                    The internal database ID of the new data node just created
        """

        # Prepare strings and a data-binding dictionary suitable for inclusion in a Cypher query,
        #   to define the new node to be created
        labels_str = CypherUtils.prepare_labels(labels)    # EXAMPLE:  ":`CAR`:`INVENTORY`"
        (cypher_props_str, data_binding) = CypherUtils.dict_to_cypher(properties_to_set)
        # EXAMPLE:
        #   cypher_props_str = "{`name`: $par_1, `city`: $par_2}"
        #   data_binding = {'par_1': 'Julian', 'par_2': 'Berkeley'}

        # Create a new Data node, with a "SCHEMA" relationship to its Class node
        q = f'''
            MATCH (cl :CLASS)
            WHERE id(cl) = {class_internal_id}           
            CREATE (dn {labels_str} {cypher_props_str})
            MERGE (dn)-[:SCHEMA]->(cl)           
            RETURN id(dn) AS internal_id
            '''

        # TODO: consider switching to update_query(), for more insight
        internal_id = cls.db.query(q, data_binding, single_cell="internal_id")

        return internal_id



    @classmethod
    def import_pandas_nodes(cls, df :pd.DataFrame, class_node :Union[int, str],
                            datetime_cols=None, int_cols=None,
                            extra_labels=None, schema_code=None, report_frequency=100) -> [int]:
        """
        Import a group of entities, from the rows of a Pandas dataframe, as data nodes in the database.

        NaN's and empty strings are dropped - and never make it into the database

        :param df:          A Pandas Data Frame with the data to import;
                                each row represents a record - to be turned into a graph-database node.
                                Each column represents a Property of the data node, and it must have been
                                previously declared in the Schema
        :param class_node:  Either an integer with the internal database ID of an existing Class node,
                                or a string with its name
        :param datetime_cols: (OPTIONAL) String, or list/tuple of strings, of column name(s)
                                that contain datetime strings such as '2015-08-15 01:02:03'
                                (compatible with the python "datetime" format)
        :param int_cols:    (OPTIONAL) String, or list/tuple of strings, of column name(s)
                                that contain integers, or that are to be converted to integers
                                (typically necessary because numeric Pandas columns with NaN's
                                 are automatically turned into floats)
        :param extra_labels:(OPTIONAL) String, or list/tuple of strings, with label(s) to assign to the new data node,
                                IN ADDITION TO the Class name (which is always used as label)
        :param schema_code: (OPTIONAL) Legacy element, deprecated.  Extra string to add as value
                                to a "schema_code" property for each new data node created
        :param report_frequency: (OPTIONAL) How often to print out the status of the import-in-progress

        :return:            A list of the internal database ID's of the newly-created data nodes
        """
        # TODO: consider a partial merger with create_data_node()

        # Do various validations
        cls.assert_valid_class_identifier(class_node)

        assert (extra_labels is None) or isinstance(extra_labels, (str, list, tuple)), \
            "NeoSchema.import_pandas_nodes(): argument `extra_labels`, if passed, must be a string, or list/tuple of strings"


        # Obtain both the Class name and its internal database ID
        if type(class_node) == str:
            class_name = class_node
            class_internal_id = cls.get_class_internal_id(class_node)
        else:
            class_name = cls.get_class_name(class_node)
            class_internal_id = class_node


        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.import_pandas_nodes(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        labels = class_name     # By default, use the Class name as a label

        if type(extra_labels) == str and extra_labels.strip() != class_name:
            labels = [extra_labels, class_name]

        elif isinstance(extra_labels, (list, tuple)):
            # If we get thus far, labels is a list or tuple
            labels = list(extra_labels)
            if class_name not in extra_labels:
                labels += [class_name]

        if type(datetime_cols) == str:
            datetime_cols = [datetime_cols]
        elif datetime_cols is None:
            datetime_cols = []

        if type(int_cols) == str:
            int_cols = [int_cols]
        elif int_cols is None:
            int_cols = []


        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.import_pandas_nodes(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # Verify whether all properties are allowed
        # TODO: consider using allowable_props()
        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        class_properties = cls.get_class_properties(class_node=class_node, include_ancestors=True)

        assert set(cols) <= set(class_properties), \
            f"import_pandas(): attempting to import Pandas dataframe columns " \
            f"not declared in the Schema:  {set(cols) - set(class_properties)}"


        # Prepare the properties to add

        recordset = df.to_dict('records')   # Turn the Pandas dataframe into a list of dicts
        #print(recordset)
        print(f"Getting ready to import {len(recordset)} records...")

        internal_id_list = []
        for d in recordset:     # d is a dictionary
            d_scrubbed = cls._scrub_dict(d)     # Zap NaN's, blank strings, leading/trailing spaces

            for dt_col in datetime_cols:
                if dt_col in d_scrubbed:
                    dt_str = d_scrubbed[dt_col]     # EXAMPLE: '2015-08-15 01:02:03'
                    dt_python = datetime.fromisoformat(dt_str)  # As a python "datetime" object
                                                                # EXAMPLE: datetime.datetime(2015, 8, 15, 1, 2, 3)
                    dt_neo = DateTime.from_native(dt_python)    # In Neo4j format; TODO: let NeoAccess handle this
                                                                # EXAMPLE: neo4j.time.DateTime(2015, 8, 15, 1, 2, 3, 0)
                    d_scrubbed[dt_col] = dt_neo     # Replace the original string value

            for col in int_cols:
                if col in d_scrubbed:
                    val = d_scrubbed[col]           # This might be a float
                    val_int = int(val)
                    d_scrubbed[col] = val_int       # Replace the original value


            if schema_code:
                d_scrubbed["schema_code"] = schema_code      # Add a legacy element, perhaps to be discontinued

            #print(d_scrubbed)
            new_internal_id = cls._create_data_node_helper(class_internal_id=class_internal_id,
                                                           labels=labels, properties_to_set=d_scrubbed)
            #print("new_internal_id", new_internal_id)
            internal_id_list.append(new_internal_id)

            if report_frequency  and  (len(internal_id_list) % report_frequency == 0):
                print(f"    imported {len(internal_id_list)} so far")
        # END for

        if report_frequency:
            print(f"    FINISHED importing a total of {len(internal_id_list)} records")

        return internal_id_list



    @classmethod
    def _scrub_dict(cls, d :dict) -> dict:
        """
        Helper function to clean up data during imports.

        Given a dictionary, assemble and return a new dict where string values are trimmed of
        any leading or trailing blanks.
        Entries whose values are blank or NaN get omitted from the new dictionary being returned.

        EXAMPLE:    {"a": 1, "b": 3.5, "c": float("nan"), "d": "some value", "e": "   needs  cleaning!    ",
                     "f": "", "g": "            "}
                gets simplified to:
                    {"a": 1, "b": 3.5, "d": "some value", "e": "needs  cleaning!"  }

        :param d:   A python dictionary
        :return:
        """
        scrubbed_d = {}
        for k,v in d.items():   # Loop over all key/value pairs in the dictionary
            if type(v) == str:
                v = v.strip()       # Zap all leading and trailing blanks
                if v == "":
                    continue        # Blank string values get omitted

            elif type(v) == float and math.isnan(v):
                continue            # NaN's get omitted

            scrubbed_d[k] = v

        return scrubbed_d



    @classmethod
    def import_pandas_links(cls, df :pd.DataFrame, class_from :str, class_to :str,
                            col_from :str, col_to :str,
                            link_name :str,
                            col_link_props=None, name_map=None,
                            skip_errors = False, report_frequency=100) -> [int]:
        """
        Import a group of relationships between existing database Data Nodes,
        from the rows of a Pandas dataframe, as database links between the existing Data Nodes

        :param df:          A Pandas Data Frame with the data RELATIONSHIP to import
        :param class_from:  Name of the Class of the data nodes from which the relationship starts
        :param class_to:    Name of the Class of the data nodes from which the relationship ends
        :param col_from:    Name of the Data Frame column specifying the data nodes from which the relationship starts
        :param col_to:      Name of the Data Frame column specifying the data nodes from which the relationship starts
        :param link_name:   Name of the new relationship being created
        :param col_link_props:    (OPTIONAL) Name of a property to assign to the relations,
                                as well as name of the Data Frame column containing the values
        :param name_map:    (OPTIONAL) Dict with mapping from Pandas column names
                                to Property names in the data nodes in the database
        :param skip_errors: (OPTIONAL) If True, the import continues even in the presence of errors;
                                default is False
        :param report_frequency: (OPTIONAL) How often to print out the status of the import-in-progress

        :return:            A list of of the internal database ID's of the created links
        """
        # TODO: verify that the requested relationship between the Classes is registered in the Schema

        cols = list(df.columns)     # List of column names in the Pandas Data Frame
        assert col_from in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_from}` requested in the argument 'col_from'"

        assert col_to in cols, \
            f"import_pandas_links(): the given Data Frame doesn't have the column named `{col_to}` requested in the argument 'col_to'"


        if col_from in name_map:
            key_from = name_map[col_from]
        else:
            key_from = col_from

        if col_to in name_map:
            key_to = name_map[col_to]
        else:
            key_to = col_to

        if col_link_props in name_map:
            link_prop = name_map[col_link_props]
        else:
            link_prop = col_link_props


        recordset = df.to_dict('records')   # Turn the Pandas dataframe into a list of dicts
        print(f"Getting ready to import {len(recordset)} links...")

        links_imported = []
        for d in recordset:     # d is a dictionary
            # Prepare a Cypher query to link up the 2 nodes
            q = f'''
                MATCH (from_node {{{key_from}: $value_from}}), (to_node {{{key_to}: $value_to}})
                MERGE (from_node)-[r:`{link_name}` {{{link_prop}: $rel_prop_value}}]->(to_node)
                RETURN id(r) AS link_id
                '''

            data_dict = {"value_from": d[col_from], "value_to": d[col_to], "rel_prop_value": d[link_prop]}
            #cls.db.debug_query_print(q, data_dict)
            result = cls.db.update_query(q, data_dict)
            #print(result)

            if result.get('relationships_created') == 1:    # If a new link was created
                returned_data = result.get('returned_data')
                #if returned_data:
                links_imported.append(returned_data[0]["link_id"])
                if result.get('properties_set') != 1:
                    error_msg = f"import_pandas_links(): failed to set the property value for the new relationship for Pandas row: {d}"
                    if skip_errors:
                        print(error_msg)
                    else:
                        raise Exception(error_msg)
            else:                                           # If no link was created
                error_msg = f"import_pandas_links(): failed to create a new relationship for Pandas row: {d}"
                if skip_errors:
                    print(error_msg)
                else:
                    raise Exception(error_msg)

            if report_frequency  and  (len(links_imported) % report_frequency == 0):
                print(f"    imported {len(links_imported)} so far")
        # END for

        if report_frequency:
            print(f"    FINISHED importing a total of {len(links_imported)} links")

        return links_imported



    @classmethod
    def add_data_node_merge(cls, class_name :str, properties :dict) -> (int, bool):
        """
        A new Data Node gets created only if
        there's no other Data Node with the same properties,
        and attached to the given Class.

        An Exception is raised if any of the requested properties is not registered with the given Schema Class,
        or if that Class doesn't accept Data Nodes.

        :param class_name:  The Class node for the Data Node to locate, or create if not found
        :param properties:  A dictionary with the properties to look up the Data Node by,
                                or to give to a new one if an existing one wasn't found.
                                EXAMPLE: {"make": "Toyota", "color": "white"}

        :return:            A pair with:
                                1) The internal database ID of either an existing Data Node or of a new one just created
                                2) True if a new Data Node was created, or False if not (i.e. an existing one was found)
        """
        # TODO: maybe return a dict with 2 keys: "internal_id" and "created" ? (like done by NeoAccess)

        assert (type(properties) == dict) and (properties != {}), \
            "NeoSchema.add_data_node_merge(): the `properties` argument MUST be a dictionary, and cannot be empty"

        class_internal_id = cls.get_class_internal_id(class_name)

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_node_merge(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        # Generate an Exception if any of the requested properties is not registered with the Schema Class
        cls.allowable_props(class_internal_id=class_internal_id, requested_props=properties,
                            silently_drop=False)


        # From the dictionary of attribute names/values,
        #       create a part of a Cypher query, with its accompanying data dictionary
        (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
        # EXAMPLE - if properties is {'cost': 65.99, 'item description': 'the "red" button'} then:
        #       attributes_str = '{`cost`: $par_1, `item description`: $par_2}'
        #       data_dictionary = {'par_1': 65.99, 'par_2': 'the "red" button'}

        q = f'''
            MATCH (cl :CLASS)
            WHERE id(cl) = {class_internal_id}
            MERGE (n :`{class_name}` {attributes_str})-[:SCHEMA]->(cl)           
            RETURN id(n) AS internal_id
            '''

        result = cls.db.update_query(q, data_dictionary)

        internal_id = result["returned_data"][0]["internal_id"]     # The internal database ID
                                                                    # of the node found or just created

        if result.get("nodes_created") == 1:
            return  (internal_id, True)         # A new node was created
        else:
            return  (internal_id, False)        # An existing node was found



    @classmethod
    def add_data_column_merge(cls, class_name :str, property_name: str, value_list: list) -> dict:
        """
        Add a data column (i.e. a set of single-property data nodes).
        Individual nodes are created only if there's no other data node with the same property/value

        :param class_name:      The Class node for the Data Node to locate, or create if not found
        :param property_name:   The name of the data column (i.e. the name of the data field)
        :param value_list:      A list of values that make up the the data column
        :return:                A dictionary with 2 keys - "new_nodes" and "old_nodes";
                                    their values are the respective numbers of nodes (created vs. found)
        """
        assert (type(property_name) == str) and (property_name != ""), \
            "NeoSchema.add_data_column_merge(): the `property_name` argument MUST be a string, and cannot be empty"

        assert (type(value_list) == list) and (value_list != []), \
            "NeoSchema.add_data_column_merge(): the `value_list` argument MUST be a list, and cannot be empty"

        class_internal_id = cls.get_class_internal_id(class_name)

        # Make sure that the Class accepts Data Nodes
        if not cls.allows_data_nodes(class_neo_id=class_internal_id):
            raise Exception(f"NeoSchema.add_data_column_merge(): "
                            f"addition of data nodes to Class `{class_name}` is not allowed by the Schema")

        # Generate an Exception if any of the requested properties is not registered with the Schema Class
        cls.allowable_props(class_internal_id=class_internal_id, requested_props={property_name : 0},
                            silently_drop=False)    # TODO: get rid of hack that requires a value for the property

        new_id_list = []
        existing_id_list = []
        for value in value_list:
            properties = {property_name : value}
            # From the dictionary of attribute names/values,
            #       create a part of a Cypher query, with its accompanying data dictionary
            (attributes_str, data_dictionary) = CypherUtils.dict_to_cypher(properties)
            # EXAMPLE - if properties is {'cost': 65.99, 'item description': 'the "red" button'} then:
            #       attributes_str = '{`cost`: $par_1, `item description`: $par_2}'
            #       data_dictionary = {'par_1': 65.99, 'par_2': 'the "red" button'}

            q = f'''
                MATCH (cl :CLASS)
                WHERE id(cl) = {class_internal_id}
                MERGE (n :`{class_name}` {attributes_str})-[:SCHEMA]->(cl)           
                RETURN id(n) AS internal_id
                '''

            result = cls.db.update_query(q, data_dictionary)

            internal_id = result["returned_data"][0]["internal_id"]     # The internal database ID
                                                                        # of the node found or just created
            if result.get("nodes_created") == 1:
                new_id_list.append(internal_id)         # A new node was created
            else:
                existing_id_list.append(internal_id)    # An existing node was found
        # END for

        return {"new_nodes": new_id_list, "old_nodes": existing_id_list}
        # TODO: rename "old_nodes" to "present_nodes" (or "existing_nodes", or "found_nodes")



    @classmethod
    def add_data_node_with_links(cls, class_name = None, class_internal_id = None,
                                 properties = None, labels = None,
                                 links = None,
                                 assign_uri=False, new_uri=None) -> int:
        """
        This is NeoSchema's counterpart of NeoAccess.create_node_with_links()

        Add a new data node, of the Class specified by its name,
        with the given (possibly none) attributes and label(s),
        optionally linked to other, already existing, DATA nodes.

        If the specified Class doesn't exist, or doesn't allow for Data Nodes, an Exception is raised.

        The new data node, if successfully created:
            1) will be given the Class name as a label, unless labels are specified
            2) will optionally be assigned an "uri" unique value
               that is either automatically assigned or passed.

        EXAMPLES:   add_data_node_with_links(class_name="Cars",
                                              properties={"make": "Toyota", "color": "white"},
                                              links=[{"internal_id": 123, "rel_name": "OWNED_BY", "rel_dir": "IN"}])

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: verify that all the requested links conform to the Schema
        TODO: invoke special plugin-code, if applicable???
        TODO: maybe rename to add_data_node()

        :param class_name:  The name of the Class that this new data node is an instance of.
                                Also use to set a label on the new node, if labels isn't specified
        :param class_internal_id: OPTIONAL alternative to class_name.  If both specified,
                                class_internal_id prevails
                            TODO: merge class_name and class_internal_id into class_node, as done
                                  for create_data_node()
        :param properties:  An optional dictionary with the properties of the new data node.
                                EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:      OPTIONAL string, or list of strings, with label(s) to assign to the new data node;
                                if not specified, use the Class name.  TODO: ALWAYS include the Class name, as done in create_data_node()
        :param links:       OPTIONAL list of dicts identifying existing nodes,
                                and specifying the name, direction and optional properties
                                to give to the links connecting to them;
                                use None, or an empty list, to indicate if there aren't any
                                Each dict contains the following keys:
                                    "internal_id"   REQUIRED - to identify an existing node
                                    "rel_name"      REQUIRED - the name to give to the link
                                    "rel_dir"       OPTIONAL (default "OUT") - either "IN" or "OUT" from the new node
                                    "rel_attrs"     OPTIONAL - A dictionary of relationship attributes

        :param assign_uri:  If True, the new node is given an extra attribute named "uri",
                                    with a unique auto-increment value, as well an extra attribute named "schema_code".
                                    Default is False

        :param new_uri:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                    If new_uri is provided, then assign_uri is automatically made True

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

        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes: "uri" and "schema_code";
        # if requested, expand cypher_prop_dict accordingly
        if assign_uri or new_uri:
            if not new_uri:
                new_id = cls.next_available_datanode_uri()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_uri
            #print("New ID assigned to new data node: ", new_id)
            cypher_prop_dict["uri"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                cypher_prop_dict["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of cypher_prop_dict at this stage:
            #       {"make": "Toyota", "color": "white", "uri": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned uri


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
                                     assign_uri=False, new_uri=None) -> int:
        """
        TODO: OBSOLETED BY add_data_node_with_links() - TO DITCH *AFTER* add_data_node_with_links() gets link validation!
        A faster version of add_data_point()
        Add a new data node, of the Class specified by name or ID,
        with the given (possibly none) attributes and label(s),
        optionally linked to another, already existing, DATA node.

        The new data node, if successfully created, will be assigned a unique value for its field uri
        If the requested Class doesn't exist, an Exception is raised

        NOTE: if the new node requires MULTIPLE links to existing data points, use add_and_link_data_point() instead

        EXAMPLES:   add_data_point(class_name="Cars", data_dict={"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     data_dict={"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with uri = 999, and label "salesperson"

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
                                        EXAMPLE: the uri of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param assign_uri:  If True, the new node is given an extra attribute named "uri" with a unique auto-increment value
        :param new_uri:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
                                    If new_uri is provided, then assign_uri is automatically made True

        :return:                If successful, an integer with the Neo4j ID
                                    of the node just created;
                                    otherwise, an Exception is raised
        """
        #print(f"In add_data_point().  rel_name: `{rel_name}` | rel_prop_key: `{rel_prop_key}` | rel_prop_value: {rel_prop_value}")

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("NeoSchema.add_data_point(): Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name_by_schema_id(schema_id)      # Derive the Class name from its ID

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


        # In addition to the passed properties for the new node, data nodes may contain 2 special attributes: "uri" and "schema_code";
        # if requested, expand cypher_prop_dict accordingly
        if assign_uri or new_uri:
            if not new_uri:
                new_id = cls.next_available_datanode_uri()      # Obtain (and reserve) the next auto-increment value
            else:
                new_id = new_uri
            #print("New ID assigned to new data node: ", new_id)
            cypher_prop_dict["uri"] = new_id               # Expand the dictionary

            schema_code = cls.get_schema_code(class_name)
            if schema_code != "":
                cypher_prop_dict["schema_code"] = schema_code  # Expand the dictionary

            # EXAMPLE of cypher_prop_dict at this stage:
            #       {"make": "Toyota", "color": "white", "uri": 123, "schema_code": "r"}
            #       where 123 is the next auto-assigned uri


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
                           new_uri=None, return_uri=True) -> Union[int, str]:
        """
        TODO: OBSOLETE.  Replace by add_data_node_with_links()
              TO DITCH *AFTER* add_data_node_with_links() gets link validation!

        Add a new data node, of the Class specified by name or ID,
        with the given (possibly none) attributes and label(s),
        optionally linked to another DATA node, already existing.

        The new data node, if successfully created, will be assigned a unique value for its field uri
        If the requested Class doesn't exist, an Exception is raised

        EXAMPLES:   add_data_point(class_name="Cars", data_dict={"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     data_dict={"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with uri = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable
        TODO: make the issuance of a new uri optional

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param data_dict:       An optional dictionary with the properties of the new data point.
                                TODO: a better name might be "properties"
                                    EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to the new data node;
                                    if not specified, use the Class name.  TODO: the Class name ought to ALWAYS be added

        :param connected_to_id: Int or None.  To optionally specify another (already existing) DATA node
                                        to connect the new node to, specified by its uri.
                                        TODO: --> for efficiency, use the Neo4j ID instead [and ditch the arg "connected_to_labels"]
                                        EXAMPLE: the uri of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param connected_to_labels:     EXAMPLE: "salesperson"
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param new_uri:         Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be a unique string)
        :param return_uri:      Default to True.    TODO: change to False
                                If True, the returned value is the auto-increment "uri" value of the node just created;
                                    otherwise, it returns its Neo4j ID

        :return:                EITHER a string with either the auto-increment "uri" value
                                OR or the internal database ID
                                of the node just created (based on the flag "return_uri")
        """
        #print(f"In add_data_point().  rel_name: `{rel_name}` | rel_prop_key: `{rel_prop_key}` | rel_prop_value: {rel_prop_value}")

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name_by_schema_id(schema_id)      # Derive the Class name from its ID

        if labels is None:
            # If not specified, use the Class name
            labels = class_name

        if data_dict is None:
            data_dict = {}

        assert type(data_dict) == dict, "The data_dict argument, if provided, MUST be a dictionary"

        cypher_props_dict = data_dict

        if not cls.allows_data_nodes(class_name=class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes contain 2 special attributes: "uri" and "schema_code";
        # expand cypher_props_dict accordingly
        # TODO: make this part optional
        if not new_uri:
            new_id = cls.next_available_datanode_uri()      # Obtain (and reserve) the next auto-increment value
        else:
            new_id = new_uri
        #print("New ID assigned to new data node: ", new_id)
        cypher_props_dict["uri"] = new_id               # Expand the dictionary

        schema_code = cls.get_schema_code(class_name)       # TODO: this may slow down execution
        if schema_code != "":
            cypher_props_dict["schema_code"] = schema_code  # Expand the dictionary

        # EXAMPLE of cypher_props_dict at this stage:
        #       {"make": "Toyota", "color": "white", "uri": 123, "schema_code": "r"}
        #       where 123 is the next auto-assigned uri

        # Create a new data node, with a "SCHEMA" relationship to its Class node and, if requested, also a relationship to another data node
        if connected_to_id:     # if requesting a relationship to an existing data node
            if rel_prop_key and (rel_prop_value != '' and rel_prop_value is not None):  # Note: cannot just say "and rel_prop_value" or it'll get dropped if zero
                rel_attrs = {rel_prop_key: rel_prop_value}
            else:
                rel_attrs = None

            neo_id = cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"},

                                                               {"labels": connected_to_labels, "key": "uri", "value": connected_to_id,
                                                                "rel_name": rel_name, "rel_dir": rel_dir, "rel_attrs": rel_attrs}
                                                               ]
                                                  )
        else:                   # simpler case : only a link to the Class node
            neo_id = cls.db.create_node_with_relationships(labels, properties=cypher_props_dict,
                                                  connections=[{"labels": "CLASS", "key": "name", "value": class_name,
                                                                "rel_name": "SCHEMA"}]
                                                  )

        if return_uri:
            return new_id
        else:
            return neo_id



    @classmethod
    def add_and_link_data_point_OBSOLETE(cls, class_name: str, connected_to_list: [tuple], properties=None, labels=None,
                                         assign_uri=False) -> int:
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

        The new data node optionally gets assigned a unique "uri" value (TODO: make optional)

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
        :param assign_uri:      If True, the new node is given an extra attribute named "uri" with a unique auto-increment value

        :return:                    If successful, an integer with Neo4j ID of the node just created;
                                        otherwise, an Exception is raised
        """
        new_neo_id = cls.add_data_point_fast_OBSOLETE(class_name=class_name, properties=properties, labels=labels,
                                                      assign_uri=assign_uri)
        # TODO: maybe expand add_data_point_fast(), so that it can link to multiple other data nodes at once
        for link in connected_to_list:
            node_neo_id, rel_name = link    # Unpack
            cls.add_data_relationship(from_id=new_neo_id, to_id=node_neo_id, rel_name=rel_name)

        return new_neo_id



    @classmethod
    def update_data_node(cls, data_node :Union[int, str], set_dict :dict, drop_blanks = True) -> int:
        """
        Update, possibly adding and/or dropping fields, the properties of an existing Data Node

        :param data_node:   Either an integer with the internal database ID, or a string with a URI value
        :param set_dict:    A dictionary of field name/values to create/update the node's attributes
                                (note: blanks ARE allowed within the keys)
        :param drop_blanks: If True, then any blank field is interpreted as a request to drop that property
                                (as opposed to setting its value to "")
        :return:            The number of properties set or removed;
                                if the record wasn't found, or an empty set_dict was passed, return 0
                                Important: a property is counted as "set" even if the new value is
                                           identical to the old value!
        """
        #TODO: check whether the Schema allows the added/dropped fields, if applicable
        #      Compare the keys of set_dict against the Properties of the Class of the Data Node

        if set_dict == {}:
            return 0            # Nothing to do!

        if type(data_node) == int:
            where_clause =  f'WHERE id(n) = {data_node}'
        elif type(data_node) == str:
            where_clause =  f'WHERE n.uri = "{data_node}"'
        else:
            raise Exception("update_data_node(): the argument `data_node` must be an integer or a string")


        data_binding = {}
        set_list = []
        remove_list = []
        for field_name, field_value in set_dict.items():                # field_name, field_value are key/values in set_dict
            if (field_value != "") or (drop_blanks == False):
                field_name_safe = field_name.replace(" ", "_")              # To protect against blanks in name, which could not be used
                                                                            #   in names of data-binding variables.  E.g., "end date" becomes "end_date"
                set_list.append(f"n.`{field_name}` = ${field_name_safe}")   # Example:  "n.`end date` = end_date"
                data_binding[field_name_safe] = field_value                 # Add entry the Cypher data-binding dictionary, of the form {"end_date": some_value}
            else:
                remove_list.append(f"n.`{field_name}`")

        # Example of data_binding at the end of the loop: {'color': 'white', 'max_quantity': 7000}

        set_clause = ""
        if set_list:
            set_clause = "SET " + ", ".join(set_list)   # Example:  "SET n.`color` = $color, n.`max quantity` = $max_quantity"

        remove_clause = ""
        if drop_blanks and remove_list:
            remove_clause = "REMOVE " + ", ".join(remove_list)   # Example:  "REMOVE n.`color`, n.`max quantity`


        q = f'''
            MATCH (n) {where_clause}
            {set_clause} 
            {remove_clause}            
            '''

        #cls.db.debug_query_print(q, data_binding)

        stats = cls.db.update_query(q, data_binding)
        #print(stats)
        number_properties_set = stats.get("properties_set", 0)
        return number_properties_set



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
    def delete_data_point(cls, uri: str, labels=None) -> int:
        """
        Delete the given data point.  TODO: obsolete in favor of delete_data_node()

        :param uri:
        :param labels:      OPTIONAL (generally, redundant)
        :return:            The number of nodes deleted (possibly zero)
        """
        match = cls.db.match(key_name="uri", key_value=uri, properties={"schema_code": "cat"},
                            labels=labels)
        return cls.db.delete_nodes(match)



    @classmethod
    def register_existing_data_node(cls, class_name="", schema_id=None,
                                    existing_neo_id=None, new_uri=None) -> int:
        """
        Register (declare to the Schema) an existing data node with the Schema Class specified by its name or ID.
        An uri is generated for the data node and stored on it; likewise, for a schema_code (if applicable).
        Return the newly-assigned uri

        EXAMPLES:   register_existing_data_node(class_name="Chemicals", existing_neo_id=123)
                    register_existing_data_node(schema_id=19, existing_neo_id=456)

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data node is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param existing_neo_id: Internal ID to identify the node to register with the above Class.
                                TODO: expand to use the match() structure
        :param new_uri:     OPTIONAL. Normally, the Item ID is auto-generated,
                                but it can also be provided (Note: MUST be unique)

        :return:                If successful, an integer with the auto-increment "uri" value of the node just created;
                                otherwise, an Exception is raised
        """
        if not existing_neo_id:
            raise Exception("Missing argument: existing_neo_id")

        assert type(existing_neo_id) == int, \
            "register_existing_data_node(): The argument `existing_neo_id` MUST be an integer"  # TODO: use validity checker

        # Make sure that at least either class_name or schema_id is present
        if (not class_name) and (not schema_id):
            raise Exception("Must specify at least either the class_name or the schema_id")

        if not class_name:
            class_name = cls.get_class_name_by_schema_id(schema_id)      # Derive the Class name from its ID
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

        if not new_uri:
            new_uri = cls.next_available_datanode_uri()     # Generate, if not already provided

        cls.debug_print("register_existing_data_node(). New uri to be assigned to the data node: ", new_uri)

        data_binding = {"class_name": class_name, "new_uri": new_uri, "existing_neo_id": existing_neo_id}

        schema_code = cls.get_schema_code(class_name)
        if schema_code != "":
            data_binding["schema_code"] = schema_code   # Expand the dictionary

        # EXAMPLE of data_binding at this stage:
        #       {'class_name': 'Chemicals', 'new_uri': 888, 'existing_neo_id': 123, 'schema_code': 'r'}
        #       where 888 is the next auto-assigned uri

        # Link the existing data node, with a "SCHEMA" relationship, to its Class node, and also set some properties on the data node
        q = f'''
            MATCH (existing), (class :CLASS {{name: $class_name}}) WHERE id(existing) = $existing_neo_id
            MERGE (existing)-[:SCHEMA]->(class)
            SET existing.uri = $new_uri
            '''
        if schema_code != "":
            q += " , existing.schema_code = $schema_code"

        cls.db.debug_query_print(q, data_binding, "register_existing_data_node") # Note: this is the special debug print for NeoAccess
        result = cls.db.update_query(q, data_binding)
        #print(result)

        number_new_rels = result.get('relationships_created')   # This ought to be 1
        if number_new_rels != 1:
            raise Exception("Failed to created the new relationship (`SCHEMA`)")

        return new_uri



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
                                this is understood be the internal database ID, unless an 'id_type' argument is passed
        :param to_id:       The ID of the data node at which the new relationship is to end;
                                this is understood be the internal database ID, unless an 'id_type' argument is passed
        :param rel_name:    The name to give to the new relationship between the 2 specified data nodes
        :param rel_props:   TODO: not currently used.  Unclear what multiple calls would do in this case
        :param labels_from: (OPTIONAL) Labels on the 1st data node
        :param labels_to:   (OPTIONAL) Labels on the 2nd data node
        :param id_type:     For example, "uri";
                            if not specified, all the node ID's are assumed to be internal database ID's

        :return:            None.  If the specified relationship didn't get created (for example,
                            in case the the new relationship doesn't exist in the Schema), raise an Exception
        """
        assert rel_name, f"add_data_relationship_OLD(): no name was provided for the new relationship"

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
            raise Exception(f"add_data_relationship_OLD(): cannot add the relationship `{rel_name}` between the data nodes, "
                            f"because no such relationship exists from Class `{class_from}` to Class `{class_to}`. "
                            f"The Schema needs to be modified first")



    @classmethod
    def add_data_relationship_hub(cls, center_id :int, periphery_ids :[int], periphery_class :str,
                                    rel_name :str, rel_dir = "OUT") -> int:
        """
        Add a group of relationships between a single Data Node ("center")
        and each of the Data Nodes in the given list ("periphery"),
        with the specified relationship name and direction.

        All Data Nodes must already exist.
        All the "periphery" Data Nodes must belong to the same Class
            (whose name is passed by periphery_class)

        :param center_id:       Internal database ID of an existing Data Node
                                    that we wish to connect
                                    to all other Data Nodes specified in the next argument
        :param periphery_ids:   List of internal database IDs of existing Data Nodes,
                                    all belonging to the Class passed by the next argument
        :param periphery_class: The name of the common Class to which all the Data Nodes
                                    specified in periphery_ids belong to
        :param rel_name:        A string with the name to give to all the newly-created relationships
        :param rel_dir:         Either "IN" (towards the "center" node)
                                    or "OUT" (away from it, towards the "periphery" nodes)

        :return:                The number of relationships created
        """
        cls.assert_valid_relationship_name(rel_name)

        center_class = cls.class_of_data_node(node_id=center_id)


        q = f'''
            MATCH (center_node), (periphery_node :{periphery_class}) 
            WHERE id(center_node)= $center_id AND id(periphery_node) IN $periphery_ids   
                   
            '''

        if rel_dir == "OUT":
            assert cls.class_relationship_exists(from_class=center_class, to_class=periphery_class, rel_name=rel_name), \
                f"add_data_relationship_hub(): first, you must update the Schema to register a `{rel_name}` " \
                f"relationship from Class `{center_class}` to Class `{periphery_class}`"

            q += f" MERGE (center_node)-[:`{rel_name}`]->(periphery_node)"
        elif rel_dir == "IN":
            assert cls.class_relationship_exists(from_class=periphery_class, to_class=center_class, rel_name=rel_name), \
                f"add_data_relationship_hub(): first, you must update the Schema to register a `{rel_name}` " \
                f"relationship from Class `{periphery_class}` to Class `{center_class}`"

            q += f" MERGE (center_node)<-[:`{rel_name}`]-(periphery_node)"
        else:
            raise Exception(f"add_data_relationship_hub(): argument `rel_name` "
                            f"must be either 'IN' or 'OUT'; the value passed was {rel_dir}")

        result = cls.db.update_query(q, {"center_id": center_id, "periphery_ids": periphery_ids})
        number_relationships_added = result.get("relationships_created", 0)   # If key isn't present, use a value of 0

        return number_relationships_added




    @classmethod
    def add_data_relationship(cls, from_id :int, to_id :int, rel_name :str, rel_props = None) -> None:
        """
        Simpler (and possibly faster) version of add_data_relationship_OLD()

        Add a new relationship with the given name, from one to the other of the 2 given data nodes,
        identified by their Neo4j ID's.

        The requested new relationship MUST be present in the Schema, or an Exception will be raised.
        TODO: also ought to allow intermediate "INSTANCE_OF" hops

        Note that if a relationship with the same name already exists between the data nodes exists,
        nothing gets created (and an Exception is raised)

        :param from_id: The internal database ID of the data node at which the new relationship is to originate
                                TODO: also allow primary keys, as done in class_of_data_node()
        :param to_id:   The internal database ID of the data node at which the new relationship is to end
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

        # TODO: drop the current approach of putting "-[:`{rel_name}`]->" in the Cypher only captures Schema
        #       Class relationships with no Properties; should instead call a new method:
        #           class_relationship_exists(from_class, to_class, rel_name)
        #       and then proceed if True
        '''      
        assert cls.class_relationship_exists(from_class=from_class, to_class=to_class, rel_name=rel_name), \
            f"Relationship `{rel_name}` from Class `{from_class}` to Class `{to_class}` must first be registered in the Schema"

        q = f
            MATCH (from_node), (to_node)
            WHERE id(from_node) = $from_neo_id AND id(to_node) = $to_neo_id
            MERGE (from_node)-[:`{rel_name}`]->(to_node)          
        '''

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
    def remove_data_relationship(cls, from_uri :str, to_uri :str, rel_name :str, labels=None) -> None:
        """
        Drop the relationship with the given name, from one to the other of the 2 given DATA nodes.
        Note: the data nodes are left untouched.
        If the specified relationship didn't get deleted, raise an Exception

        TODO: first verify that the relationship is optional in the schema???
        TODO: migrate from "uri" values to also internal database ID's, as done in class_of_data_node()

        :param from_uri:    String with the "uri" value of the data node at which the relationship originates
        :param to_uri:      String with the "uri" value of the data node at which the relationship ends
        :param rel_name:    The name of the relationship to delete
        :param labels:      OPTIONAL (generally, redundant).  Labels required to be on both nodes

        :return:            None.  If the specified relationship didn't get deleted, raise an Exception
        """
        assert rel_name != "", f"remove_data_relationship(): no name was provided for the relationship"

        match_from = cls.db.match(labels=labels, key_name="uri", key_value=from_uri,
                                  dummy_node_name="from")

        match_to =   cls.db.match(labels=labels, key_name="uri", key_value=to_uri,
                                  dummy_node_name="to")

        cls.db.remove_links(match_from, match_to, rel_name=rel_name)   # This will raise an Exception if no relationship is removed



    @classmethod
    def remove_multiple_data_relationships(cls, node_id: Union[int, str], rel_name: str, rel_dir: str, labels=None) -> None:
        """     TODO: test
        Drop all the relationships with the given name, from or to the given data node.
        Note: the data node is left untouched.

        IMPORTANT: this function cannot be used to remove relationship involving any Schema node

        :param node_id:     The internal database ID (integer) or name (string) of the data node of interest
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
    def follow_links_NOT_YET_IMPLEMENTED(cls, class_name, key_name, key_value, link_sequence):
        """
        Follow a chain of links among data nodes,
        starting with a given data node (or maybe possibly a set of them?)

        :param class_name:      (OPTIONAL)
        :param key_name:        TODO: or pass a "match" object?
        :param key_value:
        :param link_sequence:   EXAMPLE: [("occurs", "OUT", "Indexer),
                                          ("has_index", "IN", None)]
                                    Each triplet is: (relationship name,
                                                      direction,
                                                      name of Class of data node on other side)
                                    Any component could be None
        :return:                A list of internal node ID's (or, optionally, all properties of the end nodes?)
        """
        #TODO: possibly use cls.db.follow_links()
        pass




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
                * INABILITY TO LINK TO EXISTING NODES IN DBASE (try using: "uri": some_int  as the only property in nodes to merge)
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
        cls.debug_print("***************************** cache initialized ***************************** ")

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

            for root_uri in node_id_list:
                cls.debug_print(f"***Linking import node (uri={metadata_neo_id}) with "
                                f"data root node (Neo4j ID={root_uri}), thru relationship `imported_data`")
                # Connect the root of the import to the metadata node
                cls.add_data_relationship(from_id=metadata_neo_id, to_id=root_uri, rel_name="imported_data")

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
                    gets silently dropped.  TODO: issue some report about anything that gets dropped

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
                                                assign_uri=False)



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

    '''                                       ~   URI'S   ~                                           '''

    def ________URI________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def is_valid_uri(cls, uri :str) -> bool:
        """
        Return True if the passed uri is valid; otherwise, return False

        :param uri:
        :return:
        """
        if type(uri) == str and uri != "":
            return True

        return False



    @classmethod
    def generate_uri(cls, prefix, namespace, suffix="") -> str:
        """
        Generate a URI (or fragment thereof, aka "token"),
        using the given prefix and suffix;
        the middle part is a unique auto-increment value (separately maintained
        in various groups, or "namespaces".)

        EXAMPLE:  generate_uri("doc.", "documents", ".new") might produce "doc.3.new"

        :param prefix:      A string to place at the start of the URI
        :param namespace:   A string with the name of the desired group of auto-increment values
        :param suffix:      (OPTIONAL) A string to place at the end of the URI
        :return:            A string with a newly-generated URI (unique in the given namespace)
        """
        return f"{prefix}{cls.next_autoincrement(namespace)}{suffix}"



    @classmethod
    def next_autoincrement(cls, namespace :str, advance=1) -> int:
        """
        This utilizes an ATOMIC database operation to both read and advance the autoincrement counter,
        based on a (single) node with label `Schema Autoincrement`
        and an attribute indicating the desired namespace (group);
        if no such node exists (for example, after a new installation), it gets created, and 1 is returned.

        Note that the returned number (or last of a sequence of numbers, if advance > 1)
        is de-facto "permanently reserved" on behalf of the calling function,
        and can't be used by any other competing thread, thus avoid concurrency problems (racing conditions)

        :param namespace:   A string used to maintain completely separate groups of auto-increment values;
                                leading/trailing blanks are ignored
        :param advance:     Normally, auto-increment advances by 1 unit, but a different positive integer
                                may be used

        :return:            An integer that is a unique auto-increment for the specified namespace
                                (starting with 1); it's ready-to-use and "reserved", i.e. could be used
                                at any future time
        """
        assert type(namespace) == str, \
            "next_autoincrement(): the argument `namespace` is required and must be a string"
        assert namespace != "", \
            "next_autoincrement(): the argument `namespace` must be a non-empty string"

        assert type(advance) == int, \
            "next_autoincrement(): the argument `advance` is required and must be an integer"
        assert advance >= 1, \
            "next_autoincrement(): the argument `advance` must be an integer >= 1"


        namespace = namespace.strip()   # Zap leading/trailing blanks

        q = f'''
            MATCH (n: `Schema Autoincrement` {{namespace: $namespace}})
            SET n.next_count = n.next_count + {advance}
            RETURN n.next_count AS next_count
            '''
        next_count = cls.db.query(q, data_binding={"namespace": namespace}, single_cell="next_count")

        if next_count is None:     # If no node found
            cls.db.create_node(labels="Schema Autoincrement",
                               properties={"namespace": namespace, "next_count": 1+advance})
            return 1       # Start a new count for this namespace
        else:
            return next_count - advance



    @classmethod
    def next_available_datanode_uri(cls, prefix="") -> str:
        """
        Reserve and return a URI based on the next available auto-increment ID,
        in the separately-maintained group (i.e. namespace) called "data_node".
        This value (not to be confused with the internal database ID assigned to each node),
        is meant as a permanent primary key.

        For unique ID's to use on Schema nodes, use next_available_schema_id() instead

        :param prefix:  (OPTIONAL) String to prefix to the auto-increment number
        :return:        A unique auto-increment integer used for Data nodes
        """
        n = cls.next_autoincrement("data_node")
        uri = f"{prefix}{n}"

        return uri





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
            EXAMPLE:  {'name': 'MY CLASS', 'schema_id': 123, 'strict': False}

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




######################################################################################################
######################################################################################################

class DataNode:
    """
    EXPERIMENTAL: not yet in use!

    This new class is being experimented with, in the method APIRequestHandler.search_for_word()

    It might perhaps better belong to the lower (NeoAccess) layer

    TODO: explore some variation of the following data structure for network of data nodes (or maybe of any node)

        - general node object -
        {'properties': properties_dict,
         'internal_id': some_int,
         'labels': list_of_labels,
         'links': list_of_link_objects
        }

        - link object -
        {'name': relationship_name,
         'properties': relationship_properties_dict,
         'direction': in_or_out,
         'node': node_object_on_other_side
        }

    Contrast it with data structure returned by Neo4j.

    Also explore a SIMPLER data structure for a node and its immediate neighbors:

        - simpler node object -
        {'properties': properties_dict,
         'internal_id': some_int,
         'labels': list_of_labels,
         'links': list_of_neighbor_objects
        }

        - neighbor object -
        {'link_name': relationship_name,
         'link_direction': in_or_out,
         'link_properties': relationship_properties_dict,

         'properties': properties_dict,
         'internal_id': some_int,
         'labels': list_of_labels,
         'links': list_of_neighbor_objects  <-- MAYBE! Allow network representation, but may lose simplicity
    }

    Note:          {'link_name', 'link_direction', 'link_properties'} might be turned into a "link object"

    """
    def __init__(self, internal_id, labels, properties, links=None):
        """
        Initialize the data structure that represents all that is known about a Data Node

        :param internal_id:
        :param labels:
        :param properties:
        """
        self.internal_id = internal_id
        self.labels = labels
        self.properties = properties
        self.links = links              # List of DataRelationship objects
                                        # IMPORTANT: None means 'unknown'; whereas [] means no links



    def add_relationship(self, link_name, link_direction, link_properties, node_obj) -> None:
        """
        Save in memory a representation of all the data for the relationship
        with the specified other node

        :param link_name:
        :param link_direction:
        :param link_properties:
        :param node_obj:        Object of type DataNode
        :return:                None
        """
        new_rel = DataRelationship(link_name, link_direction, link_properties, node_obj)
        if self.links is None:
            self.links = [new_rel]
        else:
            self.links.append(new_rel)



##############################

class DataRelationship:
    """
    EXPERIMENTAL helper class: not yet in use!
    """

    def __init__(self, link_name, link_direction, link_properties, node_obj):
        """
        Initialize the data structure that represents all that is known
        about the relationship with the specified node

        :param link_name:
        :param link_direction:
        :param link_properties:
        :param node_obj:        Object of type DataNode
        """
        self.link_name = link_name
        self.link_direction = link_direction
        self.link_properties = link_properties
        self.node_obj = node_obj
