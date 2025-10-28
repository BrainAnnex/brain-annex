Vue.component('vue-show-nodes-tabular',
    {
        props: ['data_from_flask'],

        template: `
            <div>
            <!-- Dataset in tabular form -->
            <table class="node">
            <!-- Header line -->
            <tr>
                <th class="subtle">#</th> <!-- Header for column showing row counts -->
                <th v-for="cell in headers">
                {{cell[0]}}
                    <span class="subtle" v-if="cell[1] == 'IN'"> (IN)</span>
                    <span class="subtle" v-else-if="cell[1] == 'OUT'"> (OUT)</span>
                </th>
            </tr>

            <!-- The table data -->
            <tr v-for="(row, row_number) in records">
                <td class="subtle">{{row_number + 1}}</td>
                <td v-for="(cell, column_number) in row">
                    <!-- Format the cell depending on its rendering_data -->

                    <!-- Cell containing literals: -->
                    <span v-if="rendering_data[row_number][column_number] == 0">
                        {{cell}}
                    </span>

                    <!-- Cell containing relationships (in condensed format): -->
                    <a v-else-if="rendering_data[row_number][column_number] == 1"
                       v-on:click.prevent="expand_relationship_info(row_number, column_number)"
                       v-bind:title="prepare_cell_info(cell)"
                       href="#">
                    {{get_length(cell)}}
                    </a>

                    <!-- Cell containing relationships (in expanded format): -->
                    <template v-else-if="rendering_data[row_number][column_number] == 2">
                        <span v-for="element in cell"
                              v-bind:title="'node id: ' + element[1]"
                              class='label' v-bind:style="{'background-color': obtain_label_color(element[0])}">
                        {{combine_labels(element[0])}}
                        </span>
                    </template>

                    <!-- Cell containing Neo4j labels: -->
                    <template v-else-if="rendering_data[row_number][column_number] == 3">
                        <span v-for="label_name in cell"
                              class='label' v-bind:style="{'background-color': obtain_label_color(label_name)}">{{label_name}} </span>
                    </template>
                </td>
            </tr>

            </table>

            </div>
            `,


        data: function() {
            return {
                json_data: this.data_from_flask,
                headers: this.data_from_flask['headers'],
                records: this.data_from_flask['records'],
                original_records: this.data_from_flask['records'],
                rendering_data: this.initialize_rendering(this.data_from_flask),
                label_color_list: ["117, 250, 250" , "205, 85, 212" , "247, 147, 47" , "68, 240, 177" , "219, 212, 70" , "247, 90, 47" , "250, 117, 164"],
                label_color_map: {},
                selected_rows: []   // Experimental; not yet implemented
            }
        },


        // ------------- METHODS --------------
        methods: {
            obtain_label_color(label_name)
            // Look up, or assign, a color to use for the specified label name.  In the process, create a color map to re-use
            {
                //console.log("label_name: " + label_name);
                let color = this.label_color_map[label_name];
                if (color == null)  {
                    let index = Object.keys(this.label_color_map).length;
                    index = index % this.label_color_list.length;   // Take the remainder, to cycle thru the available colors
                    //console.log("index: " + index);
                    color = "rgb(" + this.label_color_list[index] + ")";
                    this.label_color_map[label_name] = color;
                }
                //console.log("color: " + color);
                return color;
            },


            combine_labels(label_list)
            // For node with multiple labels, combine the labels into a single string
            {
                let text = "";
                for (i in label_list) {
                    if (i != 0)
                        text += " / ";  // This is the separator we're using

                    text += label_list[i];
                }
                return text;
            },


            prepare_cell_info(cell_data)
            // Prepare a string of data suitable for a pop-up balloon, with the given cell data
            {
                //console.log(cell_data);

                if (cell_data == null)
                    return "";

                let info;

                if (cell_data.length == 1)
                    info = "Links to node labeled: ";   // Singular
                else
                    info = "Links to nodes labeled: ";  // Plural

                for (let i = 0; i < cell_data.length; i++)  {
                    if (i != 0)
                        info += " , ";

                    info += "[" + cell_data[i][0] + "]";
                }

                return info;
            },


            initialize_rendering(original_data)
            // Define a 2-D array of rendering codes for all the records' data cells
            {
                //alert("In initialize_rendering");
                var headers = original_data['headers'];
                var original_records = original_data['records'];

                var render_array = [];

                // Duplicate the 2-D array original_records, and store in it a code for the cell rendering
                for (let row_n = 0; row_n < original_records.length; row_n++) {
                    //alert("pushing");
                    render_array.push([]);
                    for (let col_n = 0; col_n < original_records[row_n].length; col_n++) {
                        if (headers[col_n][1] == "node_labels")
                            render_array[row_n].push(3);    // Code for cells containing Neo4j labels
                        else if (this.is_relationship_header(headers, col_n))
                            //render_array[row_n][col_n] = 1;
                            render_array[row_n].push(1);    // Code for cells containing relationships
                        else
                            render_array[row_n].push(0);    // Code for cells containing literals
                    }
                };

                //console.log(render_array);
                return render_array;
            },


            expand_relationship_info(row_number, column_number)
            /*  Adjust the rendering data for the given cell, to indicate the the relationship info is
                to be shown in expanded format.  Special code 2 indicates this operation
             */
            {
                //alert(`In expand_relationship_info ${row_number} ${column_number}`);

                const op_code = 2;      // The special code indicating this expanded format

                let data_row = this.rendering_data[row_number];
                Vue.set(data_row, column_number, op_code);  // op_code is the new value with the special code
                                                            // Vue.set (rather than just setting a value) is needed for Vue reactivity
                                                            //      to the change in value
            },


            is_relationship_header(header_array, column_number)
            // Consult the header data to determine if the specified column contains relationship data
            {
                cell_type = header_array[column_number][1];
                if (cell_type == "IN" ||  cell_type == "OUT")
                    return true;
                else
                    return false;
            },


            get_length(cell_data)
            // Return the length of a given list - or the empty string if the argument is null
            {
                if (cell_data == null)
                    return "";
                else
                    return cell_data.length;
            }

        } // end methods

    }

);  // end component 'vue-show-nodes-tabular'



///////////////////////////////////////////////////////////////////////////////////////////////////////



// Instantiation must come after the component definition
new Vue({
    el: '#vue-root-1',      // There should be a DIV in the main HTML code with this id

    data: {
    },

    methods : {
    }
});