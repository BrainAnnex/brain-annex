from BrainAnnex.modules.neo_access import neo_access


class NodeExplorer:
    """

    """
    def __init__(self):
        self.neo = neo_access.NeoAccess()



    def example_node_set(self) -> ([]):
        """
        Provide a hardwired example dataset

        :return: A pair of lists : (headers, records)
        """

        header_list = ["Label", "Name", "Location", "Hours", "URL"]
        record_list = [
                ["Restaurant", "Crepevine", "College Ave, Berkeley", "M-F 8am-9pm; weekend to 10pm", "https://crepevine.com"],
                ["Restaurant", "The Red Sea", "5200 Claremont Ave, at Telegraph, Oakland", "10am-11pm exc. Tue closed", "https://theredsea.com"],
                ["Restaurant", "Ikaros", "3268 Grand Ave, by Lake Merritt", "", "https://ikaros.com"]
                ]

        #node_blocks = [(header_list, record_list)]  # Not yet used; just 1 node block for now

        return (header_list, record_list)



    def all_nodes_by_label(self, label: str) -> tuple:
        """
        Take the union set of all the attributes of the nodes with the given label.

        EXAMPLE: if the nodes for label "client" are [ {'gender': 'M', 'age': 42}, {'gender': 'F', 'age': 21, 'location': "Berkeley"} ]
                 then return
                         (['label', 'gender', 'age', 'location'],
                          [ ['client', 'M', 42, ""] ,
                            ['client', 'F', 21, "Berkeley"]
                          ]
                         )

        :param label:   A Neo4j label
        :return:        A 6-tuple containing (header_list, record_list, inbound_headers, outbound_headers, inbound_counts, outbound_counts)
        """
        db = neo_access.NeoAccess()
        # Retrieve ALL nodes with the specified label
        recordset = db.get_nodes(label, return_nodeid=True, return_labels=True)
                                    # EXAMPLE: [ {"neo4j_id": 145, "neo4j_labels": ["person", "client"], 'gender': 'M', 'age': 42},
                                    #            {"neo4j_id": 222, "neo4j_labels": ["person"], 'gender': 'F', 'age': 21, location: "Berkeley"} ]

        if len(recordset) == 0:
            return ([], [], [], [], 0, 0)     # If no records were found.  Return a 6-tuple with empty lists and zero counts


        # Take the union set of all the nodes' schema
        set_of_headers = set()      # Empty set
        for record in recordset:    # Process each record (which is a dictionary) in turn
            set_of_keys = set(record)   # A set whose elements are all the keys
            set_of_headers = set_of_headers.union(set_of_keys)  # Keep adding to the set any new fields not seen before

        header_list = list(set_of_headers)   # Convert set to list

        # Move the field "neo4j_id" to the front of header_list, if present
        if "neo4j_id" in header_list:
            header_list.remove("neo4j_id")
            header_list = ["neo4j_id"] + header_list

        # Move the field "neo4j_labels" to the front of header_list, if present
        if "neo4j_labels" in header_list:
            header_list.remove("neo4j_labels")
            header_list = ["neo4j_labels"] + header_list


        record_list = []
        for record in recordset:    # Process each record (which is a dictionary) in turn
            new_record = [record.get(field_name, "") for field_name in header_list] # Extract the dictionary values in the same order
                                                                                              #   as the keys in header_list;
                                                                                              #   if not present, use a blank
            record_list.append(new_record)


        inbound_headers = set()     # Empty set
        outbound_headers = set()
        inbound_data = []
        outbound_data = []


        for node in recordset:
            node_id = node["neo4j_id"]
            (parent_list, child_list) = db.get_parents_and_children(node_id)
            # EXAMPLE of individual items in either parent_list or child_list:
            #       {'id': 163, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'}
            node_inbound_headers = {item["rel"] for item in parent_list}    # Set of headers for Inbound Relationship applying to this node
                                                                            # Example: {"r1", "r2"}
            inbound_headers = inbound_headers | node_inbound_headers        # Set Union

            node_outbound_headers = {item["rel"] for item in child_list}    # Set of headers for Inbound Relationship applying to this node
            outbound_headers = outbound_headers | node_outbound_headers     # Set Union

            # Extract inbound relationship data
            node_inbound_labels = self._extract_relationship_data(parent_list)
            print("Inbound data for individual node:", node_inbound_labels) # EXAMPLE: {'HAS_RACE': [['Subject', 233], ['Subject', 236], ['Subject', 225]]}
            # Accumulate for all nodes
            inbound_data.append(node_inbound_labels)


            # Extract outbound relationship data
            node_outbound_labels = self._extract_relationship_data(child_list)
            print("Outbound data for individual node:", node_outbound_labels) # EXAMPLE: {'FROM_DATA': [['Source Data Row', 93], ['Source Data Row', 106]]}
            # Accumulate for all nodes
            outbound_data.append(node_outbound_labels)


        #print("\nOverall Inbound data:", inbound_data)
        #print("Overall Outbound data:\n", outbound_data)

        # Process Inbound data
        inbound_counts = self._extract_relationship_counts(inbound_data, inbound_headers)

        # Process Outbound data
        outbound_counts = self._extract_relationship_counts(outbound_data, outbound_headers)

        """
        # Example, for a dataset with 4 nodes:
        inbound_headers = ["a", "b", "c"]
        outbound_headers = ["X", "Y"]

        inbound_counts = [[2, 5, 1], [1, 1, 3], [4, 0, 4], [5, 2, 5]]
        outbound_counts = [[3, 12] ,[1, 5], [2, 5], [4, 0]]
        """

        return (header_list, record_list, inbound_headers, outbound_headers, inbound_counts, outbound_counts)



    def _extract_relationship_data(self, source_list) -> {}:
        """
        Extract relationship data (either Inbound or Outbound) for a single node

        :param source_list:     For Inbound relationships, this needs to be the list of the node's parents;
                                for Outbound, the list of the node's children.
                                EXAMPLE of individual items in the list:
                                    {'id': 163, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'}

        :return:                A dictionary, for a single node
                                EXAMPLE:  {'HAS_RACE': [['Subject', 233], ['Subject', 225]]}
        """
        node_relationship_dict = {}    # A dictionary, for a single node

        for item in source_list:
            rel_name = item["rel"]                      # EXAMPLE: "R1"
            label_of_rel_source = item["labels"][0]     # For now, just consider the first label.  EXAMPLE: "Label_A"
            id_of_rel_source = item["id"]               # EXAMPLE: 123
            #print("rel_name:", rel_name)
            #print("label_of_rel_source:", label_of_rel_source)
            #print("id_of_rel_source:", id_of_rel_source)

            if rel_name in node_relationship_dict:
                node_relationship_dict[rel_name] += [[label_of_rel_source, id_of_rel_source]]   # If they is already in dictionary, append...
            else:
                node_relationship_dict[rel_name] = [[label_of_rel_source, id_of_rel_source]]    # ...otherwise, set

            #print('~~~~~~~~~~~~~~~~~~~~')

        return node_relationship_dict



    def _extract_relationship_counts(self, relationship_data, relationship_headers) -> []:
        """
        Process the relationship data (inbound or outbound) for a node, to create a list of counts - in the
        same order as the relationship headers

        :param relationship_data:       List of relationship data (one item per node)
                                            EACH item in that list is a dictionary, such as
                                            {'R1': [['label_A', 93], ['label_A', 106]]}
        :param relationship_headers:    List of relationship headers.  EXAMPLE: ['R1', 'R2', 'R3']

        :return:                        A list of list of integers.  EXAMPLE: [[1, 6, 7], [4, 0, 1]]
                                            EACH item (on per node) is a count of relationships to the corresponding header
        """
        relationship_counts = []

        for node_relationship_data in relationship_data:
            # EXAMPLE of node_relationship_data: {'R1': [['label_A', 93], ['label_A', 106]] , 'R2': [['label_B', 88]]}
            #print("Processing node: node_relationship_data = ", node_relationship_data)
            node_relationship_counts = []
            for header in relationship_headers:     # EXAMPLE: 'R1'
                #print("Processing header: ", header)
                extracted = node_relationship_data.get(header, [])   # default to empty list if the header key isn't present in the node_relationship_data dictionary
                #print("extracted relationship data for the node: ", extracted)  # EXAMPLE: [['label_A', 93], ['label_A', 106]]

                out_count = len(extracted)                           # Count how many relationships arrive to (or depart from) this node
                #print("out_count:", out_count)
                node_relationship_counts.append(out_count)

            #print("node_relationship_counts for this row: ", node_relationship_counts) # EXAMPLE: [1, 6, 7] , if there are 3 relationship headers
            relationship_counts.append(node_relationship_counts)                        # Accumulate all the count data for the various nodes
            #print("--- next row ---")

        #print("relationship_counts: ", relationship_counts)

        return relationship_counts      # EXAMPLE: [[1, 6, 7], [4, 0, 1]]



    def export_experimental(self):
        """
        TENTATIVE JSON FORMAT for export/import:

        {
            version: "1.0",

            "key_fields": ["_key"],

            nodes:  [
                {
                    "_key": "d-12",
                    "_neo4j_labels": ["Label A", "Label B"],
                    "_neo4j_id": 123,
                    "field_A": 482,
                    "field_B": "red"
                },
                {
                    "_key": "i-53",
                    "_neo4j_labels": ["Label C"],
                    "_neo4j_id": 456,
                    "field_C": 3.1415
                }
            ],

            edges:  [
                {
                    from: "d-12",
                    to: "i-53",
                    attr: {
                        "cost": "$50",
                        "distance": 82.4
                    }
                }
            ]
        }
        """

        node_id = 1 # TODO: hardwired for testing

        (parent_list, child_list) = self.neo.get_parents_and_children(node_id)
        # EXAMPLE of individual items in either parent_list or child_list:
        #       {'id': 163, 'labels': ['Subject'], 'rel': 'HAS_TREATMENT'}



############################   NEW EXPERIMENTAL STUFF   ############################


    def column_based_results(self, recordset: [{}], use_for_missing=None, row_defining_keys=None):
        """
        Take a row-based Neo4j recordset (for example, as returned by get_nodes),
        and turn it into a column-based one.
        EXAMPLE: turn
                        [   {"gender": "M", "age": 42, "condition_id": 3},
                            {"gender": "F", "age": 16, "location": "Berkeley"}
                        ]
                 into
                        {   'location': [None, 'Berkeley'],
                            'age': [42, 16],
                            'condition_id': [3, None],
                            'gender': ['M', 'F']
                        }

        :param recordset: A list of dictionaries, with each row representing a record (Neo4j node)
                          EXAMPLE: [  {"gender": "M", "age": 42, "condition_id": 3},
                                      {"gender": "F", "age": 16, "location": "Berkeley"}
                                   ]

        :param use_for_missing:     What to use for missing values.  Typically None (default), "", 0, "NaN"

        :param row_defining_keys:   Optionally, designate a row (by index) to define the keys (field names) to use;
                                    any extra field found in other rows will be discarded.
                                    By default, use ALL the keys (field names) found in any row.
                                    (If the passed value isn't a valid row index, it's ignored.)

        :return:          A dictionary of column vectors (as lists)
                          EXAMPLE:  {"gender": ["M", "F"],
                                     "age": [42, 16],
                                     "condition_id": [3, None],
                                     "location": [None, "Berkeley"]
                                    }
        """
        # Extract the property keys (column headers)
        if (row_defining_keys is not None) and (0 <= row_defining_keys < len(recordset)):
            keys = recordset[row_defining_keys].keys()  # Extract the column names from the specified record
        else:
            # Take the union set of all the nodes' keys
            set_of_keys = set()         # Empty set
            for record in recordset:    # Process each record (which is a dictionary) in turn
                new_set_of_keys = set(record)   # A set whose elements are all the keys of the current record
                set_of_keys = set_of_keys.union(new_set_of_keys)  # Keep adding to the set any new fields not seen before

            keys = list(set_of_keys)   # Convert set to list

        #print("keys: ", keys)

        dict_of_column_vectors = {k: []  for k in keys} # Initialize a new dictionary, using the existing keys (field name)
                                                        #       and empty lists (empty column vectors) as values
                                                        #       EXAMPLE: { 'patient_id': [] , 'gender': [] }

        for record in recordset:  # Look at each record (data from a single Neo4j node) in turn
            for prop in keys:       # For each property (data field) in the record
                data_value = record.get(prop, use_for_missing)  # use_for_missing is returned if the lookup fails,
                                                                #       i.e. if that field is not present in  the current record
                dict_of_column_vectors[prop].append(data_value) # Grow the column vectors

        #print("dict_of_column_vectors:", dict_of_column_vectors)  # EXAMPLE: {'patient_id': [123, 99, 414], 'gender': ['M', None, 'F']}
        return dict_of_column_vectors



    def all_nodes_by_label_NEW(self, label: str) -> {}:
        """
        Retrieve all nodes with the specified label, and prepare the data for tabular presentation by the front end.

        :param label:   A string with a Neo4j label
        :return:
        """
        db = neo_access.NeoAccess()
        # TODO: Retrieve ALL nodes with the specified label, and pass the results to self.serialize_nodes()



    def serialize_nodes(self, node_list) -> {}:
        """
        Given the specified nodes, and prepare the data for tabular presentation by the front end.
        Create and return a dictionary meant for direct use by Flask, or to be turned into a JSON string.

        Take the union set of all the nodes' attributes.

        EXAMPLE: if the nodes in the set are
                        N1 (neo4j ID 123, single label "client") : {'gender': 'M', 'location': "New York"}
                        N2 (neo4j ID 99, dual labels "client"/"vendor"): {'gender': 'F', 'age': 21, 'location': "Berkeley"}
                        with the following relationships:
                            A) "FRIENDS_OF" from N1 to N2
                            B) "FRIENDS_OF" from N1 to node outside the set (with label "creature" and id 666)
                            C) "FRIENDS_OF" to N1 from a node outside the set (label "student", id 842)
                            D) "PAID_BY"  to N2 from a node outside the set (labels "payroll"/"payable", id 1000)

                then return
                {  "headers":  [
                                    ["neo4j_labels", "NEO4J_LABELS"],
                                    ["neo4j_id", "NEO4J_ID"],
                                    ["gender"],
                                    ["age", "FLOAT"],
                                    ["location"],
                                    ["FRIENDS_OF", "OUT"],
                                    ["FRIENDS_OF", "IN"],
                                    ["PAID_BY", "IN"]
                               ],
                    "records": [
                                    [
                                        ["client"],
                                        123,
                                        "M",
                                        None,
                                        "New York",
                                        [ [["client"], 99], [["creature"], 666] ] ,
                                        [ [["student"], 842] ],
                                        None
                                    ],
                                    [
                                        ["client", "vendor"],
                                        99,
                                        "F",
                                        22.,
                                        "Berkeley",
                                        None,
                                        [ [["client"], 123] ],
                                        [ [["payroll", "payable"], 1000] ]
                                    ]
                               ]
                }


        :param label:

        :return:    A dictionary with keys "headers" and "records" (for EXAMPLE, see above)
                        headers: a list of 2-element lists, one for each of the pooled attributes, plus relationships (grouped by name, in/out.)
                                 Each element is of the form:  [name, optional_metadata]
                        records: a list of data from the nodes.
                                 Each element is a list in the same order as headers, with entries that may be strings, numbers, None, or lists
        """


        # TODO: get actual data from dbase

        all_data  = {
                    "headers":  [
                                    ["neo4j_labels", "NEO4J_LABELS"],
                                    ["neo4j_id", "NEO4J_ID"],
                                    ["gender"],
                                    ["age", "FLOAT"],
                                    ["location"],
                                    ["FRIENDS_OF", "OUT"],
                                    ["FRIENDS_OF", "IN"],
                                    ["PAID_BY", "IN"]
                               ],
                    "records": [
                                    [
                                        ["client"],
                                        123,
                                        "M",
                                        None,
                                        "New York",
                                        [ [["client"], 99], [["creature"], 666] ] ,
                                        [ [["student"], 842] ],
                                        None
                                    ],
                                    [
                                        ["client", "vendor"],
                                        99,
                                        "F",
                                        22,
                                        "Berkeley",
                                        None,
                                        [ [["client"], 123] ],
                                        [ [["payroll", "payable"], 1000] ]
                                    ]
                               ]
                    }

        return all_data




def test_column_based_results(db):
    # A general situation where different records may agree on some field, but not all
    recordset = [   {"gender": "M", "age": 42, "condition_id": 3},
                    {"gender": "F", "age": 16, "location": "Berkeley"},
                    {"gender": "F"}
                ]

    result = db.column_based_results(recordset)
    assert result == {'location': [None, 'Berkeley', None], 'age': [42, 16, None], 'condition_id': [3, None, None], 'gender': ['M', 'F', 'F']}

    # Same, but use the string "N/A" for missing data entries
    result = db.column_based_results(recordset, use_for_missing="N/A")
    assert result == {'location': ['N/A', 'Berkeley', 'N/A'], 'age': [42, 16, 'N/A'], 'condition_id': [3, 'N/A', 'N/A'], 'gender': ['M', 'F', 'F']}

    # Now let the set of keys (field names) be defined by the 1st (0-th) record - which has the result of dropping the "location" field
    result = db.column_based_results(recordset, row_defining_keys=0)
    assert result == {'age': [42, 16, None], 'condition_id': [3, None, None], 'gender': ['M', 'F', 'F']}

    # If the set of keys (field names) is defined by the last (2nd) record - the only field retained is "gender"
    result = db.column_based_results(recordset, row_defining_keys=2)
    assert result == {'gender': ['M', 'F', 'F']}

    # 2 records that agree on all fields
    recordset = [   {"gender": "M", "age": 42},
                    {"gender": "F", "age": 16}
                ]
    result = db.column_based_results(recordset)
    assert result == {'gender': ['M', 'F'], 'age': [42, 16]}

    # A 1-record, 1-field recordset
    recordset = [ {"gender": "F"} ]
    result = db.column_based_results(recordset)
    assert result == {'gender': ['F']}

    # An empty recordset
    recordset = [ ]
    result = db.column_based_results(recordset)
    assert result == { }
