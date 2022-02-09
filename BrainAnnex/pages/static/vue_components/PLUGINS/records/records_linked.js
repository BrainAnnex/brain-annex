Vue.component('vue-plugin-r-linked',
    {
        props: ['item_data', 'rel_name', 'rel_dir'],
        /*  item_data:  EXAMPLE: {"item_id":52, "pos":10, "schema_code":"r"
                                  "German":"Tier", "English":"animal"}
            rel_name:   EXAMPLE: "BA_served_at"
            rel_dir:    Either "IN" or "OUT"
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <table class='r-main'>
            <!-- Header row  -->
            <tr>
                <th style='background-color: white'>
                <img v-if="rel_dir=='IN'" src='/BA/pages/static/graphics/thick_up_arrow_16_216098.png'>
                <img v-else src='/BA/pages/static/graphics/down_thick_arrow_16_216439.png'>
                </th>

                <th v-for="cell in this.determine_headers()">
                {{cell}}
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

            </tr>
            </table>

            </div>		<!-- End of outer container -->
            `,


        data: function() {
            return {
                editing_mode: false,

                current_data: this.clone_and_standardize(this.item_data),   // Scrub some data, so that it won't show up in the tabular format
                original_data: this.clone_and_standardize(this.item_data)
                // NOTE: clone_and_standardize() gets called twice

            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {

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
                delete clone_obj.item_id;
                delete clone_obj.schema_code;
                //delete clone_obj.class_name;
                //delete clone_obj.insert_after;

                return clone_obj;
            },

            render_cell(cell_data)
            // If the string is a URL, convert it into a hyperlink
            {
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