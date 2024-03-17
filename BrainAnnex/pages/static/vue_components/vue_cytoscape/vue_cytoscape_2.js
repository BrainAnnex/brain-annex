Vue.component('vue_cytoscape_2',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: {
            <!-- NOTE:  Only lower cases in props names! -->

            graph_data: {
                required: true
            },

            component_id: {
                default: 1
            }

        },



        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

                <div v-bind:id="'cy_' + component_id" class="cytoscape-container">
                    <!-- CYTOSCAPE.js WILL INSERT THE GRAPH HERE -->
                </div>

                <div class="legend">
                    <template v-for="item in node_info">
                        <span v-html="item"></span>
                        <br>
                    </template>
                </div>

            </div>		<!-- End of outer container -->
            `,



        // ----------------  DATA  -----------------
        data: function() {
            return {
                graph_structure: this.graph_data.structure,

                node_info: ["Click on a node to see its attributes"]
            }
        },



        // ----------------  MOUNTED  -----------------
        mounted() {
            /* Note: the "mounted" Vue hook is invoked later in the process of launching this component
             */
            console.log('The component is now mounted');

            this.create_graph('cy_' + this.component_id);    // This will let Cytoscape.js do its thing
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            assemble_element_structure()
            /*  Create and return the graph structure needed by Cytoscape.js
                (a list of objects with a key named "data")
                EXAMPLE:
                    [
                        {data: {id: 1, name: 'Headers', labels: 'CLASS'}
                        },
                        {data: {id: 2, name: 'text', labels: 'PROPERTY'}
                        },
                        {data: {id: 3, source: 1, target: 2, name: 'HAS_PROPERTY'}
                        }
                    ]
             */
            {
                res = [];

                for (i in this.graph_structure) {   // Note:  i will be an integer, not an array element!!
                    el = {data: this.graph_structure[i]};
                    res.push(el);
                }

                console.log(res);

                return res;
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            create_graph(element_id)
            /*  This function needs to be invoked after this Vue component is "mounted".
                Replace the contents of the HTML element whose id is the given element_id
                with the graphic structure created by Cytoscape
             */
            {
                console.log(`Running create_graph() to replace page element with ID ${element_id}`);

                var cy_object = cytoscape({

                    container: document.getElementById(element_id),    // Container to render in

                    elements: this.assemble_element_structure,   // List of graph elements (nodes & edges)


                    style: [ // the stylesheet for the graph
                        {
                            selector: 'node',       // NODES
                            style: {
                                'width': 60,
                                'height': 60,
                                'label': this.node_caption_f,         // 'data(color)'
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
                            selector: ':selected',
                            style: {
                                'background-color': 'yellow',
                                'line-color': 'red'
                            }
                        }

                    ],  // END of style


                    layout: {
                        name: 'circle',   // OR: 'grid'
                        rows: 1
                    }

                });

                cy_object.on('click', 'node', this.show_node_info);

                /*
                // EXAMPLES of adding nodes
                cy_object.add([
                    { data: { id: 4, labels: 'import' , name: 'Restaurants' }, position: {x: 80, y: 100} }
                ]);

                cy_object.add([
                    { data: { id: 5, labels: 'SOME_OTHER_LABELS' , name: 'Mr. Node' }, position: {x: 80, y: 200} }
                ]);
                */
            },



            /*
                SUPPORT FUNCTIONS
             */

            show_node_info(ev)
            // Invoked when clicking on a node
            {
                var node = ev.target;
                console.log(node.position());
                //console.log(node.id());
                //console.log(node.data());
                //console.log(node);
                //console.log(node.data);
                //console.log(node.data('name'));
                console.log(Object.keys(node.data()));

                const cyto_data_obj = node.data();
                let info_arr = [];
                for (k in cyto_data_obj) {
                    //console.log( k, cyto_data_obj[k] );
                    info_arr.push(`<b>${k}</b>: ${cyto_data_obj[k]}`);
                }
                //console.log(info_arr);

                const pos = node.position()
                const x = pos.x.toFixed(1);
                const y = pos.y.toFixed(1);
                //this.node_info = `id: ${node.id()} , x: ${x} , y: ${y}`;
                this.node_info = info_arr;
            },


            map_labels_to_caption_field(labels)
            {
                console.log(this.graph_data.caption_mapping);

                if (labels in this.graph_data.caption_mapping)
                    return this.graph_data.caption_mapping[labels];

                return "id";
            },

            node_caption_f(ele)
            /*
                Note: the various fields of the node may be extracted from the argument ele
                      as ele.data(field_name).  For example: ele.data("id")
             */
            {
                console.log(ele.data("id"));
                console.log(ele.data("labels"));

                const field_to_use_as_caption = this.map_labels_to_caption_field(ele.data("labels"));

                return ele.data(field_to_use_as_caption)
            },


            node_color_f(ele)
            /*  Determine and return the color to use for the inside of the node
                passed as argument (as a graph element)
             */
            {
                const default_color = '#FFFFFF';    // TODO: assign colors on rotation instead
                                                    //       SEE vue_curves_4.js

                //console.log(this.graph_data.graph_color_mapping);
                //console.log(ele.data("labels"));
                const labels = ele.data("labels");    // Counterpart of node labels (but only 1 for now)
                if (labels in this.graph_data.color_mapping)  {
                    let requested_color = this.graph_data.color_mapping[labels];
                    return requested_color;
                }
                else
                    return default_color;
            },


            node_border_color_f(ele)
            /*  Determine and return the color to use for the border of the node
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