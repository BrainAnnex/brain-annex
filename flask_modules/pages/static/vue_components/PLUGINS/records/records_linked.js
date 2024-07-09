/*  Vue component to display and edit the "sub-records" (linked records) of a given record.
    This is a simplified, and specialized, version of its parent component, 'vue-plugin-r'
 */

Vue.component('vue-plugin-r-linked',
    {
        props: ['item_data', 'rel_name', 'rel_dir'],
        /*  item_data:  The "parent" record, from which we're following its links.
                        EXAMPLE: {"uri":52, "pos":10, "schema_code":"r"
                                  "German":"Tier", "English":"animal"}
            rel_name:   Name of the relationship that the user followed to get here.
                        EXAMPLE: "sold_by"
            rel_dir:    Direction or the relationship, from the point of view of its "source".
                        Either "IN" or "OUT"
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <table v-if='display_record' class='r-main'>
                <!--
                    Header row
                  -->
                <tr>
                    <th style='background-color: white'>
                    <img v-if="rel_dir=='IN'" src='/BA/pages/static/graphics/thick_up_arrow_16_216098.png'>
                    <img v-else src='/BA/pages/static/graphics/down_thick_arrow_16_216439.png'>
                    </th>

                    <th v-for="cell in this.determine_headers()">
                    {{cell}}
                    </th>

                    <th>
                    &nbsp;
                    </th>
                </tr>


                <!--
                    Row for the data, starting with the relationship name
                 -->
                <tr>
                    <th v-if="rel_dir=='IN'" class='subrecord-in'>
                    {{rel_name}}
                    </th>
                    <th v-if="rel_dir=='OUT'" class='subrecord-out'>
                    {{rel_name}}
                    </th>

                    <td v-for="key in this.determine_cells()">
                        <!-- Display SPAN or INPUT elements, depending on the editing status -->
                        <span v-if="!editing_mode" v-html="render_cell(current_data[key])"></span>
                        <input v-if="editing_mode" type="text" size="25" v-model="current_data[key]">
                    </td>

                    <td>
                        <a v-on:click.prevent="hide_record()"  href="#" title='Hide this record' alt='Hide this record'>
                            <img src='/BA/pages/static/graphics/eye_hidden_16_315219.png'>
                        </a>
                    </td>

                </tr>
            </table>

            </div>		<!-- End of outer container -->
            `,


        data: function() {
            return {
                display_record: true,
                editing_mode: false,

                current_data: this.clone_and_standardize(this.item_data),   // Scrub some data, so that it won't show up in the tabular format
                original_data: this.clone_and_standardize(this.item_data)
                // NOTE: clone_and_standardize() gets called twice

            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            hide_record()
            {
                const uri = this.item_data.uri;
                console.log(`Hiding record with uri ${uri}`);
                this.display_record = false;
            },


            determine_headers()
            {
                return Object.keys(this.current_data);
            },


            determine_cells()
            {
                return this.determine_headers();
            },


            clone_and_standardize(obj)
            // Clone, and remove keys that don't get shown nor edited
            {
                clone_obj = Object.assign({}, obj);     // Clone the object

                // Scrub some data, so that it won't show up in the tabular format
                delete clone_obj.uri;
                delete clone_obj.schema_code;
                //delete clone_obj.class_name;
                //delete clone_obj.insert_after;

                return clone_obj;
            },

            render_cell(cell_data)
            // If the string is a string that appears to be a URL, convert it into a hyperlink;
            // otherwise, just return the argument
            {
                if (typeof cell_data != "string")
                     return cell_data;

                // Do a simple-minded check as to whether the cell content appear to be a hyperlink
                if (cell_data.substring(0, 8) == "https://"
                            ||  cell_data.substring(0, 7) == "http://")
                    return `<a href='${cell_data}' target='_blank'>${cell_data}<a>`;
                else
                    return cell_data;
            }

        }  // METHODS

    }
); // end component