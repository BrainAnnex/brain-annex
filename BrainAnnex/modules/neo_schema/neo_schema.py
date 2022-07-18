from typing import Union, List
from BrainAnnex.modules.neo_access.neo_access import CypherUtils
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
        * DATA POINTS
        * DATA IMPORT
        * EXPORT SCHEMA
        * INTERNAL  METHODS



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

        Copyright (c) 2021-2022 Julian A. West

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
                                        #       change it, if you have conflicts with other modules
                                        #       Alt. name ideas: "SCHEMA"

    property_label = "PROPERTY"         # Neo4j label to be used with Property nodes managed by this class

    class_prop_rel = "HAS_PROPERTY"     # The name to use for the relationships from `Class` to `Property` nodes

    data_class_rel = "SCHEMA"           # The name to use for the relationships from data nodes to `Property` nodes
                                        #       Alt. name ideas: "IS", "HAS_CLASS", "HAS_SCHEMA", "TYPE", "TYPE_OF"

    debug = False                       # Flag indicating whether a debug mode is to be used by all methods of this class
                                        #       (currently, in very limited use)



    @classmethod
    def set_database(cls, db) -> None:
        """
        IMPORTANT: this method MUST be called before using this class!

        :param db:  Database-interface object, to be used with the NeoAccess library
        :return:    None
        """
        cls.db = db



    #####################################################################################################
    #                                                                                                   #
    #                                   ~ CLASS-related  ~                                              #
    #                                                                                                   #
    #####################################################################################################

    @classmethod
    def create_class(cls, name: str, code=None, schema_type="L", no_datanodes = False) -> int:
        """
        Create a new Class node with the given name and type of schema,
        provided that the name isn't already in use for another Class.

        Return the auto-incremented unique ID assigned to the new Class,
        or raise an Exception if a class by that name already exists

        NOTE: if you want to add Properties at the same time that you create a new Class,
              use the function new_class_with_properties() instead.

        TODO: offer the option to link to an existing Class.  link_to=None, link_name="INSTANCE_OF", link_dir="OUT"
        TODO: maybe an option to add multiple Classes of the same type at once???

        :param name:        Name to give to the new Class
        :param code:        Optional string indicative of the software handler for this Class and its subclasses
        :param schema_type: Either "L" (Lenient) or "S" (Strict).  Explained under the class-wide comments
        :param no_datanodes If True, it means that this Class does not allow data node to have a "SCHEMA" relationship to it;
                                typically used by Classes having an intermediate role in the context of other Classes.
        :return:            An integer with the unique schema_id assigned to the node just created, if it was created;
                                an Exception is raised if a class by that name already exists
        """
        assert schema_type=="L" or schema_type=="S", "schema_type argument must be either 'L' or 'S'"

        name = name.strip()     # Strip any whitespace at the ends
        assert name != "", "Unacceptable Class name, either empty or blank"

        #print(f"create_class(): about to call db.exists_by_key with parameters `{cls.class_label}` and `{name}`")
        if cls.class_name_exists(name):
            raise Exception(f"A class named `{name}` ALREADY exists")

        schema_id = cls.next_available_id()    # A schema-wide ID, also used for Property nodes

        attributes = {"name": name, "schema_id": schema_id, "type": schema_type}
        if code:
            attributes["code"] = code
        if no_datanodes:
            attributes["no_datanodes"] = True       # TODO: test this option

        #print(f"create_class(): about to call db.create_node with parameters `{cls.class_label}` and `{attributes}`")
        cls.db.create_node(cls.class_label, attributes)
        return schema_id



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

        match = cls.db.find(labels="CLASS", key_name="name", key_value=class_name)
        result = cls.db.get_nodes(match, single_cell="schema_id")

        if result is None:
            return -1

        return result



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
        :return:
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

        match = cls.db.find(labels="CLASS", key_name="schema_id", key_value=schema_id)
        result = cls.db.get_nodes(match, single_cell="name")

        if not result :
            return ""

        return result



    @classmethod
    def get_all_classes(cls, only_names=True) -> [str]:
        """
        Fetch and return a list of all the existing Schema classes - either just their names (sorted alphabetically)
        (TODO: or a fuller listing - not yet implemented)

        TODO: disregard capitalization is sorting

        :return:    A list of all the existing Class names
        """
        match = cls.db.find(labels=cls.class_label)
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
        print("result of update query in delete_class(): ", result)
        number_nodes_deleted = result.get("nodes_deleted", 0)   # 0 is given as default value, if not present

        if number_nodes_deleted < 1:     # If no nodes were deleted
            if safe_delete:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist, or data nodes are attached to it")
            else:
                raise Exception(f"Nothing was deleted; potential cause: the specified Class (`{name}`) doesn't exist")



    @classmethod
    def allows_data_nodes(cls, class_name: str) -> bool:
        """
        Determine if the given Class allows data nodes directly linked to it

        :param class_name:  Name of the Class
        :return:            True if allowed, or False if not
                            If the Class doesn't exist, raise an Exception
        """
        class_node_dict = cls.db.get_record_by_primary_key(labels="CLASS", primary_key_name="name", primary_key_value=class_name)

        if class_node_dict == None:
            raise Exception(f"Class named {class_name} not found in the Schema")

        if "no_datanodes" in class_node_dict:
            return not class_node_dict["no_datanodes"]

        return True    # If key is not in dictionary, then it defaults to True




    ###########     RELATIONSHIPS AMONG CLASSES     ###########

    @classmethod
    def create_class_relationship(cls, from_id: int, to_id: int, rel_name="INSTANCE_OF") -> None:
        """
        Create a relationship (provided that it doesn't already exist) with the specified name
        between the 2 existing Class nodes (identified by their schema_id),
        going in the from -> to direction direction.

        In case of error, an Exception is raised

        Note: multiple relationships by the same name between the same nodes are allowed by Neo4j,
              as long as the relationships differ in their attributes

        TODO: add a method that reports on all existing relationships among Classes?
        TODO: allow to alternatively specify the classes by name
        TODO: allow properties on the relationship

        :param from_id:     schema_id of one existing Class node
        :param to_id:       schema_id of another existing Class node
        :param rel_name:    Name of the relationship to create, in the from -> to direction
                                (blanks allowed)
        :return:            None
        """
        assert rel_name, "create_class_relationship(): A name must be provided for the new relationship"

        q = f'''
            MATCH (from:CLASS {{schema_id: $from_id}}), (to:CLASS {{schema_id: $to_id}})
            MERGE (from)-[:`{rel_name}`]->(to)
            '''

        result = cls.db.update_query(q, {"from_id": from_id, "to_id": to_id})
        #print("result of update_query in create_subclass_relationship(): ", result)
        if result.get("relationships_created") != 1:
            raise Exception(f"Failed to create new relationship from node with Schema_id {from_id} to node with Schema_id {to_id}")



    @classmethod
    def rename_class_rel(cls, from_class: int, to_class: int, new_rel_name) -> bool:    #### NOT IN CURRENT USE
        """
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
            match_from = cls.db.find(labels="CLASS", key_name="name", key_value=from_class, dummy_node_name="from")
            match_to = cls.db.find(labels="CLASS", key_name="name", key_value=to_class, dummy_node_name="to")
            # Remove the specified relationship between them
            number_removed = cls.db.remove_edges(match_from=match_from, match_to=match_to, rel_name=rel_name)
        except Exception as ex:
            raise Exception(f"Failed to delete the `{rel_name}` relationship from Schema Class `{from_class}` to Schema Class `{to_class}`. {ex}")

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
        match_from = cls.db.find(labels="CLASS", key_name="name", key_value=from_class, dummy_node_name="from")
        match_to = cls.db.find(labels="CLASS", key_name="name", key_value=to_class, dummy_node_name="to")
        return cls.db.edges_exist(match_from=match_from, match_to=match_to, rel_name=rel_name)



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
        Relationships are followed in the OUTbound direction

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


        return result



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




    #####################################################################################################
    #                                                                                                   #
    #                                   ~ PROPERTIES-RELATED ~                                          #
    #                                                                                                   #
    #####################################################################################################

    @classmethod
    def get_class_properties(cls, schema_id: int, include_ancestors=False, sort_by_path_len=False) -> list:
        """
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
    def add_properties_to_class(cls, class_id: int, property_list: [str]) -> int:
        """
        Add a list of Properties to the specified (ALREADY-existing) Class.
        The properties are assigned an inherent order (an attribute named "index", starting at 1),
        based on the order they appear in the list.
        If other Properties already exist, extend the existing numbering.
        TODO: Offer a way to change the order of the Properties,
              maybe by first deleting all Properties and then re-adding them

        NOTE: if the Class doesn't already exist, use new_class_with_properties() instead
        TODO: Offer option to specify the class by name.

        :param class_id:        Integer with the schema_id of the Class to which attach the given Properties
        :param property_list:   A list of strings with the names of the properties, in the desired default order
                                    Whitespace in any of the names gets stripped out.
                                    If any name is a blank string, an Exception is raised
        :return:                The number of Properties added (might be zero if the Class doesn't exist)
        """

        assert type(class_id) == int, "Argument `class_id` in add_properties_to_class() must be an integer"
        assert type(property_list) == list, "Argument `property_list` in add_properties_to_class() must be a list"
        assert cls.class_id_exists(class_id), f"No Class with ID {class_id} found in the Schema"


        clean_property_list = [prop.strip() for prop in property_list]
        for prop_name in clean_property_list:
            assert prop_name != "", "Unacceptable Property name, either empty or blank"
            assert type(prop_name) == str, "Unacceptable non-string Property name"

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
        Create a new Class node, with the specified name, and also create the specified Properties nodes,
        and link them together with "HAS_PROPERTY" relationships.

        Return the auto-incremented unique ID ("scheme ID") assigned to the new Class.
        Each Property node is also assigned a unique "scheme ID";
        the links are assigned an auto-increment index, representing the default order of the Properties.

        If a class_to_link_to name is specified, link the newly-created Class node to that existing Class node,
        using an outbound relationship with the specified name.  Typically used to create "INSTANCE_OF"
        relationships from new Classes.

        If a Class with the given name already exists, nothing is done,
        and an Exception is raised.

        NOTE: if the Class already exists, use add_properties_to_class() instead

        :param class_name:      String with name to assign to the new class
        :param property_list:   List of strings with the names of the Properties, in their default order (if that matters)
        :param code:            Optional string indicative of the software handler for this Class and its subclasses
        :param schema_type      Either "L" (Lenient) or "S" (Strict).  Explained under the class-wide comments
        :param class_to_link_to If this name is specified, and a link_to_name (below) is also specified,
                                    then create an OUTBOUND relationship from the newly-created Class
                                    to this existing Class
        :param link_to_name     Name to use for the above relationship, if requested.  Default is "INSTANCE_OF"

        :return:                If successful, the integer "schema_id" assigned to the new Class;
                                otherwise, raise an Exception
        """
        # TODO: it would be safer to use fewer Cypher transactions; right now, there's the risk of
        #       adding a new Class and then leaving it w/o properties or links, in case of mid-operation error

        new_class_id = cls.create_class(class_name, code=code, schema_type=schema_type)
        cls.debug_print(f"Created new schema CLASS node (name: `{class_name}`, Schema ID: {new_class_id})")

        number_properties_added = cls.add_properties_to_class(new_class_id, property_list)
        if number_properties_added != len(property_list):
            raise Exception(f"The number of Properties added ({number_properties_added}) does not match the size of the requested list: {property_list}")

        cls.debug_print(f"{number_properties_added} Properties added to the new Class: {property_list}")

        if class_to_link_to and link_to_name:
            # Create a relationship from the newly-created Class to an existing Class whose name is given by class_to_link_to
            parent_id = NeoSchema.get_class_id(class_name = class_to_link_to)
            print(f"parent_id (ID of `{class_to_link_to}` class): ", parent_id)
            try:
                NeoSchema.create_class_relationship(from_id=new_class_id, to_id=parent_id, rel_name =link_to_name)
            except Exception as ex:
                raise Exception(f"New Class ({class_name}) created successfully, but unable to link it to the `{class_to_link_to}` class. {ex}")

        return new_class_id



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

        match = cls.db.find(labels="CLASS", key_name="code", key_value=schema_code)
        result = cls.db.get_nodes(match, single_cell="schema_id")

        if result is None:
            return -1

        return result




    #####################################################################################################
    #                                                                                                   #
    #                                       ~ DATA POINTS ~                                             #
    #                                                                                                   #
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
    def fetch_data_point(cls, item_id: int, labels=None, properties=None) -> dict:
        """
        Return a dictionary with all the key/value pairs of the attributes of given data point

        :param item_id:     To uniquely identify the data node
        :param labels:      OPTIONAL (generally, redundant) ways to locate the data node
        :param properties:  OPTIONAL (generally, redundant) ways to locate the data node
        :return:            A dictionary with all the key/value pairs, if found; or {} if not
        """
        match = cls.db.find(key_name="item_id", key_value=item_id,
                            labels=labels, properties=properties)
        return cls.db.get_nodes(match, single_row=True)



    @classmethod
    def add_data_point(cls, class_name="", schema_id=None,
                       data_dict=None, labels=None,
                       connected_to_id=None, connected_to_labels=None, rel_name=None, rel_dir="OUT", rel_prop_key=None, rel_prop_value=None,
                       new_item_id=None, return_item_ID=True) -> int:
        """
        Add a new data node, of the Class specified by name or ID,
        optionally linked to another, already existing, data node.
        Optionally specify another DATA node to connect the new node to.
        The new data node, if successfully created, will be assigned a unique value for its field item_id
        If the requested Class doesn't exist, an Exception is raised

        EXAMPLES:   add_data_point(class_name="Cars", {"make": "Toyota", "color": "white"}, labels="car")
                    add_data_point(schema_id=123,     {"make": "Toyota", "color": "white"}, labels="car",
                                   connected_to_id=999, connected_to_labels="salesperson", rel_name="SOLD_BY", rel_dir="OUT")
                    assuming there's an existing class named "Cars" and an existing data point with item_id = 999, and label "salesperson"

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails
        :param data_dict:       An optional dictionary with the properties of the new data point.  EXAMPLE: {"make": "Toyota", "color": "white"}
        :param labels:          String or list of strings with label(s) to assign to new data node; if not specified, use the Class name

        :param connected_to_id: Int or None.  To optionally specify another DATA node to connect the new node to
                                        EXAMPLE: the item_id of a data point representing a particular salesperson or dealership

        The following group only applicable if connected_to_id isn't None
        :param connected_to_labels:     EXAMPLE: "salesperson"
        :param rel_name:        Str or None.  EXAMPLE: "SOLD_BY"
        :param rel_dir:         Str or None.  Either "OUT" (default) or "IN"
        :param rel_prop_key:    Str or None.  Ignored if rel_prop_value is missing
        :param rel_prop_value:  Str or None.  Ignored if rel_prop_key is missing

        :param new_item_id:     Normally, the Item ID is auto-generated, but it can also be provided (Note: MUST be unique)
        :param return_item_ID:  If True, the returned value is the auto-increment "item_id" value of the node just created;
                                    otherwise, it's its Neo4j ID

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

        if not cls.allows_data_nodes(class_name):
            raise Exception(f"Addition of data nodes to Class `{class_name}` is not allowed by the Schema")


        # In addition to the passed properties for the new node, data nodes contain 2 special attributes: "item_id" and "schema_code";
        # expand cypher_props_dict accordingly
        # TODO: male this part optional
        if not new_item_id:
            new_id = cls.next_available_datapoint_id()      # Obtain (and reserve) the next auto-increment value
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
    def add_and_link_data_point(cls, class_name: str, connected_to_list: [], data_dict=None, labels=None) -> int:
        """
        Create a new data node, of the Class with the given name,
        with the specified optional labels and properties,
        and link it to each of all the EXISTING nodes
        specified in the (possibly empty) list connected_to_list,
        using the various relationship names specified inside that list.

        All the relationships are understood to be OUTbound from the newly-created node -
        and they must be present in the Schema, or an Exception will be raised.

        If the requested Class doesn't exist, an Exception is raised

        The new data node gets assigned a unique "item_id" value (TODO: make optional)

        EXAMPLE:
            add_and_link_data_point(
                                class_name="PERSON",
                                data_dict={"name": "Julian", "city": "Berkeley"},
                                connected_to_list=[ (123, "IS_EMPLOYED_BY") , (456, "OWNS") ]
            )

        Note: this is the Schema layer's counterpart of NeoAccess.create_node_with_children()

        :param class_name:          Name of the Class specifying the schema for this new data point
        :param connected_to_list:   A list of pairs (Neo4j ID value, relationship name)
        :param data_dict:           A dictionary of attributes to give to the new node
        :param labels:              OPTIONAL string or list of strings with label(s) to assign to new data node;
                                        if not specified, use the Class name

        :return:                    If successful, an integer with Neo4j ID of the node just created;
                                        otherwise, an Exception is raised
        """
        new_neo_id = cls.add_data_point(class_name=class_name, data_dict=data_dict, labels=labels,
                                        return_item_ID=False)    # Request that the Neo4j ID be returned

        for link in connected_to_list:
            node_id, rel_name = link    # Unpack
            cls.add_data_relationship(from_id=new_neo_id, to_id=node_id, rel_name=rel_name)

        return new_neo_id



    @classmethod
    def register_existing_data_point(cls, class_name="", schema_id=None,
                                     existing_neo_id=None, new_item_id=None) -> int:
        """
        Register (declare to the Schema) an existing data node with the Schema Class specified by its name or ID.
        An item_id is generated for the data node and stored on it; likewise, for a schema_code (if applicable).
        Return the newly-assigned item_id

        EXAMPLES:   register_existing_data_point(class_name="Chemicals", existing_neo_id=123)
                    register_existing_data_point(schema_id=19, existing_neo_id=456)

        TODO: verify the all the passed attributes are indeed properties of the class (if the schema is Strict)
        TODO: verify that required attributes are present
        TODO: invoke special plugin-code, if applicable

        :param class_name:      The name of the Class that this new data point is an instance of
        :param schema_id:       Alternate way to specify the Class; if both present, class_name prevails

        :param existing_neo_id: Internal ID to identify the node to register with the above Class.
                                TODO: expand to use the find() structure
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

        if not cls.allows_data_nodes(class_name):
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

        print("register_existing_data_point(). New item_id to be assigned to the data node: ", new_item_id)

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

        cls.db.debug_print(q, data_binding, "register_existing_data_point") # Note: this is the special debug print for NeoAccess
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
    def add_data_relationship(cls, from_id: Union[int, str], to_id: Union[int, str], rel_name: str, rel_props = None,
                              labels_from=None, labels_to=None, id_type=None) -> None:
        """
        Add a new relationship with the given name, from one to the other of the 2 given data nodes.
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

        # Create structures later used to locate the two data node
        from_match = NeoSchema.locate_node(node_id=from_id, id_type=id_type, labels=labels_from, dummy_node_name="from")
        to_match   = NeoSchema.locate_node(node_id=to_id,   id_type=id_type, labels=labels_to,   dummy_node_name="to")

        # Get Cypher fragments related to matching the data nodes
        from_node = CypherUtils.extract_node(from_match)
        to_node = CypherUtils.extract_node(to_match)
        where_clause = CypherUtils.combined_where([from_match, to_match])
        data_binding = CypherUtils.combined_data_binding([from_match, to_match])

        # Using the Cypher fragments from above, create a query that looks for a path
        # from the first to the second data nodes, passing thru their classes
        # and thru a link with the same relationship name between those classes;
        # upon finding such a path, join the data points with a relationship
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
            # The following 2 lines will raise an Exception if either data point doesn't exist or lacks a Class
            class_from = cls.class_of_data_point(node_id=from_id, id_type=id_type, labels=labels_from)
            class_to = cls.class_of_data_point(node_id=to_id, id_type=id_type, labels=labels_to)

            #TODO: maybe double-check that the following reported problem is indeed what caused the failure
            raise Exception(f"Cannot add the relationship `{rel_name}` between the data nodes, "
                            f"because no such relationship exists from Class `{class_from}` to Class` {class_to}`. The Schema needs to be modified first")



    @classmethod
    def remove_data_relationship(cls, from_id: int, to_id: int, rel_name: str, labels=None) -> None:
        """
        Drop the relationship with the given name, from one to the other of the 2 given data nodes.
        Note: the data nodes are left untouched.
        If the specified relationship didn't get deleted, raise an Exception

        TODO: verify that the relationship is optional in the schema

        :param from_id:     The "item_id" value of the data node at which the relationship originates
        :param to_id:       The "item_id" value of the data node at which the relationship ends
        :param rel_name:    The name of the relationship to delete
        :param labels:      OPTIONAL (generally, redundant).  Labels required to be on both nodes

        :return:            None.  If the specified relationship didn't get deleted, raise an Exception
        """
        assert rel_name != "", f"remove_data_relationship(): no name was provided for the relationship"

        match_from = cls.db.find(labels=labels, key_name="item_id", key_value=from_id,
                                 dummy_node_name="from")

        match_to =   cls.db.find(labels=labels, key_name="item_id", key_value=to_id,
                                 dummy_node_name="to")

        cls.db.remove_edges(match_from, match_to, rel_name=rel_name)   # This will raise an Exception if no relationship is removed



    @classmethod
    def locate_node(cls, node_id: Union[int, str], id_type=None, labels=None, dummy_node_name="n") -> dict:
        """
        EXPERIMENTAL

        Return the "match" structure to locate a node identified
        either by its Neo4j ID, or by a primary key (with optional label.)

        :param node_id: This is understood be the Neo4j ID, unless an id_type is specified
        :param id_type: For example, "item_id";
                            if not specified, the node ID is assumed to be Neo4j ID's
        :param labels:  (OPTIONAL) Labels - a string or list/tuple of strings - for the node
        :param dummy_node_name: (OPTIONAL) A string with a name by which to refer to the node (by default, "n")

        :return:        A "match" structure
        """
        if id_type:
            match = cls.db.find(key_name=id_type, key_value=node_id, labels=labels, dummy_node_name=dummy_node_name)
        else:
            match = cls.db.find(neo_id=node_id, dummy_node_name=dummy_node_name)

        return match



    @classmethod
    def class_of_data_point(cls, node_id: int, id_type=None, labels=None) -> str:
        """
        Return the name of the Class of the given data point: identified
        either by its Neo4j ID's, or by a primary key (with optional label)

        :param node_id:     Either a Neo4j ID or a primary key value
        :param id_type:     OPTIONAL - name of a primary key used to identify the data node
        :param labels:      Optional string, or list/tuple of strings, with Neo4j labels
        :return:            A string with the name of the Class of the given data point
        """
        match = NeoSchema.locate_node(node_id=node_id, id_type=id_type, labels=labels)

        node = CypherUtils.extract_node(match)
        where_clause = CypherUtils.combined_where([match])
        data_binding = CypherUtils.combined_data_binding([match])

        q = f'''
            MATCH  {node} -[:SCHEMA]-> (class_node :CLASS)
            {where_clause}
            RETURN class_node.name AS name
            '''
        cls.db.debug_print(q, data_binding, "class_of_data_point")

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
    def data_points_of_class(cls, class_name) -> [int]:
        """
        Return the Item ID's of all the Data Points of the given Class
        TODO: offer to optionally use a label

        :param class_name:
        :return:
        """
        q = '''
            MATCH (n)-[:SCHEMA]->(c:CLASS {name: $class_name}) RETURN n.item_id AS item_id
            '''

        res = cls.db.query(q, {"class_name": class_name}, single_column="item_id")

        # Alternate approach
        #match = cls.db.find(labels="CLASS", properties={"name": "Categories"})
        #cls.db.follow_links(match, rel_name="SCHEMA", rel_dir="IN", neighbor_labels="BA")

        return res



    @classmethod
    def data_points_lacking_schema(cls):
        """
        Locate and return all Data Points that aren't associated to any Class
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
    def get_data_point_id(cls, key_value, key_name="item_id") -> int:
        """
        Get the Neo4j ID of a data point given some other primary key

        :return:   An integer with the Neo4j ID of the data point
        """

        match = cls.db.find(key_name=key_name, key_value=key_value)
        result = cls.db.get_nodes(match, return_neo_id=True, single_cell="neo4j_id")

        if result is None:
            raise Exception(f"Unable to find a data node with the attribute `{key_name}={key_value}`")

        return result




    #####################################################################################################
    #                                                                                                   #
    #                                      ~ DATA IMPORT ~                                              #
    #                                                                                                   #
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
        :param provenance:  Metadata (such as a file name) to store in the "source" attribute of the node for the import data

        :return:
        """
        print(f"In import_json_data().  class_name: {class_name} | parse_only: {parse_only} | provenance: {provenance}")
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

        :param data:        A python dictionary or list, with the data to import
        :param class_name:  The name of the Schema Class for the root node(s) of the imported data
        :param provenance:  Optional string to store in a "source" attribute in the root node
                                (only used if the top-level data structure is an object, i.e. if there's a single root node)

        :return:            List of Neo4j ID's of the root node(s) created

        TODO:   * DIRECTION OF RELATIONSHIP (cannot be specified by Python dict/JSON)
                * LACK OF "Import Data" node (ought to be automatically created if needed)
                * LACK OF "BA" (or "DATA"?) labels being set
                * INABILITY TO LINK TO EXISTING NODES IN DBASE (try using: "item_id": some_int  as the only property in nodes to merge)
                * HAZY responsibility for "schema_code" (set correctly for all nodes); maybe ditch to speed up execution
                * OFFER AN OPTION TO IGNORE BLANK STRINGS IN ATTRIBUTES
                * INTERCEPT AND BLOCK IMPORTS FROM FILES ALREADY IMPORTED
        """

        # Create an `Import Data` node for the metadata of the import
        import_metadata = {}
        if provenance:
            import_metadata["source"] = provenance

        metadata_id = cls.add_data_point(class_name="Import Data", data_dict=import_metadata,
                                         return_item_ID=False)      # Return the Neo4j ID

        # Store the import date
        q = f'''
            MATCH (n :`Import Data`) WHERE id(n) = {metadata_id}
            SET n.date = date()
            '''
        cls.db.update_query(q)

        # TODO: catch Exceptions, and store the status and error message on the `Import Data` node

        if type(data) == dict:       # If the top-level Python data structure is dictionary
            # Create a single tree
            cls.debug_print("Top-level structure of the data to import is a Python dictionary")
            # Perform the import
            root_id = cls.create_tree_from_dict(data, class_name)           # This returns a Neo4j ID

            if root_id is None:
                return []
            else:
                root_item_id = root_id
                cls.debug_print(f"***Linking import node (Neo4j ID={metadata_id}) with data root node (Neo4j ID={root_item_id}), thru relationship `imported_data`")
                cls.add_data_relationship(from_id=metadata_id, to_id=root_item_id, rel_name="imported_data")
                return [root_item_id]

        elif type(data) == list:         # If the top-level Python data structure is a list
            # Create multiple unconnected trees
            cls.debug_print("Top-level structure of the data to import is a list")
            node_id_list = cls.create_trees_from_list(data, class_name)         # This returns a list of Neo4j ID's

            for root_item_id in node_id_list:
                cls.debug_print(f"***Linking import node (item_id={metadata_id}) with data root node (Neo4j ID={root_item_id}), thru relationship `imported_data`")
                cls.add_data_relationship(from_id=metadata_id, to_id=root_item_id, rel_name="imported_data")

            return node_id_list

        else:                           # If the top-level data structure is neither a list nor a dictionary
            raise Exception(f"The top-level structure is neither a list nor a dictionary; instead, it's {type(data)}")



    @classmethod
    def create_tree_from_dict(cls, d: dict, class_name: str, level=1) -> Union[int, None]:
        """
        Add a new data node (which may turn into a tree root) of the specified Class,
        with data from the given dictionary:
            1) literal values in the dictionary are stored as attributes of the node, using the keys as names
            2) other values (such as dictionaries or lists) are recursively turned into subtrees,
               linked from the new data node through outbound relationships using the dictionary keys as names

        Return the Neo4j ID of the newly created root node
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
        :param class_name:
        :param level:
        :return:            The auto-increment "item_id" (URI) of the newly created node
        """
        assert type(d) == dict, f"create_tree_from_dict(): the argument `d` must be a dictionary (instead, it's {type(d)})"

        assert cls.class_name_exists(class_name), \
                                f"The value passed for the argument `class_name` ({class_name}) is not a valid Class name"
        schema_id = cls.get_class_id(class_name)


        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")


        cls.debug_print(f"{indent_str}Importing data dictionary, using class `{class_name}`")

        declared_outlinks = cls.get_class_relationships(schema_id=schema_id, link_dir="OUT", omit_instance=True)
        cls.debug_print(f"{indent_str}declared_outlinks: {declared_outlinks}")

        declared_properties = cls.get_class_properties(schema_id, include_ancestors=False)
        cls.debug_print(f"{indent_str}declared_properties: {declared_properties}")

        cls.debug_print(f"{indent_str}Input is a dict with {len(d)} keys: {list(d.keys())}")
        node_properties = {}
        children_info = []          # A list of pairs (Neo4j ID value, relationship name)

        skipped_properties = []
        skipped_relationships = []

        # Loop over all the dictionary entries
        for k, v in d.items():
            debug_info = f"{indent_str}*** KEY-> VALUE: {k} -> {v}"
            # Abridge the info line if excessively long
            max_length = 150
            if len(debug_info) > max_length:
                debug_info = debug_info[:max_length] + " ..."
            cls.debug_print(debug_info)

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
                    subtree_root_class_name = cls.get_linked_class_names(class_name, rel_name=k, enforce_unique=True)
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above dictionary...")
                new_node_id = cls.create_tree_from_dict(d=v, class_name=subtree_root_class_name , level=level + 1)

                if new_node_id is not None:     # If a subtree actually got created
                    children_info.append( (new_node_id, k) )    # Save relationship for use when the node gets created
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
                    subtree_root_class_name = cls.get_linked_class_names(class_name, rel_name=k, enforce_unique=True)
                    cls.debug_print(f"{indent_str}...the relationship `{k}` leads to the following Class: {subtree_root_class_name}")
                except Exception as ex:
                    cls.debug_print(f"{indent_str}Disregarding. {ex}")
                    skipped_relationships.append(k)
                    continue

                # Recursive call
                cls.debug_print(f"{indent_str}Making recursive call to process the above list...")
                new_node_id_list = cls.create_trees_from_list(l=v, class_name=subtree_root_class_name, level=level + 1)
                for child_id in new_node_id_list:
                    children_info.append( (child_id, k) )

            else:
                raise Exception(f"Unexpected type: {type(v)}")

        # End of loop over all the dictionary entries

        # Now, finally CREATE THE NEW NODE, with its attributes and links to children (the roots of the subtrees)
        if len(node_properties) == 0 and len(children_info) == 0:
            cls.debug_print(f"{indent_str}Skipping creating node of class `{class_name}` that has no properties and no children")
            return None   # Using None to indicate "skipped node/subtree"
        else:
            return cls.add_and_link_data_point(class_name=class_name, data_dict=node_properties, connected_to_list=children_info)



    @classmethod
    def create_trees_from_list(cls, l: list, class_name: str, level=1) -> [int]:
        """
        Add a set of new data nodes (the roots of the trees), all of the specified Class,
        with data from the given list.

        Return a list of the Neo4j ID of the newly created nodes

        :param l:           A list of data from which to create a set of trees in the database
        :param class_name:
        :param level:
        :return:            A list of the Neo4j values of the newly created nodes
        """
        assert type(l) == list, f"create_tree_from_dict(): the argument `l` must be a list (instead, it's {type(l)})"

        assert cls.class_name_exists(class_name), \
            f"The value passed for the argument `class_name` ({class_name}) is not a valid Class name"

        indent_spaces = level*4
        indent_str = " " * indent_spaces        # For debugging: repeat a blank character the specified number of times
        cls.debug_print(f"{indent_str}{level}. ~~~~~:")

        cls.debug_print(f"{indent_str}Input is a list with {len(l)} items")

        list_of_child_ids = []

        # Process each element of the list, in turn
        for i, item in enumerate(l):
            cls.debug_print(f"{indent_str}Making recursive call to process the {i}-th list element...")
            if cls.db.is_literal(item):
                item_as_dict = {"value": item}
                new_node_id = cls.create_tree_from_dict(d=item_as_dict, class_name=class_name, level=level + 1)  # Recursive call
                if new_node_id  is not None:     # If a subtree actually got created
                    list_of_child_ids.append(new_node_id)

            elif type(item) == dict:
                new_node_id = cls.create_tree_from_dict(d=item, class_name=class_name, level=level + 1)          # Recursive call
                if new_node_id  is not None:     # If a subtree actually got created
                    list_of_child_ids.append(new_node_id)

            elif type(item) == list:
                new_node_id_list = cls.create_trees_from_list(l=item, class_name=class_name, level=level + 1)   # Recursive call
                list_of_child_ids += new_node_id_list       # Merge of lists

            else:
                raise Exception(f"Unexpected type: {type(item)}")


        return list_of_child_ids




    ########################################################
    #                   ~  EXPORT SCHEMA  ~                #
    ########################################################

    @classmethod
    def export_schema(cls) -> {}:      # TODO: unit testing
        """
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
        # TODO: *** THIS MAY FAIL IF MULTIPLE CALLS ARRIVE ALMOST SIMULTANEOUSLY -> finish switch to using next_autoincrement()

        :return:
        """
        future_value = cls.next_autoincrement("schema_node")    # The better way to do it
        currently_used_value = cls.next_available_id_general([cls.class_label, cls.property_label], "schema_id")    # Old way

        assert future_value == currently_used_value, \
            f"NeoSchema.next_available_id() : mismatch in the 2 auto-incr. values ({future_value} vs. {currently_used_value})"

        return currently_used_value



    @classmethod
    def next_autoincrement(cls, kind: str) -> int:
        """
        This utilizes an ATOMIC database operation to both read and advance the autoincrement counter,
        based on a (single) node with label `Schema Autoincrement`
        and an attribute indicating the desired kind (group);
        if no such node exists (for example, after a new installation), it gets created, and 1 is returned

        :param kind:    A string used to maintain completely separate groups of auto-increment values
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
    def next_available_datapoint_id(cls) -> int:
        """
        Reserve and return the next available auto-increment ID,
        in the separately-maintained group called "data_node".
        This value (currently often referred to as "item_id", and not to be confused
        with the internal ID assigned by Neo4j to each node),
        is meant as a permanent primary key, on which a URI could be based.

        :return:    A unique auto-increment integer used for data nodes
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
    def debug_print(cls, info, trim=False):
        """

        :param info:
        :param trim:
        :return:
        """
        if cls.debug:
            if trim:
                info = cls.db.debug_trim(info)

            print(info)
