/*  MIT License.  Copyright (c) 2021 Julian A. West
 */

Vue.component('vue-plugin-r',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_data:  EXAMPLE: {"item_id":52,"pos":10,"schema_code":"r",class_name:"German Vocabulary","German":"Tier","English":"animal"}
                                 (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)
            category_id:
            index:          The zero-based position of the Record on the page
            item_count:     The total number of Content Items (of all types) on the page
            schema_data:    A list of field names, in order.
                                EXAMPLE: ["French", "English", "notes"]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <table class='r-main'>
            <!-- Header row  -->
            <tr>
                <th v-for="cell in this.determine_headers()">
                {{cell}}
                </td>

                <th>controls</th>
            </tr>

            <!-- Data row  -->
            <tr>
                <td v-for="key in this.determine_cells()">
                    <!-- Display SPAN or INPUT elements, depending on the editing status -->
                    <span v-if="!editing_mode" v-html="render_cell(current_data[key])"></span>
                    <input v-if="editing_mode" type="text" size="25" v-model="current_data[key]">
                </td>

                <td>
                    <span v-if="!editing_mode" style="color:gray">
                        <button type="button"
                                  v-clipboard:copy="Object.values(current_data)[0]"
                                  v-clipboard:success="onCopy"
                                  v-clipboard:error="onError">Copy the 1st cell
                        </button>   <!-- EXAMPLE to copy a named field: current_data['English'] -->
                    </span>
                </td>
            </tr>

            <tr v-if="editing_mode">    <!-- Extra table row with SAVE/Cancel controls -->
            <td colspan=3>
                <button @click="save()">SAVE</button>
                <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                <span v-if="waiting_mode" style="margin-left:15px">saving...</span>
                <span v-if="waiting_for_server" style="margin-left:15px; color:gray">Loading all fields...</span>
            </td>
            </tr>

            </table>
            <span v-if="status!='' && !editing_mode">Status : {{status}}</span>

            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item   (which is not listened to by the root component)
            -->
            <vue-controls v-bind:allow_editing="allow_editing"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item(item_data)">
            </vue-controls>

            \n</div>\n		<!-- End of outer container box -->
            `,


        data: function() {
            return {
                editing_mode: (this.item_data.item_id == -1 ? true : false),    // -1 means "new Item"

                /*  Comparison of 3 fundamental objects -

                    "PROP" DATA PASSED BY THE PARENT COMPONENT (NOT copied to component variables):
                        item_data:      The FULL data passed by the parent component

                    COMPONENT VARIABLES:
                        current_data:   Object with the values bound to the editing fields, cloned from the "prop" data;
                                        it'll change in the course of the edit-in-progress

                        original_data:  Object with pre-edit data,
                                        used to restore the data in case of an edit Cancel or failed save

                    EXAMPLE of item_data (a PROP, not a component variable!):
                        {
                            "English": "Love",
                            "German": "Liebe",
                            "item_id": 61,
                            "schema_code": "r",
                            "class_name": "German Vocabulary",
                            "pos": 0    <- BEING PHASED OUT
                        }

                    EXAMPLE of current_data and original_data:
                        {
                            "English": "Love",
                            "German": "Liebe"
                        }

                    Note that the objects may lack some of the fields specified by the Schema;
                        or, if the Schema is lax, extra fields might be present
                 */
                current_data: this.clone_and_standardize(this.item_data),   // Scrub some data, so that it won't show up in the tabular format
                original_data: this.clone_and_standardize(this.item_data),
                // NOTE: clone_and_standardize() gets called twice

                waiting_for_server: ((this.item_data.item_id != -1) ? false : this.get_fields_from_server(this.item_data)), // -1 means "new Item"

                waiting_mode: false,
                status: "",
                error_indicator: false
            }
        }, // data


        // ------------------------------   METHODS   ------------------------------
        methods: {

            determine_headers()
            {
                if (this.schema_data.length == 0)
                    return Object.keys(this.current_data);      // Fallback, if Schema info isn't available

                console.log("In determine_headers(): schema_data = ", this.schema_data);
                //console.log("this.current_data = ", this.current_data);
                //console.log("All keys of the above: ", Object.keys(this.current_data));
                let all_keys = [];

                for (let i = 0; i < this.schema_data.length; i++) { // Loop thru all field names prescribed by the Schema...
                    key_in_schema = this.schema_data[i];
                    if (key_in_schema in this.current_data)         // ... if the field name is actually present, add it to the all_keys array
                        all_keys.push(key_in_schema);
                }

                // TODO: at this point, should add any keys in this.current_data that aren't declared in the Schema, if any

                console.log("   all_keys = ", all_keys);

                //return Object.keys(this.current_data);
                return all_keys;
            },

            determine_cells()
            {
                //return this.current_data;
                //return Object.keys(this.current_data);
                return this.determine_headers();        // TODO: maybe save, to avoid re-computing
            },


            // Used to copy cell contents into the system clipboard
            onCopy: function (e) {
                console.log('You just copied: ' + e.text);
            },
            onError: function (e) {
                alert('Failed to copy texts');
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
            },


            get_fields_from_server(item)
            // Initiate request to server, to get all the field names specified by the Schema of the given Content Item
            {
                console.log(`Processing a Content Item of type 'r', with item_id = ${item.item_id}`);
                if (item.item_id == -1) {
                    url_server = "http://localhost:5000/BA/api/get_properties_by_class_name";               // New record
                    post_obj = {class_name: item.class_name}
                    console.log(`About to contact the server at ${url_server}.  POST object:`);
                    console.log(post_obj);
                    ServerCommunication.contact_server(url_server,
                            {payload_type: "JSON", post_obj: post_obj, callback_fn: this.finish_get_fields_from_server});
                }
                else {
                    url_server = "http://localhost:5000/BA/api/get_properties_by_item_id/" + item.item_id;  // Existing record
                    console.log(`About to contact the server at ${url_server}`);
                    ServerCommunication.contact_server_JSON(url_server, "", this.finish_get_fields_from_server);
                }

                return true;
            },

            finish_get_fields_from_server(success, server_payload, error_message)
            /*  Callback function to wrap up the action of get_fields_from_server() upon getting a response from the server.
                The server returns a JSON value
              */
            {
                console.log("Finalizing the get_fields_from_server() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: " , server_payload);
                    // EXAMPLE:  [ "Notes", "English", "French" ]

                    // Create new cloned objects (if just altering existing objects, Vue doesn't detect the change)
                    new_current_data = Object.assign({}, this.current_data);    // Clone the object

                    for (let i = 0; i < server_payload.length; i++) {
                        field_name = server_payload[i]

                        /* Only add fields not already present
                         */
                        if (!(field_name in this.current_data))  {
                            console.log("    Adding missing field: ", field_name);
                            new_current_data[field_name] = "";
                        }
                    }

                    this.current_data = new_current_data;
                }
                else  {             // Server reported FAILURE
                    //this.status = `FAILED lookup of extra fields`;
                    //this.error_indicator = true;
                }

                // Final wrap-up, regardless of error or success
                this.waiting_for_server = false;

            }, // finish_get_fields_from_server


            clone_and_standardize(obj)
            // Clone, and remove keys that don't get shown nor edited
            {
                clone_obj = Object.assign({}, obj);     // Clone the object

                // Scrub some data, so that it won't show up in the tabular format
                delete clone_obj.item_id;
                delete clone_obj.schema_code;
                delete clone_obj.class_name;
                delete clone_obj.insert_after;
                delete clone_obj.pos;           // TODO: this might be getting phased out

                return clone_obj;
            },

            manage_newlines(text)   // NOT IN CURRENT USE
            // Replace all newlines in the text with the HTML newline tag "<br>"
            {
                if (text == null)
                    return "";

                return "<pre>" + text + "</pre>";

                // The following isn't as clean, if text alignment was created based on monospace
                //text = text.replace(/\n/g, "<br>")     // g means globally: replace all \n with <br>
                //text = text.replace(/ /g, "&nbsp;")    // g means globally: replace all blanks with &nbsp;
                //return text;
            },


            edit_content_item(item)
            {
                console.log(`'Records' component received Event to edit content item of type '${item.schema_code}' , id ${item.item_id}`);
                this.editing_mode = true;

                this.get_fields_from_server(item);  // Consult the schema
                this.waiting_for_server = true;
            },


            save()
            {
                /*  EXAMPLE of this.current_data and this.original_data:
                        {
                            "English": "Love",
                            "German": "Liebe"
                        }

                    EXAMPLE of this.item_data:
                        {
                            "English": "Love",
                            "German": "Liebe",
                            "item_id": 61,
                            "schema_code": "r",
                            "insert_after": 123,
                            "class_name": "German Vocabulary",
                            "pos": 0
                        }
                */

                // Start the body of the POST to send to the server.  TODO: switch to newer methods of ServerCommunication
                post_body = "schema_code=" + this.item_data.schema_code;

                if (this.item_data.item_id == -1)  {     // The -1 is a convention indicating a new Content Item to create
                    // Needed for NEW Content Items
                    post_body += "&category_id=" + this.category_id;
                    post_body += "&class_name=" + encodeURIComponent(this.item_data.class_name);
                    const insert_after = this.item_data.insert_after;   // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                    post_body += "&insert_after=" + insert_after;

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data)  {
                        // Only pass non-blank values
                        if (this.current_data[key] != "")
                            post_body += "&" + key + "=" + encodeURIComponent(this.current_data[key]);
                    }
                    // EXAMPLE of post_body for a NEW record:
                    //          "schema_code=r&category_id=12&class_name=German%20Vocabulary&insert_after=123&German=Liebe"

                    url_server = `/BA/api/simple/add_item_to_category`;   // URL to communicate with the server's endpoint
                }
                else  {
                    // Update an EXISTING record
                    post_body += "&item_id=" + this.item_data.item_id;

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data) {
                        if ( (this.current_data[key] != "")  ||  (key in this.original_data) )
                            // Non-blanks always lead to updates; blanks only if the field was originally present
                            post_body += "&" + key + "=" + encodeURIComponent(this.current_data[key]);
                    }
                    // EXAMPLE of post_body for an EXISTING record: "schema_code=r&item_id=62&English=Love&German=Liebe"

                    url_server = `/BA/api/simple/update`;   // URL to communicate with the server's endpoint
                }


                this.waiting_mode = true;
                this.error_indicator = false;   // Clear possible past message

                console.log("In 'vue-plugin-r', save().  post_body: ", post_body);
                ServerCommunication.contact_server_TEXT(url_server, post_body, this.finish_save);
            }, // save


            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID
             */
            {
                console.log("Finalizing the Record saving operation...");
                if (success)  {     // Server reported SUCCESS
                    this.status = `Successful edit`;

                    // Eliminate some un-needed fields from the display
                    for (field in this.current_data)  {
                        if (this.current_data[field] != "")
                            console.log("Field still needed because non-empty: ", field);
                        else if (field in this.original_data)
                            console.log("Field blank but still needed because in original data: ", field);
                        else {
                            console.log("Eliminating field no longer in need to display: ", field);
                            delete this.current_data[field];    // Zap b/c blank, and not present before edit
                        }
                    }

                    // If this was a new item (with the temporary ID of -1), update its ID with the value assigned by the server
                    if (this.item_data.item_id == -1)
                        this.current_data.item_id = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Records component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the accepted baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.status = `FAILED edit`;
                    this.error_indicator = true;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.editing_mode = false;      // Exit the editing mode
                this.waiting_mode = false;      // Make a note that the asynchronous operation has come to an end

            }, // finish_save


            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.item_id == -1) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Records component sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }
            } // cancel_edit

        }  // METHODS

    }
); // end component