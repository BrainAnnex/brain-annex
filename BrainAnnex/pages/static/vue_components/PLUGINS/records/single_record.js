/*  Vue component to display and edit a single table rows of data (NOT headers)
    from a Content Item at type "r" (Record)
 */

Vue.component('vue-plugin-single-record',
    {
        props: ['record_data', 'field_list'],
        /*  record_data:    EXAMPLE:
                            {"uri":"52", "pos":10, "schema_code":"r",
                             class_name:"German Vocabulary", <-- NOT CURRENTLY BEING PASSED
                             "German":"Tier", "English":"animal"}

            field_list:     A list of field names being shown, in order.
                            EXAMPLE: ["French", "English", "notes"]
          */

        template: `
            <tr @dblclick="detect_double_click">    <!-- Outer container, serving as Vue-required template root  -->
            <!--
                Row of data
            -->

                <td v-for="key in field_list">
                    <!-- Display SPAN or INPUT elements, depending on the editing mode -->
                    <span v-if="!editing_mode" v-html="render_cell(record_data[key])"></span>
                    <input v-if="editing_mode" type="text" size="25" v-model="record_data[key]">
                </td>

                <td v-if="editing_mode">
                    <button @click="save">SAVE</button>
                    <a @click.prevent="cancel_edit" href="#" style="margin-left:15px">Cancel</a>
                </td>
            </tr>
            `,


        data: function() {
            return {
                editing_mode: false         // For now, unused
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            detect_double_click()
            {
                //alert("Double click detected ");
                this.editing_mode = true;
            },

            cancel_edit()
            {
                this.editing_mode = false;
            },

            save()
            {
                alert("Not yet implemented, sorry");
                this.editing_mode = false;
            },



            render_cell(cell_data)
            /*  If the passed string appears to be a URL, convert it into a hyperlink, opening in a new window;
                and if the URL is very long, show it in abbreviated form
             */
            {
                const max_url_len = 30;     // NOT counting the protocol part (such as "https://")

                let dest_name = "";         // Name of the destination of the link, if applicable
                // Do a simple-minded check as to whether the cell content appear to be a hyperlink
                if (cell_data.substring(0, 8) == "https://")
                    dest_name = cell_data.substring(8);
                else if (cell_data.substring(0, 7) == "http://")
                    dest_name = cell_data.substring(7);

                if (dest_name != "")  {     // If the cell data was determined to be a URL
                    if (dest_name.length > max_url_len)
                        dest_name = dest_name.substring(0, max_url_len) + "..."; // Display long links in abbreviated form

                    return `<a href='${cell_data}' target='_blank' style='font-size:10px'>${dest_name}<a>`;
                }
                else
                    return cell_data;
            }

        }  // METHODS

    }
); // end component