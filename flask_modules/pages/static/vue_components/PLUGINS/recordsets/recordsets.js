/*  Vue component to display and edit Content Items of type "rs" (Recordsets)
 */

Vue.component('vue-plugin-rs',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_data:      EXAMPLE :    {class_name:"Recordset",
                                          class:"YouTube Channel"
                                          n_group:10,
                                          order_by:"name",
                                          pos:100,
                                          schema_code:"rs",
                                          uri:"rs-7"
                                         }
                                      (if uri is negative, it means that it's a newly-created header, not yet registered with the server)
                            TODO: take "pos" and "class_name" out of item_data !
            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this recordset is displayed (used when creating new recordsets)
            index:          The zero-based position of this Recordset on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names (for the Recordset entity, not its records!), in Schema order.
                                EXAMPLE: ["class", "order_by", "clause", "n_group", "caption"]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <span style="font-weight:bold; color:gray">{{this.pre_edit_metadata.class}}</span>

                <!-- For the max-width attribute to work, there must not be a 'display: inline-block' in any of its ancestors -->
                <div class="dragscroll" style="margin-top: 0; max-width: 99%; overflow: auto">
                    <table class='rs-main'>

                        <!-- Header row  -->
                        <tr>
                            <th v-for="field_name in headers">
                                {{insert_blanks(field_name)}}
                            </th>
                            <th v-show="edit_mode">
                                EDIT
                            </th>
                        </tr>

                        <!--
                            All the various Data rows
                         -->
                        <tr v-for="record in recordset">
                            <!-- The various data fields -->
                            <td v-for="field_name in headers">
                                <span v-if="record.internal_id != record_being_editing"
                                    v-html="render_cell(record[field_name])"
                                ></span>
                                <input   v-else type="text" size="25"
                                         v-model="record_mid_edit[field_name]"
                                >
                            </td>

                            <!-- The control cell (for editing) -->
                            <td v-show="edit_mode" style="background-color: #f2f2f2">
                                <span v-if="record.internal_id == record_being_editing">
                                    <button @click="save_record_edit">SAVE</button>
                                    <a @click.prevent="cancel_record_edit" href="#" style="margin-left:15px">Cancel</a>
                                </span>
                                <img v-if="record_being_editing === null"
                                     src="/BA/pages/static/graphics/edit_16_pencil2.png"
                                     @click="edit_record(record)"
                                     class="control" title="EDIT" alt="EDIT"
                                >
                            </td>
                        </tr>

                        <!-- Header row, repeated at bottom of table  -->
                        <tr>
                            <th v-for="field_name in headers" class="repeated">
                                {{insert_blanks(field_name)}}
                            </th>
                            <th v-show="edit_mode">
                                NEW RECORD
                            </th>
                        </tr>

                        <!-- Row for entry of new data, if in editing mode  -->
                        <tr v-if="edit_mode">
                            <td v-for="field_name in headers">
                                <input v-model="new_record[field_name]">
                            </td>
                            <td v-show="edit_mode">
                                <button @click="save_new_record" style="">SAVE</button>
                                Cancel
                            </td>
                        </tr>

                    </table>
                </div>


                <!-- Recordset NAVIGATION (hidden if newly-created recordset) -->
                <template v-if="this.pre_edit_metadata.class">
                    <span v-if="current_page > 1" @click="get_recordset(1)" class="clickable-icon" style="color:blue; font-size:16px"> &laquo; </span>
                    <span v-if="current_page > 1" @click="get_recordset(current_page-1)" class="clickable-icon" style="color:blue; margin-left:20px; font-size:16px"> < </span>
                    <span style="margin-left:20px; margin-right:20px">Page <b>{{current_page}}</b></span>
                    <span @click="get_recordset(current_page+1)" class="clickable-icon" style="color:blue; font-size:16px"> > </span>
                    <span v-if="total_count" style="margin-left: 60px; color: gray">{{recordset.length}} records of total {{total_count}} </span>
                </template>

                <!-- Status info -->
                <p style="float: right; display: inline-block; padding-top: 0; margin-top: 8px; margin-right: 5px; text-align: right">
                    <span v-if="waiting" class="waiting">Contacting the server...</span>
                    <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
                </p>


                <!-- RECORDSET EDITOR : VIEWING VERSION -->
                <div v-if="edit_mode && !recordset_editing"
                     style="border: 1px solid gray; background-color: white; padding: 5px; margin-top: 3px; margin-bottom: 3px">
                    <b>RECORDSET definition</b>
                    <img src="/BA/pages/static/graphics/edit_16_pencil2.png" style="margin-left: 30px"
                         @click="edit_recordset"  class="control" title="EDIT" alt="EDIT">

                    <p style="margin-left: 10px">
                        Class: {{current_metadata.class}}<br>
                        Order by: {{current_metadata.order_by}}<br>
                        Number records shown per page: {{current_metadata.n_group}}
                    </p>
                </div>


                <!-- RECORDSET EDITOR : EDITING MODE -->
                <div v-if="recordset_editing" style="border: 1px solid gray; background-color: white; padding: 5px; margin-top: 3px; margin-bottom: 3px">
                    <b>RECORDSET definition</b><br>
                    <table>
                        <tr>
                            <td style="text-align: right">Class</td>
                            <td style="text-align: right">
                                <input v-model="current_metadata.class" size="35" style="font-weight: bold">
                            </td>
                            <td rowspan=3 style="vertical-align: bottom; padding-left: 50px">
                                <span @click="cancel_recordset_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                                <button @click="save_recordset_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                                <br>
                                <span v-if="waiting" class="waiting">Performing the update</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="text-align: right">Order by</td>
                            <td>
                                <input v-model="current_metadata.order_by" size="40">
                                </td>
                        </tr>
                        <tr>
                            <td style="text-align: right">Number records shown per page</td>
                            <td>
                                <input v-model="current_metadata.n_group" size="4">
                                </td>
                        </tr>
                    </table>
                </div>


                <!--  STANDARD CONTROLS (a <SPAN> element that can be extended with extra controls),
                      EXCEPT for the "edit" control, which is provided by this Vue component itself.
                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component;
                      none get intercepted and handled here
                -->
                    <!-- OPTIONAL MORE CONTROLS to the LEFT of the standard ones would go here -->

                    <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                                  v-bind:controls_to_hide="['edit']"
                                  v-on="$listeners"
                    >
                    </vue-controls>

                    <!-- OPTIONAL MORE CONTROLS to the RIGHT of the standard ones would go here -->

                <!--  End of Standard Controls -->

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                headers: [],            // EXAMPLE:  ["quote", "attribution", "notes"]

                recordset: [],          // This will get loaded by querying the server when the page loads

                current_page: 1,

                total_count: null,      // Size of the entire (un-filtered) recordset

                record_being_editing: null, // The "ID" of the record currently being edited, if any;
                                            // for now, only one record at a time may be edited

                recordset_editing: false,   // If true, the definition of the recordset goes into editing mode

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_metadata: Object.assign({}, this.item_data),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                pre_edit_metadata: Object.assign({}, this.item_data),   // Clone from the original data passed to this component

                // The following 2 apply to the single record currently being edited (just one at most)
                record_at_start_of_edit:    null,
                record_mid_edit:            null,


                new_record: {},         // Used for the addition of new record; note that it's valid
                                        // to do a Vue <<input v-models="obj[key]"> to non-existing keys of an object;
                                        // Vue will automatically add the key/value pairs as they get entered in the form


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

            if (this.item_data.uri < 0)  {  // A negative URI is a convention to indicate a just-created Recordset
                this.edit_recordset();
                return;
            }

            this.get_fields();      // Fetch from the server the field names for this Recordset

            this.get_recordset(1);  // Fetch contents of the 1st block of the Recordset from the server
        },



        // ------------------------------   METHODS   ------------------------------
        methods: {

            insert_blanks(str)
            /*  For the purpose of facilitating the breakup by the browser
                of long headers into multiple lines,
                insert a blank space after each underscore and each "/".
                EXAMPLE: "max_temp/safe_temp" will be returned as "max_ temp/ safe_ temp"
             */
            {
                var transformed = str.replace(/_/g, '_ ');      // Insert a blank after each of the underscores in the string

                return transformed.replace(/\//g, '/ ');        // Insert a blank after each of the forward slashes in the string
            },




            edit_recordset()
            {
                console.log(`Editing entire recordset`);
                this.recordset_editing = true;
            },


            cancel_recordset_edit()
            /*   Invoked when the user cancels the edit-in-progress for the recordset definition,
                or when the save operation fails.
                Revert any changes, and exit the edit mode
             */
            {
                // Restore the data to how it was prior to the aborted changes

                this.current_metadata = Object.assign({}, this.pre_edit_metadata);  // Clone from pre_edit_metadata

                this.recordset_editing = false;               // Exit the editing mode for the recordset definition
            },



            edit_record(record)
            /*  Edit an individual row (record).
                Invoked when the user clicks on the "EDIT" control for that record

                :param record:  An object with the standard properties
                                    "internal_id", "node_labels", and "uri" [may or may not have a value],
                                    plus whatever fields are part of the given particular record (node)
                                    EXAMPLE:  {internal_id: 123, node_labels: ["Restaurant"], uri: "r-88",
                                               name: "Pizzeria NY", city: "NYC"}
             */
            {
                console.log(`Editing the following individual record in recordset:`);
                console.log(record);

                this.record_being_editing = record.internal_id;     // Specify that editing is in progress for this record

                this.record_at_start_of_edit = Object.assign({}, record);   // Clone the object
                this.record_mid_edit = Object.assign({}, record);           // Clone the object
            },


            cancel_record_edit()
            {
                this.record_being_editing = null;       // To indicate that no record is being edited

                // Clear the temporary variables used for the editing
                this.record_at_start_of_edit = null;
                this.record_mid_edit = null;
            },

            save_record_edit()
            {
                alert("Editing individual records not yet implemented, sorry!");
                this.cancel_record_edit();      // Clean up and leave the editing mode for the record being edited
            },



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
            },




            /*
                ---  SERVER CALLS  ---
             */

            save_new_record()
            // Send a request to the server, to save a record newly entered thru a form
            {
                console.log(`In save_new_record(), for Recordset with URI '${this.current_metadata.uri}'`);

                var url_server_api = "/BA/api/create_data_node_JSON";
                var post_obj = {class_name: this.current_metadata.class};       // Class of the records

                //console.log("New record just entered:");
                //console.log(this.new_record);

                for (k in this.new_record ) {
                    //console.log(`key: '${k}' , value: ${this.new_record[k]}`);
                    post_obj[k] = this.new_record[k];
                }

                console.log(`About to contact the server at '${url_server_api}' .  POST object:`);
                console.log(post_obj);      // EXAMPLE:  {class_name: "Quote", quote: "Inspiration exists, but it has to find us working", attribution: "Pablo Picasso"}

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: true,
                             callback_fn: this.finish_save_new_record
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_save_new_record(success, server_payload, error_message)
            // Callback function to wrap up the action of save_new_record() upon getting a response from the server
            {
                console.log("Finalizing the save_new_record() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `New record added`;
                    //...
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    //...
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;       // Make a note that the asynchronous operation has come to an end
                this.new_record = {};       // Clear the data-entry fields
            },



            save_recordset_edit()
            // Send a request to the server, to update or create this Recordset's definition
            {
                console.log(`In save_recordset_edit(), for Recordset with URI '${this.current_metadata.uri}'`);

                // Send the request to the server, using a POST

                if (this.current_metadata.uri < 0) {    // A negative URI is a convention to indicate a just-created Recordset
                    // Create a new Recordset
                    var url_server_api = "/BA/api/add_item_to_category_JSON";
                    var post_obj = {category_uri: this.category_id,
                                    class_name: this.item_data.class_name,
                                    insert_after: this.item_data.insert_after,   // URI of Content Item to insert after, or keyword "TOP" or "BOTTOM"

                                    class: this.current_metadata.class,
                                    n_group: parseInt(this.current_metadata.n_group),
                                    order_by: this.current_metadata.order_by
                                   };
                }
                else  {
                    // Update an existing Recordset
                    var url_server_api = "/BA/api/update_content_item_JSON";
                    var post_obj = {uri: this.current_metadata.uri,
                                    class_name: this.item_data.class_name,

                                    class: this.current_metadata.class,
                                    n_group: parseInt(this.current_metadata.n_group),
                                    order_by: this.current_metadata.order_by
                                   };
                }

                console.log(`About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: true,
                             callback_fn: this.finish_save_recordset_edit
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_save_recordset_edit(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of save_recordset_edit(() upon getting a response from the server
            {
                console.log("Finalizing the save_recordset_edit() operation...");
                //console.log(`Custom data passed: ${custom_data}`);
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    if (this.current_metadata.uri < 0)  {
                        // If this was a newly-created item (with the temporary negative ID)
                        this.status_message = `Recordset creation completed`;
                        this.current_metadata.uri = server_payload;     // Update the temporary URI with the value assigned by the server
                    }
                    else
                        this.status_message = `Recordset update completed`;

                    // Inform the parent component of the new state of the data
                    //TODO: get this to work, and also manage changes in URI (maybe pass original negative URI as separate arg, or extra field in object)
                    //console.log("Recordsets component sending `updated-item` signal to its parent, with the following data:");
                    //this.$emit('updated-item', this.current_metadata);

                    // Synchronize the baseline data to the current one
                    this.pre_edit_metadata = Object.assign({}, this.current_metadata);  // Clone

                    this.get_fields();          // Fetch from the server the field names for this Recordset
                    this.get_recordset(1);      // Fetch contents of the 1st block of the Recordset from the server
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    this.current_metadata = Object.assign({}, this.pre_edit_metadata);  // Clone, to restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end
                this.recordset_editing = false; // Leave the editing mode
            },



            get_fields()
            /*  Make a server call to obtain all Schema field of the Class that this recordset is based on
                E.g.
                    NeoSchema.get_class_properties(class_node="Quote", include_ancestors=True, exclude_system=True)
                to fetch:
                    ['quote', 'attribution', 'notes']

                If successful, it will update the value for this.headers
            */
            {
                console.log(`In get_fields(): attempting to retrieve field names of recordset with URI '${this.current_metadata.uri}'`);

                const url_server_api = "/BA/api/get_class_properties";

                const data_obj = {class_name: this.current_metadata.class,
                                  include_ancestors: true,
                                  exclude_system: true
                                 };

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(data_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   data_obj: data_obj,
                                json_encode_send: true,
                                callback_fn: this.finish_get_fields
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_get_fields(success, server_payload, error_message)
            // Callback function to wrap up the action of get_fields() upon getting a response from the server
            {
                console.log("Finalizing the get_fields() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    this.headers = server_payload;
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

            }, // finish_get_fields



            get_recordset(page)
            /*  Request from the server the specified page (group of records) of the recordset.
                If successful, it will update the values for:
                        this.recordset
                        this.total_count
                        this.current_page
              */
            {
                skip = (page-1) * this.current_metadata.n_group;

                //console.log(`In get_recordset(): attempting to retrieve page ${page} of recordset with URI '${this.current_metadata.uri}'`);

                // Send the request to the server, using a GET
                const url_server_api = "/BA/api/get_filtered";

                // Note: for now, we're actually doing a database search by node label,
                //       rather than by Schema Class
                const get_obj = {label: this.current_metadata.class,
                                 order_by: this.current_metadata.order_by,
                                 limit: this.current_metadata.n_group,
                                 skip: skip};

                const my_var = page;        // Optional parameter to pass

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(get_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   method: "GET",
                                data_obj: get_obj,
                                json_encode_send: true,
                                callback_fn: this.finish_get_recordset,
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
                    this.recordset = server_payload.recordset;
                    this.total_count = server_payload.total_count;
                    this.current_page = custom_data;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            } // finish_get_recordset

        }  // methods

    }
); // end component