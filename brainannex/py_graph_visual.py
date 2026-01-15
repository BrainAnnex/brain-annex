# Two classes, "DisplayNetwork" and "PyGraphVisual"


import json




class DisplayNetwork:
    """
    Used to create an HTML file that graphically displays an interactive version
    of graph-network data.
    This HTML file is a scaffold for one or move Vue components that provide the desired functionality
    """

    @classmethod
    def _write_to_file(cls, file_handler, text :str) -> None:
        """
        Write the given text (containing simple text and/or HTML code) into the file managed with
        the given File Handler

        :param file_handler:A file handler, for example as returned by calls to open()
        :param text:        String to write to the file managed by the above file handler
        :return:            None
        """
        file_handler.write(text)
        file_handler.flush()    # To avoid weird buffering issues seen in JupyterLab



    @classmethod
    def _html_header(cls, component_file_css :str) -> str:
        """
        Generate and return the text for the initial part of an HTML file, including the HEAD section.
        Various general JavaScript library files (Vue v.2, D3 and Cytoscape)
        are for now hardwired in the code.

        :param component_file_css:  The full URL of the .CSS file used by our Vue component
        :return:                    A string with HTML code
        """
        return f'''<!-- Auto-generated log file -->
<!DOCTYPE html>
<html lang="en">
<head>  
    <meta charset="UTF-8">
    <title>Cytoscape graphics</title>

    <link type="text/css" rel="stylesheet" href="{component_file_css}">

    <script src="https://life123.science/libraries/vue_2.6.12.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.21.2/cytoscape.umd.js"></script>
</head>

'''


    @classmethod
    def _html_body_start(cls, caption=None) -> str:
        """
        Prepare and return the text for the early part (but post-headers) of an HTML file,
        with an optional text caption to be shown at the top

        :param caption: [OPTIONAL] A string with plain text or HTML code.
                            EXAMPLES:  "Figure 1" ,  "<b>My Header</b>"
        :return:        A string with the HTML code to incorporate into the HTML file being formed
        """
        return f'''
<body>

{caption}
        
'''


    @classmethod
    def _html_vue_container(cls, vue_component :str, component_file :str, graph_data :dict, vue_count=1) -> str:
        """
        Generate and return the HTML for a Vue container (a DIV element with the Vue ROOT component),
        plus a script to instantiate the above Vue root component

        :param vue_component:   A string with the name of the existing Vue.js component to use.
                                    EXAMPLE: "vue_cytoscape_3" (assuming that a .js file with such a Vue component exists)
        :param component_file:  The full name (including path) of the .js file that contains the above component
        :param graph_data:      A python dictionary of data to pass to the Vue component.
                                    It must contain 3 keys: 'structure', 'color_mapping', 'caption_mapping'.
                                    For more details, see export_plot()
        :param vue_count:       An integer used to differentiate between multiple Vue components in the same HTML file.
                                    By default, 1
        :return:                A string with HTML code,
                                    including a SCRIPT element that instantiates the Vue root element
        """

        vue_id = f"vue-root-{vue_count}"    # EXAMPLE: "vue-root-1"

        return f'''

<div id="{vue_id}">   <!-- DIV container for the VUE COMPONENTS below : Vue ROOT element -->

    <{vue_component} v-bind:graph_data="graph_data_json"
                     v-bind:component_id="{vue_count}">        
    </{vue_component}>

</div>    <!--  ~~~~~~~~~~~~~~~~~~~~~  END of Vue root element  ~~~~~~~~~~~~~~~~~  -->



<!--
    Vue components (and other JS).  These must appear AFTER the Vue-containing elements
  -->
<script src="{component_file}"></script>



<script>
    // Instantiation of the Vue ROOT element
    new Vue({{
        el: '#{vue_id}',

        data: {{
            graph_data_json: 
{json.dumps(graph_data, indent=4)}
        }}  // END of data

    }});
</script>
        '''



    @classmethod
    def export_plot(cls, graph_data :dict, graphic_component :str,
                    filename :str, caption="Interactive network plot",
                    vue_comps_dir="https://life123.science/libraries/vue_components/") -> None:
        """
        Send to the given file the HTML data to create a Vue-based display of a network.

        This is meant to work alongside a Vue.js component that expects 2 arguments ("props"):
            1) graph_data
            2) component_id

        :param graph_data:          A python dictionary of data to pass to the Vue component.
                                        It must contain 3 keys:
                                            'structure'         A list of dicts
                                                EXAMPLE (two nodes followed by an edge):
                                                    [{'id': 1, '_node_labels': ['PERSON'], 'name': 'Julian'},
                                                     {'id': 2, '_node_labels': ['CAR'], 'color': 'white'},
                                                     {'id': 'edge-1', 'source': 1, 'target': 2, 'name': 'OWNS'}]

                                                Note: 'id' values can be integers or strings

                                            'color_mapping'     A dict
                                                EXAMPLE: {"label_1": "#8DCC92", "label_2": "#D9C8AD"}

                                            'caption_mapping'   A dict
                                                EXAMPLE: {"label_1": "name", "label_2": "name"}

        :param graphic_component:   The basename of a existing JavaScript and CSS files a
                                        that provides the interactive visualization functionality.
                                        The JS file is expected to implement a Vue.js component by the same name
                                        (but with hyphens in lieu of any underscore in the name, if applicable.)
                                        EXAMPLE: "vue_cytoscape_5" (assuming that a "vue_cytoscape_5.js" file
                                                 and a "vue_cytoscape_5.css" file
                                                 exist in the directory specified by the argument `vue_comps_dir`,
                                                 and that the .js file implements a Vue component named "vue-cytoscape-5")

        :param filename:            The name of the file into which to place the HTML code
                                        to create the interactive network plot.
                                        The suffix ".htm" will be added if it doesn't end with ".htm" or ".html"
                                        If the file already exists, it will get overwritten.
                                        (Note: this file will automatically include an internal reference to the JavaScript
                                        file specified in `graphic_component`)

        :param caption:             [OPTIONAL] String displayed at the top of the HTML file.
                                        By default, "Interactive network plot"

        :param vue_comps_dir:       [OPTIONAL] The full name of the directory where the Vue components reside.
                                        A final "/" in the name is optional.
                                        Note: when this function is used in a Jupyterlab notebook, it's best to use
                                              a URL.  EXAMPLE: "https://life123.science/libraries/vue_components/"
        :return:                    None
        """
        # TODO: split the 'structure' list into separate lists of nodes and edges

        # Perform data validation
        assert type(graph_data) == dict, "export_plot(): argument `graph_data` must be a python dictionary"

        assert len(graph_data) == 3, \
                "export_plot(): argument `graph_data` must contains exactly 3 keys, " \
                "named 'structure', 'color_mapping', 'caption_mapping'"

        assert ('structure' in graph_data) and type(graph_data['structure']) == list, \
                f"export_plot(): the argument `graph_data` must contain a key named 'structure' whose value is a list.  " \
                f"Passed value: {graph_data.get('structure')}"

        assert ('color_mapping' in graph_data) and type(graph_data['color_mapping']) == dict, \
                f"export_plot(): the argument `graph_data` must contain a key named 'color_mapping' whose value is a python dictionary.  " \
                f"Passed value: {graph_data.get('color_mapping')}"

        assert ('caption_mapping' in graph_data) and type(graph_data['caption_mapping']) == dict, \
                f"export_plot(): the argument `graph_data` must contain a key named 'caption_mapping' whose value is a python dictionary.  " \
                f"Passed value: {graph_data.get('caption_mapping')}"

        assert type(filename) == str, "export_plot(): argument `filename` must be a string"

        # Add the suffix ".htm" to `filename`, unless it already end with ".htm" or ".html"
        if not filename.lower().endswith((".htm", ".html")):
            filename += ".htm"


        # Prepare writing into the file (OVERWRITE)
        file_handler = open(filename, "w")      # Create a new file, to write to; over-write if present


        # Export into the HTML file the various Vue-related parts
        if not vue_comps_dir.endswith("/"):
            vue_comps_dir += "/"        # Add the final slash, unless already present

        assert not graphic_component.endswith(".js") and not graphic_component.endswith(".css"), \
            "export_plot(): the argument `graphic_component` should be the BASE NAME of existing .js and .css files; " \
            "do not include any suffix"

        component_file_js = f"{vue_comps_dir}{graphic_component}.js"
        component_file_css = f"{vue_comps_dir}{graphic_component}.css"

        vue_component_name = graphic_component.replace("_", "-")    # Replace each instance of "_" (if any) with "-"

        html = cls._html_header(component_file_css) + cls._html_body_start(caption=f"<h1>{caption}</h1>") + \
               cls._html_vue_container(vue_component=vue_component_name, vue_count=1,
                                       component_file=component_file_js, graph_data=graph_data)

        cls._write_to_file(file_handler, text = html)

        print(f"[GRAPHIC ELEMENT SENT TO FILE `{filename}`]")






########################################################################################################################


class PyGraphVisual:
    """
    Facilitate data preparation for graph visualization that uses the Cytoscape.js library
    """


    def __init__(self, db=None):
        self.db = db                    # Object of "GraphAccess" class

        self.node_structure = []        # The node data needed by the Cytoscape graph visualization.
                                        #   A list of dicts defining nodes.
                                        #   NODES must contain the keys 'id' and '_node_labels'
                                        #   EXAMPLE (2 nodes):
                                        #   [{'id': 1, '_node_labels': ['PERSON'], 'name': 'Julian'},
                                        #    {'id': 2, '_node_labels': ['CAR'], 'color': 'white'}]

        self.edge_structure = []        # The edge data needed by the Cytoscape graph visualization.
                                        #   A list of dicts defining edges.
                                        #   EDGES must contain the keys 'name', 'source', and 'target'
                                        #       (and presumably 'id' is required as well?)
                                        # EXAMPLE (1 edge):
                                        #   [{'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}]
                                        #   The above assumes that nodes 1 and 2 exist

        self.color_mapping = {}         # Mapping a node label to its interior color (the edge color is an automatic variation)
                                        # EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}

        self.caption_mapping = {}       # Mapping a node label to its caption (field name to use on the graph)
                                        # EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}

        self._all_node_ids = []         # List of all the node id's added to the graph so far;
                                        #   used for optional prevention of duplicates

        self._next_available_edge_id = 1 # An auto-increment value


        self.EXTRA_COLORS =  {          # Convenient extra colors, not available thru standard CSS names
            "graph_green": '#8DCC92',
            "graph_darkgreen": '#56947E',
            "graph_teal": '#569481',
            "graph_orange": '#F79768',
            "graph_blue": '#4C8EDB',
            "graph_red": '#F16668',
            "graph_darkbrown": '#604A0D',
            "graph_lightbrown": '#D9C8AD',
            "graph_orchid": '#C990C1',
            "graph_gold": '#FFC455'     # Has a bit more orange than 'gold'
        }



    def __str__(self) -> str:
        """
        Return an overview description of this object

        :return:    A string with a description of this object
        """
        s = f"Object describing a graph containing {len(self.node_structure)} nodes " \
            f"and {len(self.edge_structure)} edges:\n"

        s += f"    Graph Node structure: {self.node_structure}\n"
        s += f"    Graph Edge structure: {self.edge_structure}\n"
        s += f"    Graph color mapping: {self.color_mapping}\n"
        s += f"    Graph caption mapping: {self.caption_mapping}"

        return s



    def get_graph_data(self) -> dict:
        """
        Return a data dictionary with all the relevant visualization info
        (typically, to pass to the front-end, for eventual use by the Cytoscape.js library)

        :return:    A dict with 4 keys - "node_structure", "edge_structure", "color_mapping" and "caption_mapping"
                        For more details, see object constructor
        """
        #TODO: perhaps add a 2nd arg, to specify just one element to be returned
        return {"node_structure": self.node_structure,
                "edge_structure": self.edge_structure,
                "color_mapping": self.color_mapping,
                "caption_mapping": self.caption_mapping}



    def add_node(self, node_id :int|str, labels="", properties=None) -> None:
        """
        From the given data about a database node, assemble and cumulatively store the data
        in a format expected by Cytoscape.js (the visualization front-end).

        Calls with a duplicate node_id are silently disregarded.

        NO database operation is performed.  You need to first extract, or have on hand, that node data.

        EXAMPLE:    given a call to:  add_node(node_id=1, labels=['PERSON'], data={'name': 'Julian'})
                    then the internal format, cumulatively added to self.node_structure, will be:
                    {'id': 1, '_node_labels': ['PERSON'], 'name': 'Julian'}

        :param node_id:     Either an integer or a string to uniquely identify this node in the graph;
                                it will be used to specify the start/end nodes of edges.
                                Typically, use either the internal database ID, or some URI.
                                Records with a duplicate node_id are silently disregarded
        :param labels:      A string, or list of strings, with the node's label(s) used in the graph database;
                                if not used, pass an empty string
        :param properties:  A dict with all the node properties of interest
        :return:            None
        """
        assert isinstance(node_id, (int, str)), \
            "add_node(): the argument `node_id` must be an integer or a string"

        if type(node_id) == str:
            assert node_id != "", "add_node(): cannot use an empty string for the argument `node_id`"


        if node_id in self._all_node_ids:
            return      # Silently disregard duplicates.   TODO: use a "sorted list" for `self._all_node_ids`

        if properties is None:
            properties = {}

        d = properties.copy()     # Make an independent clone of the data dict


        d["id"] = node_id

        if type(labels) == str:
            labels = [labels]   # Turn into a list, if passed as a single string value

        d["_node_labels"] = labels

        self.node_structure.append(d)
        self._all_node_ids.append(node_id)



    def add_edge(self, from_node :str|int, to_node :str|int,
                 name :str, edge_id=None, properties=None) -> None:
        """
        Prepare and store the data for 1 edge, in a format expected by the visualization front-end.

        EXAMPLE:   {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}

        Note that 'id', in this context, is whatever we pass to the visualization module for the nodes;
        not necessarily related to the internal database ID's

        :param from_node:   Integer or a string uniquely identify the "id" of the node where the edge originates
        :param to_node:     Integer or a string uniquely identify the "id" of the node where the edge ends
        :param name:        Name of the relationship
        :param edge_id:     [OPTIONAL]  If not provided, strings such as "edge-123" are used,
                                        with auto-generated consecutive integers
        :param properties:  A dict with all the edge properties of interest

        :return:            None
        """
        # TODO: check if the edge already exists, with same name
        # TODO: unclear if edge id's are really needed by Cytoscape.js

        d = {"name": name, "source": from_node, "target": to_node}

        if edge_id is not None:
            d["id"] = edge_id
        else:
            # Use an auto-increment value of the form "edge-n" for some n
            d["id"] = f"edge-{self._next_available_edge_id}"
            self._next_available_edge_id += 1        # Maintain an auto-increment value for edge ID's

        if properties:
            d.update(properties)    # Also store the edge properties in its dict

        self.edge_structure.append(d)



    def assign_caption(self, label :str, caption="name") -> None:
        """
        Incrementally assign and store a mapping from label name to caption (name of field to use on the display).
        Additional calls to this function will register further assignments.

        EXAMPLES:   assign_caption(label='PERSON', caption='name')
                    assign_caption(label='CAR', caption='color')

        :param label:   The name of a node label
        :param caption: The name of the node field to use on the display (by default, "name")
        :return:        None
        """
        assert type(label) == str, \
            "assign_caption(): the argument `label` must be a string"

        self.caption_mapping[label] = caption



    def assign_color_mapping(self, label :str, color :str) -> None:
        """
        Incrementally assign and store a mapping from label name to color to use for nodes having that label.
        Additional calls to this function will register further assignments.

        EXAMPLES:   assign_color_mapping(label='PERSON', color='purple')
                    assign_color_mapping(label='CAR', color='#FF0088')

        :param label:   The name of a node label
        :param color:   The name (hex string or standard CSS name) of the color to use on the display,
                            OR one of the non-standard names provided by this class,
                            in the object variable self.EXTRA_COLORS
        :return:        None
        """
        if color in self.EXTRA_COLORS:
            color = self.EXTRA_COLORS[color]     # Convert the non-standard name into a numerical value

        self.color_mapping[label] = color




    ############   The methods below require a database connection   ############


    def prepare_recordset(self, id_list :[int|str]) -> [dict]:
        """
        Given a list of node internal id's, construct and return a dataset of their properties,
        plus the special fields `internal_id` and `_node_labels`

        :param id_list: A list of internal id's of database nodes

        :return:        A list of dicts, with the node properties plus the special fields `internal_id` and `_node_labels`
                            EXAMPLE:
                            [{'internal_id': 123, '_node_labels': ['Person'], 'name': 'Julian'}]
        """
        assert type(id_list) == list, \
            f"initialize_graph(): argument `id_list` must be a list; it is of type {type(id_list)}"

        assert self.db, \
            "initialize_graph(): missing database handle; did you pass it when instantiating PyGraphVisual(db=...) ?"

        if id_list == []:
            return []       # No data was passed

        q = f'''
            MATCH (n)
            WHERE ID(n) IN $id_list
            RETURN n
            '''

        #self.db.debug_print_query(q, {"id_list": id_list})
        return self.db.query_extended(q, {"id_list": id_list}, flatten=True)



    def prepare_graph(self, result_dataset :[dict], cumulative=False, add_edges=True, avoid_links=None) -> [int|str]:
        """
        Given a list of dictionary data containing the properties of graph-database nodes - for example,
        as returned by GraphAccess.get_nodes() - construct and save in the object visualization data for them.

        Each dictionary entry MUST have a key named "internal_id".
        If any key named "id" is found, it get automatically renamed "id_original" (since "id" is used by the visualization software);
        if "id_original" already exists, an Exception is raised.  (Copies are made; the original data object isn't affected.)
        Though not required, a key named "_node_labels" is typically present as well.

        Any date/datetime value found in the database will first be "sanitized" into a string representation of the date;
        the time portion, if present, will get dropped

        :param result_dataset:  A list of dictionary data about graph-database nodes;
                                    each dict must contain an entry with the key "internal_id"
        :param cumulative:      If False (default) then any previous call to this function will get ignored,
                                    and a new graph is appended
        :param add_edges:       If True, all existing edges among the displayed nodes
                                    will also be part of the visualization
        :param avoid_links:     Name or list of name of links to avoid including

        :return:                A list of values with the internal databased IDs
                                    of all the nodes added to the graph structure
        """
        assert self.db, \
            "prepare_graph(): missing database handle; did you pass it when instantiating PyGraphVisual(db=...) ?"

        assert type(result_dataset) == list, \
            f"prepare_graph(): argument `id_list` must be a list; it is of type {type(result_dataset)}"

        if len(result_dataset) == 0:
            return []       # No data was passed


        if not cumulative:
            # Reset: clear out any previous graph-structure data, and reset edge number auto-increment
            self.node_structure = []
            self.edge_structure = []
            self._all_node_ids = []
            self._next_available_edge_id = 1


        id_key_renaming = False
        node_list = []      # Running list of internal databased IDs, for nodes in `result_dataset`
        for node in result_dataset:
            internal_id = node.get("internal_id")

            assert internal_id is not None, \
                f"prepare_graph() - the following record lacks the required `internal_id` key: {node}"

            node_clone = node.copy()

            #del node_clone["internal_id"]
            
            if "id" in node_clone:
                assert "id_original" not in node_clone, \
                    f"prepare_graph(): keys named `id` are routinely automatically renamed `id_original`, " \
                    f"but the latter key also already exists!  Found in: {node}"
                node_clone["id_original"] = node_clone["id"] 
                del node_clone["id"]
                id_key_renaming = True

            node_list.append(internal_id)

            if "_node_labels" in node_clone:
                labels = node["_node_labels"]
            else:
                labels = ""


            self.add_node(node_id=internal_id, labels=labels,
                          properties=self.db.sanitize_date_times(node_clone, drop_time=True))


        if add_edges:
            # Search the database for any edges among any of the nodes selected for the visualization
            exclude_clause = ""
            if avoid_links:
                if type(avoid_links) == str:
                    avoid_links = [avoid_links]
                else:
                    assert type(avoid_links) == list,  \
                        f"prepare_graph(): The argument `avoid_links`, if passed, must be a string or a list"

                exclude_clause = f"AND NOT type(r) IN {avoid_links}"
                
                
            q = f'''
                MATCH (n1)-[r]->(n2) 
                WHERE ID(n1) IN $node_list AND ID(n2) IN $node_list 
                {exclude_clause}
                RETURN DISTINCT id(n1) AS from_node, id(n2) AS to_node, 
                       type(r) AS rel_name, properties(r) AS rel_props
                '''

            #self.db.debug_print_query(q, {"node_list": node_list})
            result = self.db.query(q, {"node_list": node_list})


            # "Sanitize" the records, as needed, i.e. make them suitable for JSON serialization, 
            # in anticipation of eventually passing the data to JavaScript 
            for edge in result:
                #print(edge)
                edge_props = self.db.sanitize_date_times(edge["rel_props"], drop_time=True)
                self.add_edge(from_node=edge["from_node"], to_node=edge["to_node"],
                              name=edge["rel_name"], properties=edge_props)

        if id_key_renaming:
            print("prepare_graph(): keys named `id` were found in one or more of the records; "
                  "they were renamed `id_original` to avoid conflict with internal database IDs")
            
        return node_list



    def assemble_graph(self, id_list :[int|str]) -> ([dict],[dict]):
        """
        Given a list of node internal id's, construct and return the data needed by the Cytoscape graph visualization.

        Any date/datetime value found in the database will first be "sanitized" into a string representation of the date;
        the time portion, if present, will get dropped

        :param id_list: A list of internal id's of database nodes
        :return:        A pair with all the data needed by the Cytoscape graph visualization:
                            1) list of dicts defining nodes
                            2) list of dicts defining edges
        """
        recordset = self.prepare_recordset(id_list)
        self.prepare_graph(result_dataset=recordset, cumulative=False, add_edges=True)
        return (self.node_structure , self.edge_structure)



    def link_node_groups(self, group1 :[int|str], group2 :[int|str]) -> None:
        """
        Search the database for any edges from any of the nodes in the 1st group, to any node in the 2nd group.
        Any located edge will be added to the visualization data stored in this object

        :param group1:  List of the internal databased IDs of the 1st group of nodes
        :param group2:  List of the internal databased IDs of the 2nd group of nodes
        :return:        None
        """
        q = '''
            MATCH (n1)-[r]->(n2) 
            WHERE ID(n1) IN $group1 AND ID(n2) IN $group2 
            RETURN DISTINCT id(n1) AS from_node, id(n2) AS to_node, type(r) AS name
            '''

        result = self.db.query(q, {"group1": group1, "group2": group2})
        for edge in result:
            #print(edge)
            self.add_edge(from_node=edge["from_node"], to_node=edge["to_node"], name=edge["name"])
