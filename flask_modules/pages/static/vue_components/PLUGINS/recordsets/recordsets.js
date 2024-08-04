/*  Vue component to display and edit Content Items of type "rs" (Recordsets)
 */

Vue.component('vue-plugin-rs',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      EXAMPLE :    {class:"YouTube Channel"
                                          class_name:"Recordset",
                                          n_group:10,
                                          order_by:"name",
                                          pos:100,
                                          schema_code:"rs",
                                          uri:"rs-1"
                                         }
                                      (if uri is -1, it means that it's a newly-created header, not yet registered with the server)
                            TODO: take "pos" and "class_name" out of item_data
            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this recordset is displayed (used when creating new recordsets)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <table class='rs-main'>

                <!-- Header row  -->
                <tr>
                    <th v-for="field_name in headers">
                        {{field_name}}
                    </th>
                </tr>

                <!--
                    Data row
                 -->
                <tr v-for="record in recordset">
                    <td v-for="field_name in headers">
                        <span v-html="render_cell(record[field_name])"></span>
                    </td>
                </tr>

            </table>

            <span v-if="current_page > 1" @click="get_recordset(1)" class="clickable-icon" style="color:blue"> << </span>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <span v-if="current_page > 1" @click="get_recordset(current_page-1)" class="clickable-icon" style="color:blue"> < </span>
            &nbsp;&nbsp;&nbsp;  Page <b>{{current_page}}</b>   &nbsp;&nbsp;&nbsp;
            <span @click="get_recordset(current_page+1)" class="clickable-icon" style="color:blue"> > </span>

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                headers: ["quote", "attribution", "uri"],   // ["name", "url", "uri"],  TODO: generalize

                recordset: [],         // This will get loaded by querying the server when the page loads

                current_page: 1,
                records_per_page: this.item_data.n_group,

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   HOOKS   ------------------------------------

        mounted()
        /* Note: the "mounted" Vue hook is invoked later in the process of launching this component.
                 TODO: investigate if earlier would be better
         */
        {
            console.log(`The Recordsets component has been mounted`);
            //alert(`The Recordsets component has been mounted`);

            this.get_recordset(1);  // Fetch contents of an initial recordset from the server
        },



        // ------------------------------   METHODS   ------------------------------
        methods: {

            get_recordset(page)
            {
                skip = (page-1) * this.records_per_page;

                console.log(`In get_recordset(): attempting to retrieve page ${page} of recordset with URI '${this.item_data.uri}'`);

                // Send the request to the server, using a POST
                const url_server_api = `/BA/api/get_filtered?label=${this.item_data.class}&order_by=${this.item_data.order_by}&limit=${this.records_per_page}&skip=${skip}`;

                const get_obj = {label: this.item_data.class,
                                 order_by: this.item_data.order_by,
                                 limit: this.records_per_page,
                                 skip: skip};       // TODO: not yet in use

                const my_var = page;        // Optional parameter to pass

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(get_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {callback_fn: this.finish_get_recordset,
                             custom_data: my_var
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            }, // get_recordset


            finish_get_recordset(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of get_recordset() upon getting a response from the server
            {
                console.log("Finalizing the get_recordset() operation...");
                console.log(`Custom data passed: ${custom_data}`);
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.recordset = server_payload;
                    this.current_page = custom_data;
                    //...
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    //...
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
                //...
            }, // finish_get_recordset



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