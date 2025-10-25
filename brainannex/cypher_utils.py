# This file contains 2 helper classes for the GraphAccess library:
#       - CypherBuilder     To store the specs to identify one or more nodes,
#                           and to store Cypher fragments & data-binding dict, to identify one or more nodes (the "PROCESSED match structure")
#       - CypherUtils       Static class to pre-process node specs, plus misc. Cypher-related utilities

from typing import Union, List, Tuple


class CypherBuilder:
    """
    Used to automatically assemble various parts of a Cypher query
    to be used to locate a node, or group of nodes, based on various match criteria.
    (No support for scenarios involving links.)
    
    Objects of this class (sometimes referred to as a "match structures")
    are used to facilitate a user to specify a node in a wide variety of ways - and
    save those specifications, to use as needed in later building Cypher queries.

    NO extra database operations are involved.

    IMPORTANT:  By our convention -
                    if internal_id is provided, all other conditions are DISREGARDED;
                    if it's missing, an implicit AND operation applies to all the specified conditions
                    (Regardless, all the passed data is stored in this object)


    Upon instantiation, two broad actions take place:

    First, validation and storage of all the passed specifications (the "RAW match structure"),
    that are used to identify a node or group of nodes.

    Then the generation and storage of values for the following 6 properties:

        1) "node":  A string, defining a node in a Cypher query, incl. parentheses but *excluding* the "MATCH" keyword
        2) "where": A string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"), if applicable;
                    otherwise, a blank
        3) "clause_binding"     A dict meant to provide the data for a clause
        4) "data_binding":      A (possibly empty) data-binding dictionary
        5) "dummy_node_name":   A string used for the node name inside the Cypher query (by default, "n");
                                potentially relevant to the "node" and "where" values
        6) "cypher":            The complete Cypher query, exclusive of RETURN statement and later parts;
                                the WHERE pass will be missing if there are no clauses

        EXAMPLES:
            *   node: "(n)"
                    where: ""
                    clause_binding: {}
                    data_binding: {}
                    dummy_node_name: "n"
                    cypher: "MATCH (n)"
            *   node: "(p :`person` )"
                    where: ""
                    clause_binding: {}
                    data_binding: {}
                    dummy_node_name: "p"
            *   node: "(n  )"
                    where: "id(n) = 123"
                    clause_binding: {}
                    data_binding: {}
                    dummy_node_name: "n"
            *   node: "(n :`car`:`surplus inventory` )"
                    where: ""
                    clause_binding: {}
                    data_binding: {}
                    dummy_node_name: "n"
            *    node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: ""
                    clause_binding: {}
                    data_binding: {"n_par_1": "F", "n_par_2": 22}
                    dummy_node_name: "n"
            *   node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: "n.income > 90000 OR n.state = 'CA'"
                    clause_binding: {}
                    data_binding: {"n_par_1": "F", "n_par_2": 22}
                    dummy_node_name: "n"
            *   node: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
                    where: "n.income > $min_income"
                    clause_binding:  {"$min_income": 90000}
                    data_binding: {"n_par_1": "F", "n_par_2": 22, "min_income": 90000}
                    dummy_node_name: "n"
    """

    def __init__(self, internal_id=None,
                 labels=None, key_name=None, key_value=None,
                 properties=None,
                 clause=None, clause_binding=None,
                 dummy_name="n"):
        """
        ALL THE ARGUMENTS ARE OPTIONAL (no arguments at all means "match everything in the database")

        :param internal_id: An integer or string with the node's internal database ID.
                                If specified, it will lead to all the remaining arguments being DISREGARDED (though saved)

        :param labels:      A string (or list/tuple of strings) specifying one or more node labels.
                                (Note: blank spaces ARE allowed in the strings)
                                EXAMPLES:  "cars"
                                            ("cars", "powered vehicles")
                            Note that if multiple labels are given, then only nodes possessing ALL of them will be matched;
                            at present, there's no way to request an "OR" operation on labels

        :param key_name:    A string with the name of a node attribute; if provided, key_value must be present, too
        :param key_value:   The required value for the above key; if provided, key_name must be present, too
                                Note: no requirement for the key to be primary

        :param properties:  A (possibly-empty) dictionary of property key/values pairs, indicating a condition to match.
                                EXAMPLE: {"gender": "F", "age": 22}

        :param clause:      Either None, OR a (possibly empty) string containing a Cypher subquery,
                            OR a pair/list (string, dict) containing a Cypher subquery and the data-binding dictionary for it.
                            The Cypher subquery should refer to the node using the assigned dummy_node_name (by default, "n")
                                IMPORTANT:  in the dictionary, don't use keys of the form "n_par_i",
                                            where n is the dummy node name and i is an integer,
                                            or an Exception will be raised - those names are for internal use only
                                EXAMPLES:   "n.age < 25 AND n.income > 100000"
                                            ("n.weight < $max_weight", {"max_weight": 100})

        :param clause_binding:  A dict meant to provide the data for a clause
                                EXAMPLE:  {"max_weight": 100}

        :param dummy_name: A string with a name by which to refer to the nodes (by default, "n") in the clause;
                                only used if a `clause` argument is passed (in the absence of a clause, it's stored as None)
        """
        # The following group of object variables can be thought of as
        #   the "RAW match structure", the criteria to indentify a database node,
        #   or group of nodes.
        self.internal_id = internal_id              # Internal database ID (an int or string)
        self.labels = labels                        # A string (or list/tuple of strings)
        self.key_name = key_name                    # A string with a property name (not necessarily a primary key)
        self.key_value = key_value
        self.properties = properties                # A python dict, containing both the passed properties
                                                    #   and the requested key/value pair, if applicable
        self.clause = clause                        # EXAMPLE:  "n.age < 25 AND n.income > 100000"
                                                    #   (note: if the passed clause contains a data-binding dictionary,
                                                    #          that gets stripped from here, and incorporated into self.data_binding)
        self.clause_binding = clause_binding    # A dict meant to provide the data for a clause
                                                #   EXAMPLE, if the clause is  "n.weight < $max_weight"
                                                #            then a clause_binding of {'max_weight': 100}
        self.dummy_node_name = dummy_name       # Used to refer to the node in Cypher queries.  EXAMPLE: "n"

        # The following group of object variables can be thought of as
        #   the "PROCESSED match structure",
        #   i.e. data ready to be used for query parts to identify the node or nodes
        #   Note: the values get set further below
        self.node = ""                  # It contains filters for labels, for all the passed properties,
                                        #       and for the requested key/value pair, as applicable
                                        # EXAMPLE: "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        self.where = ""                 # EXAMPLES: "id(n) = 123"
                                        #           "n.income > 90000 OR n.state = 'CA'"
        self.data_binding = {}          # For all the passed properties,
                                        #   and for the requested key/value pair, as applicable
                                        #   EXAMPLE: {"n_par_1": "F", "n_par_2": 22}
        self.cypher = ""                # The complete Cypher query, exclusive of RETURN statement and later parts;
                                        #   the WHERE pass will be missing if there are no clauses


        # Validate all the passed arguments, and clean up some of the string values
        self._validate_and_clean()

        # Finalize the object's construction
        self.build_cypher_elements(dummy_name=self.dummy_node_name)



    def _validate_and_clean(self) -> None:
        """
        Validate all the arguments passed to the class constructor, and clean up some of the string values

        :return:    None
        """
        if self.internal_id is not None:
            assert CypherUtils.valid_internal_id(self.internal_id), \
                f"CypherBuilder() instantiation: the argument `internal_id` ({self.internal_id}) " \
                f"is not a valid internal database ID value"

        if self.labels is not None:
            assert (type(self.labels) == str) or (type(self.labels) == list) or (type(self.labels) == tuple), \
                f"CypherBuilder() instantiation: the argument `labels`, " \
                f"if provided, must be a string, or a list/tuple of strings.  The type passed was {type(self.labels)}"

        if self.key_name is not None:
            assert type(self.key_name) == str, \
                f"CypherBuilder(): the argument `key_name`, if provided, must be a string.  The type passed was {type(self.key_name)}"

            self.key_name = self.key_name.strip()           # Zap any leading/trailing blanks

            assert self.key_value is not None, \
                f"CypherBuilder(): if the argument `key_name` is provided, so must be `key_value`"


        if self.key_value is not None:
            assert self.key_name, "CypherBuilder(): If the argument `key_value` is provided, so must be `key_name`"


        if self.properties is None:
            self.properties = {}
        else:
            assert type(self.properties) == dict, \
                f"CypherBuilder(): the argument `properties`, if provided, must be a python dictionary"

        if self.key_name in self.properties:
            raise Exception(f"CypherBuilder(): Name conflict between the specified key_name (`{self.key_name}`) "
                            f"and one of the keys in properties ({self.properties})")


        if self.clause is None:
            self.clause = ""
        else:
            assert type(self.clause) == str, \
                f"CypherBuilder(): the argument `clause`, if provided, must be a string.  EXAMPLE: 'n.age > 21'"

            self.clause = self.clause.strip()          # Zap leading/trailing blanks


        if self.clause_binding is None:
            self.clause_binding = {}
        elif self.clause_binding != {}:
            assert type(self.clause_binding) == dict, \
                "CypherBuilder(): the argument `clause`, if provided must be a dict.  EXAMPLE: {'max_weight': 100}"

            assert self.clause, \
                f"CypherBuilder(): if the argument `clause_binding` is provided, so must be `clause`"



    def build_cypher_elements(self, dummy_name=None) -> None:
        """
        This method manages the parts of the object buildup that depend on the dummy node name.
        Primary use case:
            if called at the end of a new object's instantiation, it finalizes its construction

        Alternate use case:
            if called on an existing object, it will change its structure
                to make use of the given node dummy name, if possible, or raise an Exception if not.
                (Caution: the object will get permanently changed)

        :param dummy_name:  String with the desired dummy name to use to refer to the node in Cypher queries
        :return:            None
        """
        if dummy_name is None:
            dummy_name = self.dummy_node_name
        elif dummy_name != self.dummy_node_name:
            assert not self.clause, \
                f"finalize_dummy_name(): cannot use the dummy name `{dummy_name}` on a CypherBuilder object " \
                f"that contains a clause with a different dummy name (`{self.dummy_node_name}`)"

        if dummy_name is None:
            dummy_name = "n"    # Fallback default

        self.dummy_node_name = dummy_name


        """
        IMPORTANT:  By our convention -
                1) if internal_id is provided, all other conditions are DISREGARDED;
                2) if it's missing, an implicit "AND" operation applies to all the specified conditions
                
                TODO: maybe ditch (1) and give an option to what boolean to use in (2)
        """
        if self.internal_id is not None:    # If an internal node ID is specified, it over-rides all the other conditions
                                            # (note: internal_id might be 0)
            self.node = f"({self.dummy_node_name})"
            self.where = f"id({self.dummy_node_name}) = {self.internal_id}"
            self.data_binding = {}
            self.cypher = f"MATCH {self.node} WHERE {self.where}"
            return


        # If we get here, we're dealing with the case where the internal_id isn't given


        # Turn labels (string or list/tuple of strings) into a string suitable for inclusion into Cypher
        cypher_labels = CypherUtils.prepare_labels(self.labels)     # EXAMPLES:     ":`patient`"
                                                                    #               ":`CAR`:`INVENTORY`"


        properties = self.properties.copy()     # Make a clone, so as to leave self.properties undisturbed

        if self.key_name and self.key_value:
            properties[self.key_name] = self.key_value       # Incorporate key_name/key_value into the properties


        if properties == {}:
            match_from_properties = ""
            if self.clause_binding:
                self.data_binding = self.clause_binding
        else:
            # Transform the dictionary properties into a string describing its corresponding Cypher clause,
            #       plus a corresponding data-binding dictionary.
            #       (assuming an implicit AND between the equalities described by the terms in the dictionary)
            #
            #       EXAMPLE:
            #               properties: {"gender": "F", "year first met": 2003}
            #           will lead to:
            #               match_from_properties = "{`gender`: $n_par_1, `year first met`: $n_par_2}"
            #               props_data_binding = {'n_par_1': "F", 'n_par_2': 2003}

            (match_from_properties, props_data_binding) = CypherUtils.dict_to_cypher(properties, prefix=self.dummy_node_name + "_par_")

            self.data_binding = props_data_binding        # The properties dictionary is to be used as the only Cypher-binding dictionary

            if self.clause_binding != {}:
                # Merge the properties dictionary into the existing cypher_dict, PROVIDED that there's no conflict
                overlap = self.clause_binding.keys()  &  props_data_binding.keys()   # Take the set intersection of their respective keys
                if overlap != set():                                                 # If not equal to the empty set
                    raise Exception(f"The `clause_binding` argument should not contain "
                                    f"any keys of the form `{self.dummy_node_name}_par_i`, where <i> is an integer. "
                                    f"Those names are reserved for internal use. Conflicting keys: {overlap}")

                self.data_binding.update(self.clause_binding)   # Merge the clause_binding dictionary into the data_binding one


        # Start constructing the Cypher string
        self.node = f"({self.dummy_node_name} {cypher_labels} {match_from_properties})"
        if self.clause:
            self.where = self.clause
            self.cypher = f"MATCH {self.node} WHERE ({self.where})"
        else:
            self.where = ""
            self.cypher = f"MATCH {self.node}"



    def __str__(self) -> str:
        """
        Return a description of this object

        :return:
        """
        return f'''Object properties:
                   internal_id: {self.internal_id}
                   labels: {self.labels}
                   key_name: {self.key_name}
                   key_value: {self.key_value}
                   properties: {self.properties}
                   clause: {self.clause}
                   clause_binding: {self.clause_binding}
                   dummy_node_name: {self.dummy_node_name}
                   
                   node: {self.node}
                   where: {self.where}
                   
                   data_binding: {self.data_binding}
                   cypher: {self.cypher}
                '''



    def extract_node(self) -> str:
        """
        Return the node information to be used in composing Cypher queries

        :return:        A string with the node information, as needed by Cypher queries.  EXAMPLES:
                            "(n  )"
                            "(p :`person` )"
                            "(n :`car`:`surplus inventory` )"
                            "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        """
        return self.node


    def extract_dummy_name(self) -> str:
        """
        Return the dummy node name to be used in composing Cypher queries

        :return:    A string with the dummy node name to use in the Cypher query (often "n" , or "to" , or "from")
        """
        return self.dummy_node_name


    def unpack_match(self) -> tuple:
        """
        Return a tuple containing:
        (node, where, data_binding, dummy_node_name) ,
        for use in composing Cypher queries

        :return:    A tuple containing (node, where, data_binding, dummy_node_name)
                        1) "node":  a string, defining a node in a Cypher query,
                                    incl. parentheses but *excluding* the "MATCH" keyword
                        2) "where": a string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"),
                                    if applicable;  otherwise, a blank
                        3) "data_binding":      a (possibly empty) data-binding dictionary
                        4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                                potentially relevant to the "node" and "where" values
        """
        return (self.node, self.where , self.data_binding, self.dummy_node_name)



    def extract_where_clause(self) -> str:
        """
        Cleanup the WHERE clause, and prefix the "WHERE" keyword as needed

        :return:
        """
        if self.where:
            return "WHERE ({self.where})"

        return ""



    def assert_valid_structure(self) -> None:
        """
        Verify that the object is a valid one (i.e., correctly initialized); if not, raise an Exception
        TODO: NOT IN CURRENT USE.  Perhaps to phase out, or keep it but tighten its tests

        :return:        None
        """
        assert type(self.node) == str, "the `node` attribute is not a string, as expected"
        assert type(self.where) == str, f"the `where` attribute is not a string, as expected; instead, it is {self.where}"
        assert type(self.data_binding) == dict, "the `data_binding` attribute is not a dictionary, as expected"
        assert type(self.dummy_node_name) == str, "the `dummy_node_name` attribute is not a string, as expected"





######################################################################################################################

class CypherUtils:
    """
    Helper STATIC class.
    Meant as a PRIVATE class; not indicated for the end user.
    """

    @classmethod
    def process_match_structure(cls, handle :Union[int, str, CypherBuilder],
                                dummy_node_name=None, caller_method=None) -> CypherBuilder:
        """
        Accept either a valid internal database node ID, or a "CypherBuilder" object,
        and turn it into a "CypherBuilder" object that makes use of the requested dummy name

        Note: no database operation is performed

        :param handle:          EITHER a valid internal database ID (int or string),
                                    OR a "CypherBuilder" object (containing data to identify a node or set of nodes)

        :param dummy_node_name: [OPTIONAL] A string that will be used inside a Cypher query, to refer to nodes
        :param caller_method:   [OPTIONAL] String with name of caller method, only used for error messages

        :return:                A "CypherBuilder" object, used to identify a node,
                                    or group of nodes
        """
        if type(handle) == CypherBuilder:
            # Clone the object, but using the requested dummy name
            if dummy_node_name is None:
                dummy_node_name = handle.dummy_node_name
            elif (dummy_node_name != handle.dummy_node_name):
                    assert not handle.clause, \
                        f"process_match_structure(): Cannot change the dummy node name to `{dummy_node_name}` " \
                        f"on an existing query construct with a clause ({handle.clause}) that uses a different dummy name ({handle.dummy_node_name})"

            return CypherBuilder(internal_id=handle.internal_id,
                 labels=handle.labels, 
                 key_name=handle.key_name, key_value=handle.key_value,
                 properties=handle.properties,
                 clause=handle.clause, clause_binding=handle.clause_binding,
                 dummy_name=dummy_node_name)


        if type(handle) == dict:
            return CypherBuilder(properties=handle, dummy_name=dummy_node_name)


        # Since the `handle` argument is not on object of class "CypherBuilder", nor a dict,
        # then it's expected to be a valid internal dbase ID
        # TODO: maybe skip this redundant test for valid id, as long as the error message will be clear
        if cls.valid_internal_id(handle):    # If the argument "handle" is a valid internal database ID
            return CypherBuilder(internal_id=handle, dummy_name=dummy_node_name)      # Instantiate an object of type "CypherBuilder"
        else:
            if caller_method is None:
                caller_method = "process_match_structure"   # This is used for the error message, below
            raise Exception(f"{caller_method}(): the `match` argument is neither a valid internal database ID, "
                        f"nor an object of type 'cypher_utils.CypherBuilder' ; the passed value is: {handle}")



    @classmethod
    def assemble_cypher_blocks(cls, handle :Union[int, str, CypherBuilder],
                              dummy_node_name=None, caller_method=None) -> tuple:
        """

        :param handle:          EITHER a valid internal database ID (int or string),
                                    OR a "CypherBuilder" object (containing data to identify a node or set of nodes)

        :param dummy_node_name: [OPTIONAL] A string that will be used inside a Cypher query, to refer to nodes
        :param caller_method:   [OPTIONAL] String with name of caller method, only used for error messages

        :return:                A tuple containing (node, where, data_binding, dummy_node_name)
                                    1) "node":  a string, defining a node in a Cypher query,
                                                incl. parentheses but *excluding* the "MATCH" keyword
                                    2) "where": a string, defining the "WHERE" part of the subquery
                                                (*excluding* the "WHERE"),
                                                if applicable;  otherwise, a blank
                                    3) "data_binding":      a (possibly empty) data-binding dictionary
                                    4) "dummy_node_name":   a string used for the node name inside the Cypher query (by default, "n");
                                                            potentially relevant to the "node" and "where" values
        """
        cypher_object = cls.process_match_structure(handle=handle,
                                        dummy_node_name=dummy_node_name, caller_method=caller_method)
        #print(cypher_object)
        return cypher_object.unpack_match()



    @classmethod
    def check_match_compatibility(cls, match1 :CypherBuilder, match2 :CypherBuilder) -> None:
        """
        If the two given "CypherBuilder" objects
        are incompatible - in terms of collision in their dummy node names -
        raise an Exception.

        :param match1:  A "CypherBuilder" object to be used to identify a node, or group of nodes
        :param match2:  A "CypherBuilder" object to be used to identify a node, or group of nodes
        :return:        None
        """
        assert match1.extract_dummy_name() != match2.extract_dummy_name(), \
            f"check_match_compatibility(): conflict between 2 matches " \
            f"using the same dummy node name (`{match1.extract_dummy_name()}`). " \
            f"Make sure to pass different dummy names"





    ############ The following methods make no reference to any "CypherBuilder" object

    @classmethod
    def assert_valid_internal_id(cls, internal_id :Union[int, str]) -> None:
        """
        Raise an Exception if the argument is not a valid internal graph database ID

        :param internal_id: Alleged internal graph database ID
        :return:            None
        """
        assert cls.valid_internal_id(internal_id), \
            f"assert_valid_internal_id(): the passed value ({internal_id}) is not a valid internal graph database ID; " \
            f"a string or non-negative integer expected"



    @classmethod
    def valid_internal_id(cls, internal_id :Union[int, str]) -> bool:
        """
        Return True if `internal_id` is a potentially valid ID for a graph database.
        Note that whether it's actually valid will depend on the specific graph database, which isn't known here.

        EXAMPLES:
            - Neo4j version 4 uses non-negative integers
            - Neo4j version 5 still uses non-negative integers, but also offers an alternative internal ID that is a string
            - Most other graph databases (such as Neptune) use strings

        :param internal_id: An alleged internal database ID
        :return:            True if internal_id is a valid internal database ID, or False otherwise
        """
        # TODO: also invoke the database-specific lower layer InterGraph
        t = type(internal_id)
        if t != int and t != str:
            return False

        if t == int:
            if internal_id < 0:
                return False

        return True



    @classmethod
    def prepare_labels(cls, labels :Union[str, List[str], Tuple[str]]) -> str:
        """
        Turn the given string, or list/tuple of strings - representing one or more database node labels - into a string
        suitable for inclusion into a Cypher query.
        Blanks ARE allowed in the names.
        EXAMPLES:
            "" or None          both give rise to    ""
            "client"            gives rise to   ":`client`"
            "my label"          gives rise to   ":`my label`"
            ["car", "vehicle"]  gives rise to   ":`car`:`vehicle`"

        :param labels:  A string, or list/tuple of strings, representing one or multiple Neo4j labels;
                            it's acceptable to be None
        :return:        A string suitable for inclusion in the node part of a Cypher query
        """
        if not labels:
            return ""   # No labels

        if type(labels) == str:
            labels = [labels]

        cypher_labels = ""
        for single_label in labels:
            cypher_labels += f":`{single_label}`"       # EXAMPLE: ":`label 1`:`label 2`"
            # Note: the back ticks allow the inclusion of blank spaces in the labels

        return cypher_labels



    @classmethod
    def prepare_where(cls, where_list: Union[str, list]) -> str:
        """
        Given a WHERE clause, or list/tuple of them, combined them all into one -
        and also prefix the WHERE keyword to the result (if appropriate).
        The *combined* clauses of the WHERE statement are parentheses-enclosed, to protect against code injection

        EXAMPLES:   "" or "      " or [] or ("  ", "") all result in  ""
                    "n.name = 'Julian'" returns "WHERE (n.name = 'Julian')"
                        Likewise for ["n.name = 'Julian'"]
                    ("p.key1 = 123", "   ",  "p.key2 = 456") returns "WHERE (p.key1 = 123 AND p.key2 = 456)"

        :param where_list:  A string with a subclause, or list or tuple of subclauses,
                            suitable for insertion in a WHERE statement

        :return:            A string with the combined WHERE statement,
                            suitable for inclusion into a Cypher query (empty if there were no subclauses)
        """
        if type(where_list) == str:
            where_list = [where_list]
        else:
            assert type(where_list) == list or type(where_list) == tuple, \
                f"prepare_where(): the argument must be a string, list or tuple; instead, it was of type {type(where_list)}"

        purged_where_list = [w for w in where_list if w.strip() != ""]      # Drop all the blank terms in the list

        if len(purged_where_list) == 0:
            return ""

        return "WHERE (" + " AND ".join(purged_where_list) + ")"    # The outer parentheses are to protect against code injection



    @classmethod
    def prepare_data_binding(cls, data_binding_1 :dict, data_binding_2 :dict) -> dict:
        """
        Return the combined version of two data binding dictionaries
        (without altering the original dictionaries)

        :return:    A (possibly empty) dict with the combined data binding dictionaries,
                        suitable for inclusion into a Cypher query
        """
        assert type(data_binding_1) == dict, "prepare_data_binding(): all arguments must be python dictionaries"
        assert type(data_binding_2) == dict, "prepare_data_binding(): all arguments must be python dictionaries"

        combined_data_binding = data_binding_1.copy()   # Clone the 1st dict, to avoid side effects on it, from the mergebelow
        combined_data_binding.update(data_binding_2)    # Merge the second dict into the clone of the first one

        return combined_data_binding



    @classmethod
    def dict_to_cypher(cls, data_dict: {}, prefix="par_") -> (str, {}):
        """
        Turn a Python dictionary (meant for specifying node or relationship attributes)
        into a string suitable for Cypher queries,
        plus its corresponding data-binding dictionary.

        EXAMPLE :
                {'cost': 65.99, 'item description': 'the "red" button'}

                will lead to the pair:
                    (
                        '{`cost`: $par_1, `item description`: $par_2}',
                        {'par_1': 65.99, 'par_2': 'the "red" button'}
                    )

        Note that backticks are used in the Cypher string to allow blanks in the key names.
        Consecutively-named dummy variables ($par_1, $par_2, etc) are used,
        instead of names based on the keys of the data dictionary (such as $cost),
        because the keys might contain blanks.

        SAMPLE USAGE:
            (cypher_properties, data_binding) = dict_to_cypher(data_dict)

        :param data_dict:   A Python dictionary
        :param prefix:      Optional prefix string for the data-binding dummy names (parameter tokens); handy to prevent conflict;
                                by default, "par_"

        :return:            A pair consisting of a string suitable for Cypher queries,
                                and a corresponding data-binding dictionary.
                            If the passed dictionary is empty or None,
                                the pair returned is ("", {})
        """
        if data_dict is None or data_dict == {}:
            return ("", {})

        assert type(data_dict) == dict, f"The data_dict argument passed to dict_to_cypher() is not a dictionary. Value: {data_dict}"

        rel_props_list = []     # A list of strings
        data_binding = {}
        parameter_count = 1     # Sequential integers used in the data dictionary, such as "par_1", "par_2", etc.

        for prop_key, prop_value in data_dict.items():
            parameter_token =  f"{prefix}{parameter_count}"          # EXAMPLE: "par_3"

            # Extend the list of Cypher property relationships and their corresponding data dictionary
            rel_props_list.append(f"`{prop_key}`: ${parameter_token}")    # The $ refers to the data binding
            data_binding[parameter_token] = prop_value
            parameter_count += 1

        rel_props_str = ", ".join(rel_props_list)

        rel_props_str = "{" + rel_props_str + "}"

        return (rel_props_str, data_binding)
