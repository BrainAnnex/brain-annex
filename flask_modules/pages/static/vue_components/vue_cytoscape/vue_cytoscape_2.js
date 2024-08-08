Vue.component('vue_cytoscape_2',
    {
        props: {
            graph_data: {
                required: true
            },
            /* graph_data is an object with the following 3 KEYS:

                1) "structure"
                        EXAMPLE:
                            [{'name': 'German Vocabulary', 'strict': False, 'uri': 'schema-1', 'internal_id': 77, 'id': 77, 'labels': ['CLASS']},
                             {'allowed': ['der', 'die', 'das'], 'name': 'Gender', 'dtype': 'categorical',
                                   'uri': 'schema-91', 'internal_id': 79, 'id': 79, 'labels': ['PROPERTY']},
                             {'name': 'HAS_PROPERTY', 'source': 116602, 'target': 116618, 'id': 'edge-185'}
                            ]

                2) "color_mapping"      (TODO: auto-assign if unspecified; SEE vue_curves_4.js)
                        EXAMPLE:  {'PERSON': 'cyan', 'CAR': 'orange'}

                3) "caption_mapping"    (from label name to property to use for the node's caption)
                        EXAMPLE:  {'PERSON': 'name', 'CAR': 'color'}
             */

            component_id: {
                default: 1      // Used in forming a unique ID for the DIV that contains the Cytoscape grape
            }
        },


        cy_object: null,        // Component-wide metadata, available thru this.$options.cy_object
                                // Used to store the Cytoscape object


        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div v-bind:id="'cy_' + component_id" class="cytoscape-container">
                    <!--
                        ******   CYTOSCAPE.js WILL INSERT THE GRAPH HERE!   ******
                      -->
                </div>


                <!-- SIDE BOX, to the right of the main plot -->
                <div class="cytoscape-legend">
                    <p v-if="!node_info">
                        <b>Node labels</b><br><br>
                        <template v-for="color_map in Object.entries(graph_data.color_mapping)">
                            <div class="label" v-bind:style="{'background-color': color_map[1]}">{{color_map[0]}}</div>
                        </template>

                        <br><br><br>
                        <span style="color: #888; font-style: italic">Select a node or edge<br>on the graph</span>
                        <br>
                        <span style="color: #BBB; font-style: italic">(shift-click for multiple selections)</span>
                    </p>

                    <p v-else>
                        <template v-for="label_name in node_labels">
                            <div class="label" v-bind:style="{'background-color': graph_data.color_mapping[label_name]}">{{label_name}}</div>
                        </template>
                        <br><br>

                        <template v-for="item in node_info">
                            <span v-html="item"></span>
                            <br>
                        </template>
                    </p>

                    <br>
                    <hr>
                    <br>
                    <button @click=flip_plot_style>Flip plot style</button>
                    <p style="color: #BBB; margin-top:5px; margin-bottom:0">Current: "{{plot_layout_style}}"</p>

                    <br><br>
                    <b>List of Classes:</b>
                    <p style="color: #BBB; margin-left:15px; margin-top:0px; margin-bottom:0">Click names to select; click empty space on graph to de-select</p>
                    <ul>
                        <li v-for="item in class_list" >
                            <span @click="highlight_class_node(item)" class="clickable-icon" style='color:#56947E'>{{item}}</span>
                        </li>
                    </ul>

                </div>      <!-- End of side box -->

            </div>		<!-- End of outer container -->
            `,



        // ---------------------  DATA  ----------------------
        data: function() {
            return {
                graph_structure: this.graph_data.structure,     // A list of dicts

                // Data of the currently-selected node;
                // both variables are arrays of strings
                node_labels: null,
                node_info: null,

                plot_layout_style: "breadthfirst",  // CHOICES: 'grid', 'circle', 'random',
                                                    //          'concentric', 'breadthfirst', 'cose'

                class_list: []                      // List of all Class names in the Schema
            }
        },



        // ---------------------  MOUNTED  ----------------------
        mounted() {
            /* Note: the "mounted" Vue hook is invoked later in the process of launching this component;
                     waiting this late is needed.  Caution must be taken not to re-trigger it from its code.
             */
            console.log(`The 'vue_cytoscape_2' component is now mounted`);

            const cy_object = this.create_graph('cy_' + this.component_id);   // MAIN CALL : this will let Cytoscape.js do its thing!
                                                            // EXAMPLE :  "cy_1"  (this name needs to match the ID given
                                                            //                     to the DIV element containing the graph)
            // Save the newly-created Cytoscape object, as metadata for this Vue component
            // Note: it cannot be simply saved as component data, because doing so triggers another call to this
            //       "mounted" Vue hook function, leading to an infinite loop!
            this.$options.cy_object = cy_object;

            // Create a list of all Class names in the Schema.  TODO: maybe also save the id's alongside the names
            for (node of this.graph_structure) {        // Loop over this.graph_structure
                let labels = node.labels;
                //console.log(`labels: ${labels}`);
                if (labels !== undefined  &&  labels.includes('CLASS'))  {
                    //console.log(`ADDING CLASS NAME: '${node.name}'`);
                    this.class_list.push(node.name);    // This operation is safe, because it doesn't trigger
                                                        // a new call to this "mounted" Vue hook function!
                }
            }
            // Finally, sort the newly-created list of Class names
            this.class_list.sort();                         // This operation is safe
        },



        // ---------------------  COMPUTED  ----------------------
        computed: {
            assemble_element_structure()
            /*  Create and return the graph structure needed by Cytoscape.js
                (an array of objects, each with a key named "data")
                EXAMPLE:
                    [
                        {data: {'id': 1, 'name': 'Julian', 'labels': ['PERSON']}
                        },
                        {data: {'id': 2, 'color': 'white', 'labels': ['CAR']}
                        },
                        {data: {'name': 'OWNS', 'source': 1, 'target': 2, 'id': 'edge-1'}
                        }
                    ]
             */
            {
                cyto_arr = [];

                for (i in this.graph_structure) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.graph_structure[i]};
                    cyto_arr.push(el);
                }

                //console.log("assemble_element_structure produced:")
                //console.log(cyto_arr);

                return cyto_arr;
            }
        },



        // ---------------------  METHODS  ----------------------
        methods: {
            flip_plot_style()
            // Re-render the graph with a changed plot style
            {
                //console.log("In flip_plot_style()");
                if (this.plot_layout_style == "breadthfirst")
                    this.plot_layout_style = "random";
                else
                    this.plot_layout_style = "breadthfirst";

                var cy_object = this.create_graph('cy_' + this.component_id); // This will let Cytoscape.js re-render the plot
                this.$options.cy_object = cy_object;        // Save the new objec
                this.node_info = null;                      // Unset any node selection
            },



            create_graph(element_id)
            /*  This function needs to be invoked after this Vue component is "mounted".
                Replace the contents of the desired HTML element (specified by the given element_id)
                with the graphic structure created by Cytoscape
             */
            {
                console.log(`Running create_graph() to replace page element with ID '${element_id}'`);

                var cy_object = cytoscape({

                    container: document.getElementById(element_id),    // Container to render in

                    elements: this.assemble_element_structure,          // List of graph elements (nodes & edges)


                    style: [    // The stylesheet for the graph
                        {
                            selector: 'node',       // NODES
                            style: {
                                'width': 60,
                                'height': 60,
                                //'label': 'data(name)',
                                'label': this.node_caption_f,
                                //'background-color': '#8DCC93',
                                'background-color': this.node_color_f,

                                'border-width': 2,
                                //'border-color': '#5db665',
                                'border-color': this.node_border_color_f,

                                'font-size': '11px',
                                'color': '#101010',        // Color of the text
                                'text-halign': 'center',
                                'text-valign': 'center'
                            }
                        },

                        {
                            selector: 'edge',      // RELATIONSHIPS
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
                            selector: ':selected',   // SELECTED node and links
                            style: {
                                'background-color': 'yellow',
                                'line-color': 'red'
                            }
                        }

                    ],  // END of style


                    layout: {
                        name: this.plot_layout_style,
                        rows: 1
                    }

                });


                /*
                    Detect all click of interest, and register their handlers
                 */
                cy_object.on('click', this.clear_legend);           // A click on the empty space of the graph (the Cytoscape core)
                cy_object.on('click', 'node', this.show_node_info); // A click on a node on the graph
                cy_object.on('click', 'edge', this.show_edge_info); // A click on an edged

                /*
                // EXAMPLES of adding nodes
                cy_object.add([
                    { data: { id: 4, labels: 'import' , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy_object.add([
                    { data: { id: 5, labels: 'SOME_OTHER_LABELS' , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */

                return cy_object;         // The newly-created Cytoscape object

            },  // create_graph



            /*
                SUPPORT FUNCTIONS
             */

            show_node_info(ev)
            // Invoked when clicking on a node
            {
                const node = ev.target;

                const cyto_data_obj = node.data();      // An object with various keys, such as 'id', 'labels', 'name'

                this.populate_legend_from_node(cyto_data_obj);
            },


            populate_legend_from_node(node_data_obj)
            // Invoked when a node is to be highlighted
            {
                // Each of the above object's key/value pairs will go into an array element,
                // as an HTML string
                let info_arr = [];
                let html_row_str = "";

                for (k in node_data_obj) {
                    //console.log( k, node_data_obj[k] );
                    if (k == "labels")
                        continue;       // No need to show; labels are shown elsewhere as graphic tags
                    if (k != "name")
                        html_row_str = `<b>${k}</b>: ${node_data_obj[k]}`;
                    else
                        html_row_str = `<span style='color: brown; font-weight: bold'>${k}: ${node_data_obj[k]}</span>`;

                    info_arr.push(html_row_str);  // Data to update the UI graph legend
                }
                //console.log(info_arr);

                // Update the legend
                this.node_info = info_arr;
                this.node_labels = node_data_obj.labels;
            },


            show_edge_info(ev)
            // Invoked when clicking on an edge
            {
                const edge = ev.target;

                const cyto_data_obj = edge.data();      // An object with various keys, such as 'id', 'name', 'source', 'target'
                let info_arr = [];                      // Each of the object key/value pairs will go into an array element, as an HTML string
                for (k in cyto_data_obj) {
                    //console.log( k, cyto_data_obj[k] );
                    info_arr.push(`<b>${k}</b>: ${cyto_data_obj[k]}`);  // Data to update the UI graph legend
                }
                //console.log(info_arr);

                // Update the legend
                this.node_info = info_arr;
                this.node_labels = null;
            },


            clear_legend(ev)
            /*  Invoked when clicking anywhere - including the image background.
                Clear the plot legend (note: if clicking on a node or edge, the legend
                will get set again by the next handler)
            */
            {
                // The following change will clear the plot legend
                this.node_info = null;
                this.node_labels = null;
            },



            highlight_class_node(class_name)
            // Instruct Cytoscape to select the node corresponding to the given Class name
            {
                //console.log(`Clicked on Class "${class_name}"`);
                //console.log(this.$options.cy_object);

                // Needs to locate the 'id' of a node from this.graph_structure
                // that has the desired Class name
                // EXAMPLE (fragment):  {'name': class_name, 'id': 116404, 'labels': ['CLASS']}

                var found = false;

                for (node of this.graph_structure)  {        // Loop over this.graph_structure
                    let labels = node.labels;
                    //console.log(`labels: ${labels}`);
                    //console.log(`Examining Class '${node.name}', with id=${node.id}`);
                    if (labels !== undefined  &&  labels.includes('CLASS')  &&  node.name == class_name)  {
                        found = true;
                        var located_node = node;
                        break;
                    }
                }

                if (found)  {
                    //console.log(`Located node with id:  ${located_node.id}`);
                    const selector = `#${located_node.id}`   // Used to refer to a graph element in the Cytoscape object
                    //console.log(`The following selector will be used: '${selector}'`);
                    this.$options.cy_object.$(selector).select();   // Tell Cytoscape to select this node
                                                                    // EXAMPLE:  cy_object.$('#116404').select()
                    //this.node_info = ['A test'];
                    //this.node_labels = node.labels;
                    this.populate_legend_from_node(located_node);
                }
                else
                    alert(`Class node "${class_name}" not found in the graph!  Try refreshing the page`);
            },



            map_labels_to_color(labels)
            /*  Given the labels of a node (an array of strings),
                return the name of the color to use for the inside of the node,
                based on what was specified in "color_mapping" from the "graph_data" prop.
                In case of multiple labels, try them sequentially, until a mapping is found.
                If no mapping information is present for any of the labels, use the color white by default
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_color = '#FFFFFF';    // TODO: assign colors on rotation instead

                //console.log("labels: ", labels);    // Example: ["PERSON"]
                //console.log(this.graph_data.color_mapping);

                for (single_label of labels) {
                    if (single_label in this.graph_data.color_mapping)  {
                        const color = this.graph_data.color_mapping[single_label];
                        //console.log(`Using the color '${color}' for the inside of this node`);
                        return color;
                    }
                }

                return default_color;
            },


            map_labels_to_caption_field(labels)
            /*  Given the labels of a node (an array of strings),
                return the name of the field to use for the node caption,
                based on what was specified in the "caption_mapping" value from the "graph_data" prop.
                In case of multiple labels, try them sequentially, until a mapping is found.
                If no mapping information is present for any of the labels, use the field name "id" by default
             */
            {
                // The default value, in case no mapping info found for any of the labels
                const default_caption_field_name = "id";

                //console.log("In map_labels_to_caption_field().  labels: ", labels);    // Example: ["PERSON"]
                //console.log(this.graph_data.caption_mapping);

                for (single_label of labels) {
                    if (single_label in this.graph_data.caption_mapping)  {
                        const caption_field_name = this.graph_data.caption_mapping[single_label];
                        //console.log(`Using the field '${caption_field_name}' for the caption of this node`);
                        return caption_field_name;
                    }
                }

                return default_caption_field_name;
            },



            node_caption_f(ele)
            /*  Function to generate the caption to show on the graph, for a given node.
                The caption is based on the node's labels; in the absence of a user-specified mapping,
                the data in the field "id" is used as caption.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                //console.log("Determining node caption for node with id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("labels"));

                const field_to_use_for_caption = this.map_labels_to_caption_field(ele.data("labels"));
                //console.log(`Name of field to use for caption: '${field_to_use_for_caption}'`);

                return ele.data(field_to_use_for_caption)
            },


            node_color_f(ele)
            /*  Function to generate the color to use for the inside of the given node.
                The color is based on the node's labels; in the absence of a user-specified mapping,
                white is used.

                Note: the various fields of the node may be extracted from the argument ele (representing a node element)
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                //console.log("Determining color for node with id: ", ele.data("id"));
                //console.log("    and labels: ", ele.data("labels"));

                return this.map_labels_to_color(ele.data("labels"));
            },


            node_border_color_f(ele)
            /*  Function to generate the color to use for the border of the node
                passed as argument (as a graph element).
                The relationship between the interior and edge color is:
                same Hue/Saturation but less Luminosity
             */
            {
                //console.log(this.graph_data.color_mapping);
                //console.log(ele.data("labels"));
                const interior_color = this.node_color_f(ele);
                //console.log(interior_color);
                const c = d3.hsl(interior_color);
                //console.log(c);
                const c_new = c.darker(0.635).formatHex();  // Less Luminosity
                //console.log(c_new);
                return c_new;
            }


        }  // METHODS

    }
); // end component