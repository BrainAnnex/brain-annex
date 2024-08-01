/*  Vue component to display and edit Content Items of type "rs" (Recordsets)
 */

Vue.component('vue-plugin-rs',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      EXAMPLE TBA: {}
                                      (if uri is -1, it means that it's a newly-created header, not yet registered with the server)

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <table class='rs-main'>

                <!-- Header row  -->
                <tr>
                    <th v-for="header_cell in this.headers">
                        {{header_cell}}
                    </th>
                </tr>

                <!--
                    Data row
                 -->
                <tr v-for="record in this.recordset">
                    <td v-for="cell in record">
                        <span v-html="render_cell(cell)"></span>
                    </td>
                </tr>

            </table>

            Page 1 of 1

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                headers: ["name", "url", "uri"],

                recordset: [
                            {name: "Doctor Mike", url: "http://www.youtube.com/channel/UC0QHWhjbe5fGJEPz3sVb6nw", uri: "ytc-20"},
                            {name: "Higgsino physics", url: "http://www.youtube.com/channel/UC02-e6K7o5_bPw0weXh3W3g", uri: "ytc-17"}
                           ]
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {

            render_cell(cell_data)
            /*  If the passed argument is a string that appears to be a URL, convert it into a string with HTML code
                for a hyperlink that opens in a new window;
                if the URL is very long, show it in abbreviated form in the hyperlink text.
                In all other cases, just return the argument.

                Note: this function is also found in records.js and single_records.js
             */
            {
                const max_url_len = 35;     // For text to show, NOT counting the protocol part (such as "https://")

                let dest_name = "";         // Name of the destination of the link, if applicable

                if (typeof cell_data != "string")
                     return cell_data;

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

        }  // methods

    }
); // end component