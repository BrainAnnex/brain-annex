from typing import Union


class CypherUtils:
    """
    Helper class for the class "NeoAccess".

    Most of it, is used for node-matching utilizing the "processed match structure", defined below.

    Meant as a PRIVATE class for NeoAccess; not indicated for the end user.

    A "processed match structure" (a dict) is used to facilitate for a user to specify a node in a wide variety of way - and
    save those specifications, in a "pre-digested" way, to use as needed in Cypher queries.
    It is a Python dictionary with UP TO the following 4 keys (not all are necessarily present):

            1) "node": a string, defining a node in a Cypher query, *excluding* the "MATCH" keyword
            2) "where": a string, defining the "WHERE" part of the subquery (*excluding* the "WHERE"), if applicable;
                        otherwise, a blank
            3) "data_binding": a (possibly empty) data-binding dictionary
            4) "dummy_node_name": a string used for the node name inside the Cypher query (by default, "n");
                                  potentially relevant to the "node" and "where" values


        EXAMPLES:
            *   {"node": "(n  )" , "where": "" , "data_binding": {}, "dummy_node_name": "n"}
            *   {"node": "(p :`person` )" , "where": "" , "data_binding": {}, "dummy_node_name": "p"}
            *   {"node": "(n  )" , "where": "id(n) = 123" , "data_binding": {}, "dummy_node_name": "n"}
            *   {"node": "(n :`car`:`surplus inventory` )" ,
                 "where": "" ,
                 "data_binding": {},
                 "dummy_node_name": "n"}
            *   {"node": "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})",
                 "where": "",
                 "data_binding": {"n_par_1": "F", "n_par_2": 22},
                 "dummy_node_name": "n"}
            *   {"node": "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})",
                 "where": "n.income > 90000 OR n.state = 'CA'",
                 "data_binding": {"n_par_1": "F", "n_par_2": 22},
                 "dummy_node_name": "n"}
            *   {"node": "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})",
                 "where": "n.income > $min_income",
                 "data_binding": {"n_par_1": "F", "n_par_2": 22, "min_income": 90000},
                 "dummy_node_name": "n"}
    """


    @classmethod
    def define_match(cls, labels=None, internal_id=None, key_name=None, key_value=None, properties=None, subquery=None,
                     dummy_node_name="n") -> dict:
        """
        Turn the set of specification into the MATCH part, and (if applicable) the WHERE part,
        of a Cypher query (using the specified dummy variable name),
        together with its data-binding dictionary.

        The keywords "MATCH" and "WHERE" are *not* returned, to facilitate the assembly of larger Cypher queries
        that involve multiple matches.

        ALL THE ARGUMENTS ARE OPTIONAL (no arguments at all means "match everything in the database")
        :param labels:      A string (or list/tuple of strings) specifying one or more Neo4j labels.
                                (Note: blank spaces ARE allowed in the strings)
                                EXAMPLES:  "cars"
                                            ("cars", "vehicles")

        :param internal_id:      An integer with the node's internal ID.
                                If specified, it OVER-RIDES all the remaining arguments, except for the labels

        :param key_name:    A string with the name of a node attribute; if provided, key_value must be present, too
        :param key_value:   The required value for the above key; if provided, key_name must be present, too
                                Note: no requirement for the key to be primary

        :param properties:  A (possibly-empty) dictionary of property key/values pairs, indicating a condition to match.
                                EXAMPLE: {"gender": "F", "age": 22}

        :param subquery:    Either None, or a (possibly empty) string containing a Cypher subquery,
                            or a pair/list (string, dict) containing a Cypher subquery and the data-binding dictionary for it.
                            The Cypher subquery should refer to the node using the assigned dummy_node_name (by default, "n")
                                IMPORTANT:  in the dictionary, don't use keys of the form "n_par_i",
                                            where n is the dummy node name and i is an integer,
                                            or an Exception will be raised - those names are for internal use only
                                EXAMPLES:   "n.age < 25 AND n.income > 100000"
                                            ("n.weight < $max_weight", {"max_weight": 100})

        :param dummy_node_name: A string with a name by which to refer to the node (by default, "n")

        :return:            A dictionary of data storing the parameters of the match.
                            For details, see the info stored in the comments for this Class
        """
        # Turn labels (string or list/tuple of strings) into a string suitable for inclusion into Cypher
        cypher_labels = cls.prepare_labels(labels)     # EXAMPLES:     ":`patient`"
        #               ":`CAR`:`INVENTORY`"

        if internal_id is not None:      # If an internal node ID is specified, it over-rides all the other conditions
            # CAUTION: internal_id might be 0 ; that's a valid Neo4j node ID
            cypher_match = f"({dummy_node_name})"
            cypher_where = f"id({dummy_node_name}) = {internal_id}"
            return {"node": cypher_match, "where": cypher_where, "data_binding": {}, "dummy_node_name": dummy_node_name}


        if key_name and key_value is None:  # CAUTION: key_value might legitimately be 0 or "" (hence the "is None")
            raise Exception("If key_name is specified, so must be key_value")

        if key_value and not key_name:
            raise Exception("If key_value is specified, so must be key_name")


        if properties is None:
            properties = {}

        if key_name in properties:
            raise Exception(f"Name conflict between the specified key_name ({key_name}) "
                            f"and one of the keys in properties ({properties})")

        if key_name and key_value:
            properties[key_name] = key_value


        if subquery is None:
            cypher_clause = ""
            cypher_dict = {}
        elif type(subquery) == str:
            cypher_clause = subquery
            cypher_dict = {}
        else:
            (cypher_clause, cypher_dict) = subquery
            if (cypher_clause is None) or (cypher_clause.strip() == ""):    # Zap any leading/trailing blanks
                cypher_clause = ""
                cypher_dict = {}
            elif cypher_dict is None:
                cypher_dict = {}


        if not properties:
            clause_from_properties = ""
        else:
            # Transform the dictionary properties into a string describing its corresponding Cypher clause,
            #       plus a corresponding data-binding dictionary.
            #       (assuming an implicit AND between the equalities described by the terms in the dictionary)
            #
            #       EXAMPLE:
            #               properties: {"gender": "F", "year first met": 2003}
            #           will lead to:
            #               clause_from_properties = "{`gender`: $n_par_1, `year first met`: $n_par_2}"
            #               props_data_binding = {'n_par_1': "F", 'n_par_2': 2003}

            (clause_from_properties, props_data_binding) = cls.dict_to_cypher(properties, prefix=dummy_node_name + "_par_")

            if not cypher_dict:
                cypher_dict = props_data_binding        # The properties dictionary is to be used as the only Cypher-binding dictionary
            else:
                # Merge the properties dictionary into the existing cypher_dict, PROVIDED that there's no conflict
                overlap = cypher_dict.keys() & props_data_binding.keys()    # Take the set intersection
                if overlap != set():                                        # If not equal to the empty set
                    raise Exception(f"The data-binding dictionary in the `subquery` argument should not contain any keys of the form `{dummy_node_name}_par_i`, where i is an integer. "
                                    f"Those names are reserved for internal use. Conflicting keys: {overlap}")

                cypher_dict.update(props_data_binding)      # Merge the properties dictionary into the existing cypher_dict


        # Start constructing the Cypher string
        cypher_match = f"({dummy_node_name} {cypher_labels} {clause_from_properties})"

        if cypher_clause:
            cypher_clause = cypher_clause.strip()           # Zap any leading/trailing blanks

        match_structure = {"node": cypher_match, "where": cypher_clause, "data_binding": cypher_dict, "dummy_node_name": dummy_node_name}

        return match_structure



    @classmethod
    def assert_valid_match_structure(cls, match: dict) -> None:
        """
        Verify that an alleged "match" dictionary is a valid one; if not, raise an Exception
        TODO: tighten up the checks

        :param match:   A dictionary of data to identify a node, or set of nodes, as returned by match()
        :return:        None
        """
        assert type(match) == dict, f"`match` argument is not a dictionary as expected; instead, it is a {type(match)}"

        assert len(match) == 4, f"the `match` dictionary does not contain the expected 4 entries; instead, it has {len(match)}"

        assert "node" in match, "the `match` dictionary does not contain the expected 'node' key"
        assert "where" in match, "the `match` dictionary does not contain the expected 'where' key"
        assert "data_binding" in match, "the `match` dictionary does not contain the expected 'data_binding' key"
        assert "dummy_node_name" in match, "the `match` dictionary does not contain the expected 'dummy_node_name' key"

        assert type(match["node"]) == str, "the `node` entry in the `match` dictionary is not a string, as expected"
        assert type(match["where"]) == str, f"the `where` entry in the `match` dictionary is not a string, as expected; instead, it is {match['where']}"
        assert type(match["data_binding"]) == dict, "the `data_binding` entry in the `match` dictionary is not a dictionary, as expected"
        assert type(match["dummy_node_name"]) == str, "the `dummy_node_name` entry in the `match` dictionary is not a string, as expected"


    @classmethod
    def assert_valid_internal_id(cls, internal_id: int) -> None:
        """
        Raise an Exception if the argument is not a valid Neo4j internal database ID

        :param internal_id: Alleged Neo4j internal database ID
        :return:            None
        """
        assert type(internal_id) == int, \
            f"assert_valid_internal_id(): Neo4j internal ID's MUST be integers; the value passed was {type(internal_id)}"

        # Note that 0 is a valid Neo4j ID (apparently inconsistently assigned, on occasion, by the database)
        assert internal_id >= 0, \
            f"assert_valid_internal_id(): Neo4j internal ID's cannot be negative; the value passed was {internal_id}"



    @classmethod
    def validate_internal_id(cls, internal_id: int) -> bool:    # TODO: maybe phase out in favor of assert_valid_internal_id()
        """
        Return True if internal_id is a valid ID as used internally by the database
        (aka "Neo4j ID")

        :param internal_id:
        :return:
        """
        return (type(internal_id) == int) and (internal_id >= 0)



    @classmethod
    def process_match_structure(cls, handle: Union[int, dict], dummy_node_name="n") -> dict:
        if cls.validate_internal_id(handle):
            return cls.define_match(internal_id=handle, dummy_node_name=dummy_node_name)

        if handle.get("dummy_node_name") is not None:
            dummy_node_name = handle.get("dummy_node_name") # If a value is already present in the raw match structure,
                                                            # it takes priority

        return cls.define_match(internal_id=handle.get("internal_id"),
                                labels=handle.get("labels"),
                                key_name=handle.get("key_name"), key_value=handle.get("key_value"),
                                properties=handle.get("properties"),
                                subquery=handle.get("clause"),
                                dummy_node_name=dummy_node_name)


    @classmethod
    def validate_and_standardize(cls, match, dummy_node_name="n") -> dict:
        """
        If match is a non-negative integer, it's assumed to be a Neo4j ID, and a match dictionary is created and returned.
        Otherwise, verify that an alleged "match" dictionary is a valid one:
        if yes, return it back; if not, raise an Exception

        TIP:
              Calling methods that accept "match" arguments can have a line such as:
                    match = CypherUtils.validate_and_standardize(match)
              and, at that point, they will be automatically also accepting Neo4j IDs as "matches"

        TODO: also, accept as argument a list/tuple - and, in addition to the above ops, carry out checks for compatibilities

        :param match:           Either a valid Neo4j internal ID, or a "match" dictionary (TODO: or a list/tuple of those)
        :param dummy_node_name: A string with a name by which to refer to the node (by default, "n");
                                    note: this is only used if the `match` argument is a valid Neo4j internal ID

        :return:                A valid "match" structure, i.e. a dictionary of data to identify a node, or set of nodes
        """
        if type(match) == int and match >= 0:       # If the argument "match" is a valid Neo4j ID
            return cls.define_match(internal_id=match, dummy_node_name=dummy_node_name)

        cls.assert_valid_match_structure(match)
        return match



    @classmethod
    def extract_node(cls, match: dict) -> str:
        """
        Return the node information from the given "match" data structure

        :param match:   A dictionary, as created by define_match()
        :return:        A string with the node information.  EXAMPLES:
                            "(n  )"
                            "(p :`person` )"
                            "(n :`car`:`surplus inventory` )"
                            "(n :`person` {`gender`: $n_par_1, `age`: $n_par_2})"
        """
        return match.get("node")


    @classmethod
    def extract_dummy_name(cls, match: dict) -> str:
        """
        Return the dummy_node_name from the given "match" data structure

        :param match:   A dictionary, as created by define_match()
        :return:        A string with the dummy node name (often "n", or "to, or "from")
        """
        return match.get("dummy_node_name")



    @classmethod
    def unpack_match(cls, match: dict, include_dummy=True) -> list:
        """
        Turn the passed "match" dictionary structure into a list containing:
        [node, where, data_binding, dummy_node_name]
        or
        [node, where, data_binding]
        depending on the include_dummy flag

        TODO:   gradually phase out, as more advanced util methods
                make the unpacking of all the "match" internal structure unnecessary
                Maybe switch default value for include_dummy to False...

        :param match:           A dictionary, as created by define_match()
        :param include_dummy:   Flag indicating whether to also include the "dummy_node_name" value, as a 4th element in the returned list
        :return:
        """
        if include_dummy:
            match_as_list = [match.get(key) for key in ["node", "where", "data_binding", "dummy_node_name"]]
        else:
            match_as_list = [match.get(key) for key in ["node", "where", "data_binding"]]

        return match_as_list



    @classmethod
    def check_match_compatibility(cls, match1, match2) -> None:
        """
        If the two given match structures are incompatible (in terms of collision in their dummy node name),
        raise an Exception.

        :param match1:
        :param match2:
        :return:        None
        """
        assert match1.get("dummy_node_name") != match2.get("dummy_node_name"), \
            f"check_match_compatibility(): conflict between 2 matches " \
            f"using the same dummy node name ({match1.get('dummy_node_name')}). " \
            f"Make sure to pass different dummy names to match()"



    @classmethod
    def prepare_labels(cls, labels) -> str:
        """
        Turn the given string, or list/tuple of strings - representing Neo4j labels - into a string
        suitable for inclusion in a Cypher query.
        Blanks ARE allowed in the names.
        EXAMPLES:
            "" or None          give rise to    ""
            "client"            gives rise to   ":`client`"
            "my label"          gives rise to   ":`my label`"
            ["car", "vehicle"]  gives rise to   ":`car`:`vehicle`"

        :param labels:  A string, or list/tuple of strings, representing one or multiple Neo4j labels
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
    def combined_where(cls, match_list: list) -> str:
        """
        Given a list of "match" structures, return the combined version of all their WHERE statements.
        For details, see prepare_where()
        TODO: Make sure there's no conflict in the dummy node names

        :param match_list:  A list of "match" structures
        :return:            A string with the combined WHERE statement,
                            suitable for inclusion into a Cypher query (empty if there were no subclauses)
        """
        where_list = [match.get("where", "") for match in match_list]
        return cls.prepare_where(where_list)



    @classmethod
    def prepare_where(cls, where_list: Union[str, list]) -> str:
        """
        Given a WHERE clauses, or list/tuple of them, combined them all into one -
        and also prefix to the result (if appropriate) the WHERE keyword.
        The combined clauses of the WHERE statement are parentheses-enclosed, to protect against code injection

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

        assert type(where_list) == list or type(where_list) == tuple, \
            f"prepare_where(): the argument must be a string, list or tuple; instead, it was {type(where_list)}"

        purged_where_list = [w for w in where_list if w.strip() != ""]      # Drop all the blank terms in the list

        if len(purged_where_list) == 0:
            return ""

        return "WHERE (" + " AND ".join(purged_where_list) + ")"    # The outer parentheses are to protect against code injection



    @classmethod
    def combined_data_binding(cls, match_list: list) -> dict:
        """
        Given a list of "match" structures, returned the combined version of all their data binding dictionaries.
        TODO: Make sure there's no conflicts
        TODO: Since this also works with a 1-element list, it can be use to simply unpack the data binding from the match structure
              (i.e. ought to drop the "combined" from the name)
        """
        first_match = match_list[0]
        combined_data_binding = first_match.get("data_binding", {})

        for i, match in enumerate(match_list):
            if i != 0:      # Skip the first one, which we already processed above
                new_data_binding = match.get("data_binding", {})
                combined_data_binding.update(new_data_binding)

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
