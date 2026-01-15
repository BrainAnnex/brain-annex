/*  Used in Search function in main UI
 */

Vue.component('vue-cytoscape-5',
    {
        props: {
            graph_data: {
                required: true
            },
            /* graph_data is an object with the following 4 KEYS:

                OLD) "structure"      (an array of objects that represent either nodes or edges).
                        The 'id' key is REQUIRED in each object;
                        a '_node_labels' is typically present in node objects (but not required).
                        Objects representing edges must have the keys 'source', 'target' and 'name',
                        where the values of 'source' are 'target' must be 'id' values on node objects.

                        EXAMPLE (two nodes followed by an edge):
                            [{'id': 1, '_node_labels': ['PERSON'], 'name': 'Julian'},
                             {'id': 2, '_node_labels': ['CAR'], 'color': 'white'},
                             {'id': 'edge-1', 'source': 1, 'target': 2, 'name': 'OWNS'}]

                        Note: 'id' values can be integers or strings
                        
                1) "structure" 
                
                2) "edges"

                3) "color_mapping"
                        Map of node labels to color names
                        EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}

                4) "caption_mapping"
                        Map of node labels to node field (property) names to use for the node's caption
                        EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}
             */

            component_id: {
                default: 1      // Used in forming a unique ID for the DIV that contains the Cytoscape graph
            }
        },



        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div v-bind:id="'cy_' + component_id"
                     class='cytoscape-baseline'
                     v-bind:class="{ 'cytoscape-container-normal': sidebox_expanded , 'cytoscape-container-expanded': !sidebox_expanded }">
                     <!--
                        ******   CYTOSCAPE.js WILL INSERT THE GRAPH HERE!   ******
                       -->
                </div>


                <!-- SIDE BOX, to the right of the main plot : COLLAPSED STATE -->
                <div v-if="!sidebox_expanded" class="cytoscape-legend-collapsed">
                    <img @click='sidebox_expanded = !sidebox_expanded'
                        src='https://life123.science/libraries/vue_components/graphics/thin_left_arrow_32.png'
                        style='padding:0'
                        title='Click to expand sidebar' alt='Click to expand sidebar'
                    >
                </div>


                <!-- SIDE BOX, to the right of the main plot : NORMAL STATE -->
                <div v-if="sidebox_expanded" class="cytoscape-legend">
                    <img @click='sidebox_expanded = !sidebox_expanded'
                        src='https://life123.science/libraries/vue_components/graphics/thin_right_arrow_32.png'
                        style='padding:0'
                        class='clickable-icon'
                        title='Click to collapse sidebar' alt='Click to collapse sidebar'
                    >


                    <!-- If nothing is selected on the plot, show the list of labels... -->
                    <p v-if="!legend_html" class="legend-block">
                        <b>Node labels</b><br><br>
                        <template v-for="color_map in Object.entries(color_mapping)">
                            <div class="label" v-bind:style="{'background-color': color_map[1]}">{{color_map[0]}}</div>
                        </template>

                        <br><br><br>
                        <span style="color: #888; font-style: italic">Select a node or edge<br>on the graph</span>
                        <br>
                        <span style="color: #BBB; font-style: italic">(shift-click for multiple selections)</span>
                    </p>

                    <!-- ...else, if a node or edge is selected on the plot -->
                    <p v-else class="legend-block">
                        SELECTED:
                        <template v-for="label_name in selected_node_labels">
                            <div class="label" v-bind:style="{'background-color': color_mapping[label_name]}">{{label_name}}</div>
                        </template>
                        <br><br>

                        <template v-for="item in legend_html">
                            <span v-html="item"></span>
                            <br>
                        </template>

                        <br><br>
                        <template v-if="selected_element_type == 'node'">
                            <button  @click="hide_node_by_id(selected_element.id)">Hide (node only)</button>
                            <button  @click="hide_node_and_orphans(selected_element.id)">Hide (incl. orphaned neighbors)</button>
                        </template>
                        <br>
                    </p>



                    <!-- Pulldown menu to change desired plot style -->
                    <br>
                    <hr>
                    <p class="legend-block">
                        <i>Plot layout style:</i>
                        <select @change='change_plot_style' v-model="plot_layout_style" style="margin-top:5px">
                            <option value='breadthfirst'>breadthfirst</option>
                            <option value='circle'>circle</option>
                            <option value='concentric'>concentric</option>
                            <option value='cose'>cose</option>
                            <option value='grid'>grid</option>
                            <option value='preset'>preset</option>
                            <option value='random'>random</option>
                    </select>
                    </p>



                    <!-- Edge locator -->
                    <br>
                    <hr>
                    <p class="legend-block">
                        <b>Edges:</b><br>
                        <span style="color: #BBB; font-style: italic">(Click to highlight)</span>
                        <br>
                        <template v-for="name in this.edge_names">
                            <div class="edge  clickable-icon" @click="highlight_edges(name)">
                                {{name}}
                            </div>
                        </template>
                    </p>

                    <br><br><br><br>
                    <span style="color:rgb(187, 187, 187); font-size:13px; margin-left:5px">vue-cytoscape-5 , rev. 1</span>
                </div>      <!-- End of side box -->

            </div>		<!-- End of outer container -->
            `,



        // ---------------------  DATA  ----------------------
        data: function() {
            return {

                nodes: this.graph_data.nodes,   /* An array of objects that represent nodes
                                                   EXAMPLE: [{'id': 1, 'name': 'Julian', '_node_labels': ['PERSON']},
                                                             {'id': 2, 'color': 'white', '_node_labels': ['CAR']}
                                                            ]
                                                 */
                
                edges: this.graph_data.edges,   /* An array of objects that represent edges
                                                   EXAMPLE: [{'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}]
                                                 */

                color_mapping: this.graph_data.color_mapping,
                        /*  Map of node labels to color names
                            EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}
                         */

                caption_mapping: this.graph_data.caption_mapping,
                        /*  Map of node labels to node field (property) names to use for the node's caption
                            EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}
                         */

                label_names: [],        // Array of unique label names throughout the graph
                edge_names: [],         // Array of unique edge names  throughout the graph


                // Data about the currently-selected node or edge
                selected_node_labels: null,     // Array of labels of the currently-selected node
                legend_html: null,              // Array of HTML string to display lines of formatted data on the legend,
                                                //      for the currently-selected node or edge
                selected_element: null,         // Object containing the data of the selected node or edge
                selected_element_type: null,    // Either "node" or "edge"
                //selected_collection: null,      // A cytoscape.Collection (1 node or edge wrapped in a Collection)


                default_color_palette:  {   0: "#ff7577",  // Pale red "#F16668",
                                            1: "cyan",
                                            2: "#C990C1",
                                            3: "#F79768",
                                            4: "#8DCC92",
                                            5: 'yellow',
                                            6: 'lightgray',
                                            7: 'pink',
                                            8: '#f7f2c6',   // Cream
                                            9: '#d3ff75'    // Pale green
                                        },
                next_available_color_palette_index: 0,

                sidebox_expanded: true,             // Flag indicating whether to show the plot legend

                plot_layout_style: "breadthfirst"   // CHOICES: 'grid', 'circle', 'random',
                                                    //          'concentric', 'breadthfirst', 'cose'
            }
        },




        // ---------------------  WATCH  ----------------------

        watch: {
            graph_data(newVal, oldVal)
            // Runs ONLY when the `graph_data` prop changes
            // Note: the "immediate" option cannot be used (presumably because too early in mount cycle)
            {
                console.log(`In 'vue-cytoscape-5': the "watch" on the prop "graph_data" reveals that it has changed`);

                this.nodes = this.graph_data.nodes;
                this.edges = this.graph_data.edges;
                this.extract_names();

                const cy_object = this.create_graph('cy_' + this.component_id);   // MAIN CALL : this will let Cytoscape.js do its thing!
                                                            // EXAMPLE :  "cy_1"  (this name needs to match the ID given
                                                            //                     to the DIV element containing the graph)
                // Save the newly-created Cytoscape object, as metadata for this Vue component
                // Note: the Cytoscape object cannot be simply saved as component data,
                //       because doing so leads to an infinite loop!
                //       According to ChatGPT, "Vue 2 tries to make the Cytoscape object “reactive”,
                //       recursively walks it, and gets trapped in Cytoscape’s internal circular graph."
                this.$options.cy_object = cy_object;    // TODO: try this._liveSelectedNode = cy_object
                                                        //       underscore = not reactive
            }
        },



        // ---------------------  UPDATED  ----------------------
        updated()
        /* The "updated" Vue hook is invoked when the data changes, after the virtual DOM is re-rendered.
            It happens when the props of the component change,
            as well as well a node or edge is selected on the graph (which triggers a legend change),
            but NOT when nodes are moved around in the graph
         */
        {
            //console.log(`The 'vue-cytoscape-5' component is now updated`);
        },



        // ---------------------  MOUNTED  ----------------------
        mounted()
        /* Note: the "mounted" Vue hook is invoked later in the process of launching this component;
         waiting this late is needed.
         Caution must be taken not to re-trigger it from the code in this function,
         or an infinite loop will result!
         */
        {
            console.log(`The 'vue-cytoscape-5' component is now mounted`);

            this.extract_names();

            const cy_object = this.create_graph('cy_' + this.component_id);   // MAIN CALL : this will let Cytoscape.js do its thing!
                                                            // EXAMPLE :  "cy_1"  (this name needs to match the ID given
                                                            //                     to the DIV element containing the graph)

            // Save the newly-created Cytoscape object, as metadata for this Vue component
            // Note: it cannot be simply saved as component data, because doing so triggers another call to this
            //       "mounted" Vue hook function, leading to an infinite loop!
            this.$options.cy_object = cy_object;

            console.log(`    completed execution of mounted()`);
        },



        // ---------------------  COMPUTED  ----------------------
        computed: {

            assemble_element_structure()
            /*  From the current node and edge data, 
                create and return the graph structure needed by Cytoscape.js
                (an array of objects, each with a key named "data")
                EXAMPLE:
                    [
                        {data: {'id': 1, 'name': 'Julian', '_node_labels': ['PERSON']}
                        },
                        {data: {'id': 2, 'color': 'white', '_node_labels': ['CAR']}
                        },
                        {data: {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}
                        }
                    ]
             */
            {
                var cyto_arr = [];      // Array of graph data (nodes + edges) in the format that Cytoscape expects

                for (i in this.nodes) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.nodes[i]};
                    cyto_arr.push(el);
                }
                for (i in this.edges) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.edges[i]};
                    cyto_arr.push(el);
                }
                
                //console.log("assemble_element_structure produced:")
                //console.log(cyto_arr);

                return cyto_arr;
            }

        },  // COMPUTED




        // ---------------------  METHODS  ----------------------
        methods: {

            create_graph(element_id)
            /*  Let Cytoscape.js re-render the requested plot.

                This function needs to be invoked whenever any of the following holds:

                1) this Vue component is first created
                2) its input graph data changes
                3) the user asks for a different layout

                Replace the contents of the desired HTML element (whose id is specified by the given `element_id`)
                with the graphic structure created by Cytoscape

                :param element_id:  The name to match the ID of the Cytoscape DIV element containing the graph.
                                        EXAMPLE: "cy_1"
                :return:            The newly-created Cytoscape object
             */
            {
                console.log(`Running create_graph() to replace the page element with ID '${element_id}'`);

                var cy_object = cytoscape({

                    container: document.getElementById(element_id),     // Container to render in

                    elements: this.assemble_element_structure,          // List of graph elements (nodes & edges)


                    style: [    // The stylesheet for the graph
                        {
                            selector: 'node',       // *NODES*
                            style: {
                                'width': 75,
                                'height': 75,
                                //'shape': 'ellipse',   // Adjust width/height as desired
                                //'label': 'data(name)',
                                'label': this.node_caption_funct,
                                //'background-color': '#8DCC93',
                                'background-color': this.node_color_funct,

                                'border-width': 2,
                                //'border-color': '#5db665',
                                'border-color': this.node_border_color_funct,

                                'font-size': '11px',
                                'color': '#101010',        // Color of the text
                                'text-halign': 'center',
                                'text-valign': 'center'
                            }
                        },

                        {
                            selector: 'edge',      // *RELATIONSHIPS* (LINKS)
                            style: {
                                'width': 2,
                                'line-color': '#C6C6C6',
                                'target-arrow-color': '#C6C6C6',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'label': 'data(name)',
                                'font-size': '10px',
                                'color': '#000',    // Color of the text
                                'text-rotation': 'autorotate',
                                'text-background-color': '#f6f6f6', // Same as graph background
                                'text-background-opacity': 1
                            }
                        },

                        {
                            selector: ':selected',   // *SELECTED* node and links
                            style: {
                                'background-color': 'white',    // For nodes
                                'border-width': 8,              // For the edge of nodes
                                'line-color': 'red'             // For links
                            }
                        }

                    ],  // END of style


                    layout: {
                        name: this.plot_layout_style,   // For example, "circle", "random", etc
                        rows: 3,                        // Applicable to the "grid" layout
                        positions: {
                            // The Y-axis points DOWNWARD
                            // ALTERNATIVE:
                            //       position {x: 0, y: 0}  // In node definitions; can also use renderedPosition
                            // TEST
                            '1': {x: 0,    y: 0},       // Julian
                            '2': {x: 0,    y: 200},     // Toyota
                            '3': {x: -200, y: 0},       // Berkeley
                            '4': {x: 200,  y: 0},       // Bayer
                            '5': {x: 0,    y: -200},    // USA
                            '6': {x: 200,  y: 200}      // Germany
                        }
                    }

                });


                /*
                    Detect all click of interest, and register their handlers
                 */
                cy_object.on('click', this.handle_background_click);                   // A click on the empty space of the graph (the Cytoscape core)
                cy_object.on('click', 'node', this.show_node_info);         // A click on a node on the graph
                cy_object.on('click', 'edge', this.show_edge_info);         // A click on an edge
                cy_object.on('dblclick', 'node', this.handle_double_click);// A double-click on a node on the graph

                /*
                // EXAMPLES of adding nodes
                cy_object.add([
                    { data: { id: 4, _node_labels: ['import'] , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy_object.add([
                    { data: { id: 5, _node_labels: ['SOME_OTHER_LABELS'] , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */

                return cy_object;         // The newly-created Cytoscape object

            },  // create_graph



           node_caption_funct(ele)
            /*  Function to generate the caption to show on the graph, for a given node.
                The caption is based on the node's labels; in the absence of a user-specified mapping,
                an attempt is made to locate typical important field names, such as "name" or "title";
                failing that, the data in the field "id" is used as caption.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")

                :param ele: An object representing a node element;
                                ele.data is a function to which one can pass a field name as argument
                                (such as "id", and will typically "_node_labels")
                :return:    The name of a field who value will be used as node caption in the graph
             */
            {
                //console.log("Determining node caption for node with the following element:");
                //console.log(ele);
                //console.log("    which has id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("_node_labels"));

                const field_to_use_for_caption = this.map_labels_to_caption_field(ele.data("_node_labels"), ele.data("id"));
                //console.log(`Name of field to use for caption: '${field_to_use_for_caption}'`);

                return ele.data(field_to_use_for_caption)
            },


            node_color_funct(ele)
            /*  Function to generate the color to use for the inside of the given node.
                The color is based on the node's labels; in the absence of a user-specified mapping,
                white is used.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                //console.log("Determining color for node with id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("_node_labels"));

                return this.map_labels_to_color(ele.data("_node_labels"));
            },


            node_border_color_funct(ele)
            /*  Function to generate the color to use for the border of the node
                passed as argument (as a graph element).
                The relationship between the interior and edge color is:
                same Hue/Saturation but less Luminosity
             */
            {
                //console.log(this.color_mapping);
                //console.log(ele.data("_node_labels"));
                const interior_color = this.node_color_funct(ele);
                //console.log(interior_color);
                const c = d3.hsl(interior_color);
                //console.log(c);
                const c_new = c.darker(0.635).formatHex();  // Less Luminosity
                //console.log(c_new);
                return c_new;
            },




            /*
                SUPPORT FUNCTIONS
             */

            change_plot_style()
            /*  Invoked as soon as the user selects an entry from the menu of plot styles.
                Re-render the graph with the new plot style
             */
            {
                const cy_object = this.create_graph('cy_' + this.component_id);     // This will let Cytoscape.js re-render the plot
                this.$options.cy_object = cy_object;        // Save the new object.   TODO: could this be done inside create_graph() ?
                this.clear_legend();
            },


            handle_double_click(ev)
            {
                console.log("In handle_double_click()");
                const node = ev.target;                 // A cytoscape.Collection (1 node wrapped in a Collection)

                const cyto_node_data_obj = node.data();// A JavaScript object containing the node’s data fields:
                                                        // the key 'id',
                                                        // plus typically '_node_labels', and all the node properties
                console.log({ ...cyto_node_data_obj }); // Log a snapshot of the object

                const node_id = cyto_node_data_obj.id;

                console.log(node.neighborhood());
                console.log(node.connectedEdges());

                this.hide_node(node);

                //this.hide_node(node_id);
            },



            hide_node(node_collection)
            // Hide a single node (1 node wrapped in a Collection)
            {
                const node_id = node_collection.data().id;
                console.log(`In hide_node().  Hiding node with id: ${node_id}`);


                // Remove the node from the Cytoscape graph (which automatically takes care of hiding its links)
                node_collection.remove();

                // Remove the node from our data structure
                const node_index = this.locate_node_by_id(node_id);
                console.log(`    hide_node(): node located in index position ${node_index}`);

                if (node_index == -1)  {
                    alert(`hide_node(): unable to locate any node with id ${node_id}`);
                    return;
                }

                const adjacent_edges = this.locate_adjacent_edges(node_id);
                console.log(`    hide_node(): the node is attached to the following ${adjacent_edges.length} edges:`);
                console.log(adjacent_edges);

                for (let edge_index of adjacent_edges) {
                    console.log(`    handle_double_click(): hiding EDGE with index position ${edge_index}`);
                    this.edges.splice(edge_index, 1);   // Delete 1 array element in position edge_index
                }

                console.log(`    handle_double_click(): hiding NODE with index position ${node_index}`);
                this.nodes.splice(node_index, 1);       // Delete 1 array element in position node_index
            },



            hide_node_by_id(node_id)
            /*
                :param node_id: A string (always a string!) with the Cytoscape ID of a node
             */
            {
                console.log(`In hide_node_by_id().  Searching for node with id: ${node_id}`);

                const node = this.$options.cy_object.getElementById(node_id);

                const id_check = node.data().id;    // Just for double-check.  TODO: perhaps zap later
                if (node_id != id_check)  {
                    alert("ID mismatch in hide_node_by_id!  No action taken");
                    return;
                }

                this.hide_node(node);
            },


            hide_node_and_orphans(node_id)
            /*
                :param node_id: A string (always a string!) with the Cytoscape ID of a node
             */
            {
                console.log(`In hide_node_and_orphans().  Searching for node with id: ${node_id}`);

                const node = this.$options.cy_object.getElementById(node_id);

                // Get neighboring nodes
                const neighbor_nodes = node.neighborhood().nodes();     // Filter for nodes only
                console.log("Neighbor nodes:");
                console.log({ ...neighbor_nodes }); // Log a snapshot

                // Identify which neighbors would become orphans
                const orphan_nodes = neighbor_nodes.filter(
                                                            n => n.connectedEdges().length === 1
                                                          );
                console.log("Orphan nodes:");
                console.log({ ...orphan_nodes }); // Log a snapshot

                // Remove node + orphans in one operation
                node.union(orphan_nodes).remove();
            },





            hide_node_OLD(node_id)
            /*
                TODO: eliminate
                :param node_id: A string (always a string!) with the Cytoscape ID of a node
             */
            {
                console.log(`In hide_node().  Searching for node with id: ${node_id}`);

                const node = this.$options.cy_object.getElementById(node_id);   // TODO: experimental!

                console.log(`     Alternate way to obtain id: ${node.data().id}`);

                const node_index = this.locate_node_by_id(node_id);
                console.log(`    hide_node(): node located in index position ${node_index}`);

                if (node_index == -1)  {
                    alert(`hide_node(): unable to locate any node with id ${node_id}`);
                    return;
                }

                const adjacent_edges = this.locate_adjacent_edges(node_id);
                console.log(`    hide_node(): the node is attached to the following ${adjacent_edges.length} edges:`);
                console.log(adjacent_edges);

                for (let edge_index of adjacent_edges) {
                    console.log(`    handle_double_click(): hiding EDGE with index position ${edge_index}`);
                    this.edges.splice(edge_index, 1);   // Delete 1 array element in position edge_index
                }

                console.log(`    handle_double_click(): hiding NODE with index position ${node_index}`);
                this.nodes.splice(node_index, 1);       // Delete 1 array element in position node_index

                // Update the graphic object
                const cy_object = this.create_graph('cy_' + this.component_id);     // This will let Cytoscape.js re-render the plot
                this.$options.cy_object = cy_object;        // Save the new object.   TODO: could this be done inside create_graph() ?

            },



            show_node_info(ev)
            /*  Invoked when the user clicks on a node

                :param ev:  Event data object, which contains the key `target`
             */
            {
                console.log(`In show_node_info()`);
                const node = ev.target;                 // A cytoscape.Collection (1 node wrapped in a Collection)

                const cyto_node_data_obj = node.data(); // A JavaScript object containing the node’s data fields:
                                                        // the key 'id',
                                                        // plus typically '_node_labels', and all the node properties
                console.log({ ...cyto_node_data_obj }); // Log a snapshot of the object

                // Save the info about the selected element (in this case a node)
                this.selected_element = { ...cyto_node_data_obj };      // Store a snapshot (NOT cyto_node_data_obj)
                this.selected_element_type = "node";
                //this.selected_collection = node;
                this.populate_legend_from_node(cyto_node_data_obj);
            },


            populate_legend_from_node(node_data_obj)
            /*  Populate the legend with data from the given node

                :param node_data_obj:   Object containing the node’s data fields;
                                            in particular, 'id' and (usually) '_node_labels'
             */
            {
                // Each of the above object's key/value pairs will go into an array element,
                // as an HTML string
                let info_arr = [];
                let html_row_str = "";

                for (k in node_data_obj) {
                    //console.log( k, node_data_obj[k] );
                    if (k == "_node_labels")
                        continue;       // No need to show; labels are shown elsewhere as graphic tags
                    if (k != "name")
                        html_row_str = `<b>${k}</b>: <span class='property-value'>${node_data_obj[k]}</span>`;
                    else
                        html_row_str = `<span style='color: brown; font-weight: bold'>${k}: ${node_data_obj[k]}</span>`;

                    info_arr.push(html_row_str);  // Data to update the UI graph legend
                }
                //console.log(info_arr);

                // Update the legend
                this.legend_html = info_arr;
                this.selected_node_labels = node_data_obj._node_labels;
            },


            show_edge_info(ev)
            /*  Invoked when the user clicks on an edge

                :param ev:  Event data object, which contains the key `target`
             */
            {
                //console.log(`In show_edge_info()`);
                const edge = ev.target;                 // A cytoscape.Collection (1 edge wrapped in a Collection)

                const cyto_edge_data_obj = edge.data(); // A JavaScript object containing the edge’s data fields;
                                                        // in particular, the keys 'source', 'target', 'name' (and typically 'id')
                //console.log({ ...cyto_edge_data_obj }); // Log a snapshot of the object

                // Save the info about the selected element (in this case an edge)
                this.selected_element = { ...cyto_edge_data_obj };      // Store a snapshot
                this.selected_element_type = "edge";
                //this.selected_collection = edge;

                this.populate_legend_from_edge(cyto_edge_data_obj);
            },


            populate_legend_from_edge(edge_data_obj)
            /*  Populate the legend with data from the given edge

                :param edge_data_obj:   Object containing the edge’s data fields;
                                            in particular, 'source', 'target', 'name' and (usually) 'id'
             */
            {
                let info_arr = [];                      // Each of the object key/value pairs will go into an array element, as an HTML string
                for (k in edge_data_obj) {
                    //console.log( k, cyto_data_obj[k] );
                    info_arr.push(`<b>${k}</b>: ${edge_data_obj[k]}`);  // Data to update the UI graph legend
                }
                //console.log(info_arr);

                // Update the legend
                this.legend_html = info_arr;
                this.selected_node_labels = null;
            },


            handle_background_click(ev)
            /*  Invoked when clicking anywhere - including the image background.
                Clear the plot legend (note: if clicking on a node or edge, the legend
                will get set again by the next handler)
            */
            {
                this.clear_legend();
            },


            clear_legend()
            // Unset the details of the node or edge selection (in the legend)
            {
                // The following changes will clear the plot legend
                this.legend_html = null;
                this.selected_node_labels = null;
                this.selected_element = null;
                this.selected_element_type = null;
                //this.selected_collection = null;
            },



            auto_assign_color_to_label(label)
            /*  Automatically assign a color to the specified label,
                in auto-increment fashion from a default color palette.
                If a color association was already present, it will be over-written.

                :param label:   The name of a node label
             */
            {
                if (! (this.next_available_color_palette_index in this.default_color_palette))
                    // If we ran out of available default colors, implement a wrap-around
                    this.next_available_color_palette_index = 0;        // Reset the auto-increment

                let assigned_color = this.default_color_palette[this.next_available_color_palette_index];
                this.color_mapping[label] = assigned_color;
                this.next_available_color_palette_index += 1;
                //console.log(`auto_assign_color_to_label(): assigned color '${assigned_color}' to label '${label}'`);
            },


            map_labels_to_color(labels)
            /*  Given the labels of a node (an array of strings),
                return the name of the color to use for the inside of the node,
                based on what was specified in "color_mapping" from the "graph_data" prop.

                In case of multiple labels, try them sequentially, until a mapping is found.
                The label "BA" is (at least for now) skipped - being a special label.
                TODO: introduce "low-priority" labels.
                If no mapping information is present for any of the labels,
                or if invoked with an undefined value,
                use the color white by default

                :param labels:  Array of strings (the labels of a database node)
                :return:        String with a color name or numeric code
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_color = '#FFFFFF';

                if (labels === undefined)  {
                    console.log("map_labels_to_color(): invoked with `undefined` argument.  Returning default value")
                    return default_color;
                }

                //console.log("map_labels_to_color(): labels: ", labels);    // Example: ["PERSON"]
                //console.log(this.color_mapping);

                for (single_label of labels) {
                    if ((single_label in this.color_mapping) && (single_label != "BA"))  {
                        const color = this.color_mapping[single_label];
                        //console.log(`Using the color '${color}' for the inside of this node`);
                        return color;
                    }
                }

                return default_color;
            },


            map_labels_to_caption_field(labels, node_id)
            /*  Given the labels of a node (an array of strings),
                return the name of the field to use for the node caption,
                based on what was specified in the "caption_mapping" value from the "graph_data" prop.
                In case of multiple labels, try them sequentially, until a mapping is found.

                If no mapping information is present for any of the labels,
                or if invoked with an undefined value,
                try to use any of some common field names, such as "name", "title", etc.
                - or, failing that, use the field name "id" by default

                :param labels:  An array of strings
                :param node_id: An integer or string with the node id
                :return:        String
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_caption_field_name = "id";

                if (labels === undefined)  {
                    //console.log("map_labels_to_caption_field(): invoked with `undefined` argument.  Using a default value")
                }
                else  {
                    //console.log("map_labels_to_caption_field().  labels: ", labels);    // Example: ["PERSON"]
                    //console.log(this.graph_data.caption_mapping);

                    for (single_label of labels) {
                        if (single_label in this.graph_data.caption_mapping)  {
                            //const caption_field_name = this.graph_data.caption_mapping[single_label];
                            const caption_field_name = this.caption_mapping[single_label];
                            //console.log(`Using the field '${caption_field_name}' for the caption of this node`);
                            return caption_field_name;
                        }
                    }
                }

                // If we get here, no mapping information was available.  Try some typical names
                //console.log(`map_labels_to_caption_field(): no mapping information was available. Trying common names for node with id ${node_id}...`);

                const node_index = this.locate_node_by_id(node_id);
                //console.log(node_index);
                if (node_index == -1)  {
                    alert(`map_labels_to_caption_field(): unable to locate node with id ${node_id}`);
                    return default_caption_field_name;
                }

                const node = this.nodes[node_index];    // An object; among its keys will be the node field (property) names


                const common_field_names = ["name", "Name", "title", "Title", "caption", "Caption", "model", "brand"];

                for (let field_name of common_field_names) {
                    if (field_name in node)  {
                        if (labels.length == 1)  {
                            // If there's just 1 label, associate it with this assumed field name, for future reference
                            let single_label = labels[0];
                            console.log(`map_labels_to_caption_field(): Assigning field "${field_name}" for the captions of nodes with label "${single_label}"`);
                            this.caption_mapping[single_label] = field_name;
                        }
                        return field_name;
                    }
                }

                /*
                if ("name" in node)
                    return "name";
                if ("Name" in node)
                    return "Name";
                if ("title" in node)
                    return "title";
                if ("Title" in node)
                    return "Title";
                if ("caption" in node)
                    return "caption";
                if ("Caption" in node)
                    return "Caption";
                if ("model" in node)
                    return "model";
                if ("brand" in node)
                    return "brand";
                */

                // Nothing could be found; fall back to the generic default
                //console.log("map_labels_to_caption_field(): no typical common names identified. Falling back to the generic default");
                return default_caption_field_name;
            },



            extract_names()
            /*  Parse the arrays of node and edge data,
                do some validation,
                and set the variables this.edge_names and this.label_names,
                as well as auto-assign default colors as needed
            */
            {
                console.log(`Entering extract_names()`);

                // Reset the arrays of edge and label names
                this.edge_names = [];
                this.selected_node_labels = [];

                // Parse the array of edges
                for (el of this.edges)  {     // el is an object that represents an edge
                    if (('source' in el) && ('target' in el))  {
                        // Validate the edge...
                        if (! ('name' in el))
                            alert(`Irregularity in passed graph structure: found a nameless edge (from node ${el.source} to node ${el.target})`);

                        if (! this.edge_names.includes(el.name))
                            this.edge_names.push(el.name);      // Keep a running list of all edge names encountered
                        }
                }       
                
                // Parse the array of nodes
                for (el of this.nodes)  {     // el is an object that represents a node       
                    // Validate the node
                    if (! ('id' in el))
                        alert(`Irregularity in passed graph structure: found a node lacking a key named 'id'`);
                    if (! ('_node_labels' in el))
                        alert(`Irregularity in passed graph structure: found a node (id ${el.id}) lacking a key named '_node_labels'`);
                    else  {
                        let labels = el._node_labels;
                        //console.log(`extract_names(): verifying or assigning colors to the labels ${labels}`);
                        if (! Array.isArray(labels))
                            alert(`Irregularity in passed graph structure: found a node (id ${el.id}) whose labels are not an array'`);
                        else {
                            for (let l of labels)  {
                                //console.log(`extract_names(): examining color assignment to label '${l}'`);
                                if (! (l in this.color_mapping))
                                    this.auto_assign_color_to_label(l);
                                    
                                if (! this.selected_node_labels.includes(l))
                                    this.selected_node_labels.push(l);      // Keep a running list of all label names encountered
                            }
                        }
                    }
                }
            },



            highlight_edges(name)
            // Highlight in the graph all edges with the given name
            {
                console.log(`Invoking highlight_edges() with name = "${name}"`);
                //console.log("cy_object:");
                //console.log(this.$options.cy_object);

                // Needs to locate the 'id' of edges from the displayed graph
                // that contains the desired name
                // EXAMPLE (fragment):  {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}

                var found_array = [];   // Array of edge objects

                for (edge of this.edges)  {        // Loop over array of edge objects
                    //console.log(`Examining edge with name "${edge.name}", and id="${edge.id}"`);
                    if (edge.name == name)
                        found_array.push(edge);
                }
                console.log(`Located the following ${found_array.length} edge(s):`);
                console.log(found_array);

                if (found_array.length == 0)  {
                    alert(`The desired edge not found in the graph!`);
                    return;
                }

                // Highlight each located edge in turn
                for (edge of found_array)  {        // Loop over array of edge objects
                    var edge_id = edge.id;
                    console.log(`    attempting to highlight edge with id: "${edge_id}"`);
                    const selector = `#${edge_id}`; // Used to refer to a graph element in the Cytoscape object.
                                                    // EXAMPLE: "#edge-3"

                    this.$options.cy_object.$(selector).select();   // Tell Cytoscape to select this edge
                                                                    // EXAMPLE:  cy_object.$('#edge-3').select()
                }
            },



            highlight_located_node(label, key, value)
            /*  This is a generalization of the function highlight_class_node() in vue_cytoscape_2
                Instruct Cytoscape to select the node of the specified label that contains the given key/property pair.
                EXAMPLE: label="CLASS", key="name", value="some_class_name"
             */
            {
                console.log(`Invoking highlight_located_node() with label = "${label}", key = "${key}", value = "${value}"`);
                console.log("cy_object:");
                console.log(this.$options.cy_object);

                // Needs to locate the 'id' of a node from the array this.nodes
                // that contains the desired key/value pair
                // EXAMPLE (fragment):  {key: value, 'id': 116404, '_node_labels': ['CLASS']}

                var found = false;

                for (node of this.nodes)  {        // Loop over all the nodes
                    let node_labels = node._node_labels;
                    console.log(`node_labels: ${node_labels}`);
                    console.log(`Examining node with labels '${node_labels}', and id=${node.id}`);
                    if (node_labels !== undefined  &&  node_labels.includes(label)  &&  node[key] == value)  {
                        found = true;
                        var located_node = node;
                        break;
                    }
                }

                if (!found)  {
                    alert(`The desired node not found in the graph!  Try refreshing the page`);
                    return;
                }

                console.log(`Located node with id:  ${located_node.id}`);
                const selector = `#${located_node.id}`;   // Used to refer to a graph element in the Cytoscape object
                //console.log(`The following selector will be used: '${selector}'`);
                this.$options.cy_object.$(selector).select();   // Tell Cytoscape to select this node
                                                                // EXAMPLE:  cy_object.$('#116404').select()
                //this.legend_html = ['A test'];
                //this.selected_node_labels = node._node_labels;
                this.populate_legend_from_node(located_node);
            },



            locate_node_by_id(node_id)
            /*  Locate and return the index of first element of the this.nodes array
                whose 'id' key value matches the passed value.

                :param node_id: A string (always a string!) with the Cytoscape ID of a node
                :return:        A zero-based index of an element of the array this.nodes,
                                    or -1 if not found
             */
            {
                //console.log(`In locate_node_by_id().  Searching for node with id: ${node_id}`);
                //console.log(typeof node_id);


                // Loop over array of nodes
                //for (el of this.nodes)  {      // el is an object that represents a node
                for (i in this.nodes) {   // Note:  i will be an integer, not an array element!!
                    let el = this.nodes[i];
                    //console.log(`    el.id : ${el.id}`);
                    //console.log(typeof el.id);
                    //console.log(`    el :`);
                    //console.log(el);
                    if (el.id == node_id)  {
                        // If the element is a node, and its id matches the desired value
                        //console.log(`    Located the following node:`);
                        //console.log(el);
                        return i;          // Formerly: return el;
                    }
                }

                console.log(`    locate_node_by_id(): Unable to locate any matching node`);
                return -1;
            },



            locate_adjacent_edges(node_id)
            /*  Locate and return the indexes of all the element of the this.edges array
                whose 'source' or 'target' matches the passed node 'id' value.
                The index values are returned in REVERSE numerical position (for ease of deleting them
                with the splice function, for example)

                :param node_id: A string (always a string!) with the Cytoscape ID of a node
                :return:        A (possibly empty) array of indexes in the this.edges array
             */
            {
                console.log(`In locate_adjacent_edges().  Searching for edges connected to node with id: ${node_id}`);

                var adjacent_edges = [];    // Running list of indexes of located edges

                // Loop over array of edges
                //for (i in this.edges) {   // Note:  i will be an integer, not an array element!!
                for (let i = this.edges.length - 1; i >= 0; i--) {
                    let e = this.edges[i];
                    if (e.source == node_id || e.target == node_id)  {
                        // Found
                        console.log(`    Located the following edge:`);
                        console.log(e);
                        adjacent_edges.push(i);     // Save the index
                    }
                }

                return adjacent_edges;
            }



        }  // METHODS

    }
); // end component