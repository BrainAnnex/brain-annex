/*  Vue component to display and edit Content Items of type "r" (generic Records)
 */

Vue.component('vue-plugin-r',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_data:  An object with the relevant data about this Record item

                        EXAMPLE: {class_name:"German Vocabulary",
                                  "uri":"52", "pos":10, "schema_code":"r",
                                  "German":"Tier", "English":"animal"}
                                  (if uri is a negative number, it means that it's a newly-created header,
                                  not yet registered with the server)

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The ID of the Category page where this record is displayed (used when creating new records)
            index:          The zero-based position of the Record on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names, in Schema order.
                                EXAMPLE: ["French", "English", "notes"]
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <table class='r-main'>
            <!-- Header row  -->
            <tr>
                <th v-for="header_cell in this.determine_headers()">
                    {{header_cell}}
                </th>

                <!--  <th>controls</th>   Experimental control cell not in current use  -->

                <th style='font-size:9px'><i>LINKS</i></th>   <!-- Cell to show all existing links -->
            </tr>


            <!--
                Row for the data, the controls and the links
             -->
            <tr>
                <td v-for="key in this.determine_cells()">
                    <!-- Display SPAN or INPUT elements, depending on the editing status -->
                    <span v-if="!editing_mode" v-html="render_cell(current_data[key])"></span>
                    <input v-if="editing_mode" type="text" size="25" v-model="current_data[key]">
                </td>

                <!-- "Controls" cell currently not in use
                <td>
                    <span v-if="!editing_mode" style="color:gray">
                        <button type="button"
                                  v-clipboard:copy="Object.values(current_data)[0]"
                                  v-clipboard:success="onCopy"
                                  v-clipboard:error="onError">Copy the 1st cell
                        </button>
                    </span>
                </td>
                -->

                <!-- Cell for the links  -->
                <td v-if="!expanded_row" @click="expand_links_cell()" class="clickable-icon" style='background-color:#333' align="center" >    <!-- "See more" cell  -->
                    <span style='color:#DDD; font-weight:bold; font-size:18px'>&gt;</span>
                </td>
                <td v-else>
                    <span v-if="waiting_for_links">Fetching links from server</span>

                    <img v-on:click='expanded_row=false'  src='/BA/pages/static/graphics/thin_left_arrow_32.png'
                         class='clickable-icon' style='float: right'
                         title='Hide' alt='Hide'>

                    <template v-if="!waiting_for_links">

                        <template v-if="in_links.length == 0 && out_links.length == 0">
                            <span style='color:gray'>(No links)</span>
                        </template>

                        <!-- Inbound links  -->
                        <div v-for="link in in_links" style='display: inline-block; padding-bottom:2px'>
                            <span class="link-count">({{link[1]}})</span> &rArr;
                            <span @click="show_linked_records(link[0], 'IN')" class="clickable-icon relationship-in">{{link[0]}}</span> &nbsp;
                        </div>

                        <br>

                        <!-- Outbound links  -->
                        <div v-for="link in out_links" style='display: inline-block; padding-bottom:2px'>
                            <span @click="show_linked_records(link[0], 'OUT')" class="clickable-icon relationship-out">{{link[0]}}</span>&rArr;
                            <span class='link-count'>({{link[1]}})</span> &nbsp;
                        </div>

                    </template>

                </td>

            </tr>
            </table>


            <!-- Area below the table, for the linked records (if shown) -->
            <div v-if="linked_records.length > 0" style="border:1px solid #DDD; margin-left: 40px; margin-bottom: 25px; padding-left: 5px">

                <!-- Display each linked record in turn -->
                <div v-for="(item, index) in linked_records">
                    <vue-plugin-r-linked
                        v-bind:key="item.uri"

                        v-bind:item_data="item"
                        v-bind:rel_name="link_name"
                        v-bind:rel_dir="rel_dir"
                    >
                    </vue-plugin-r-linked>
                </div>

            </div>

            <!-- Area below the table, for the relationship editing (if in editing mode) -->
            <div v-if="editing_mode && (in_links_schema.length > 0 || out_links_schema.length > 0)"
                 style="border-left:1px solid #DDD; padding-left:0; padding-top:0; padding-bottom:10px">
                    <div v-for="link in in_links_schema" class="edit-link"><b>IN_LINK</b><br>{{link}}</div>
                    <div v-for="link in out_links_schema" class="edit-link"><b>OUT_LINK</b><br><br>{{link}}</div>
            </div>

            <!-- Area below the table, with SAVE/Cancel controls (if in editing mode) -->
            <p v-if="editing_mode" style="border-left:1px solid #DDD; padding-left:5px">
                <button @click="save()">SAVE</button>
                <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                <span v-if="waiting_mode" style="margin-left:15px">saving...</span>
                <span v-if="waiting_for_server" style="margin-left:15px; color:gray">Loading all fields...</span>
            </p>

            <span v-if="status!='' && !editing_mode">Status : {{status}}</span>

            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item   (which is not listened to by the root component)
            -->
            <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item(item_data)">
            </vue-controls>

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                editing_mode: (this.item_data.uri < 0  ? true : false), // Negative uri means "new Item"

                /*  Comparison of 3 fundamental objects -

                    "PROP" DATA PASSED BY THE PARENT COMPONENT (NOT copied to component variables):
                        item_data:      The FULL data passed by the parent component

                    COMPONENT VARIABLES:
                        current_data:   Object with the values bound to the editing fields, cloned from the "prop" data;
                                        it'll change in the course of the edit-in-progress

                        original_data:  Object with pre-edit data,
                                        used to restore the data in case of an edit Cancel or failed save

                    EXAMPLE of item_data (a PROP, not a variable of this component!):
                        {
                            "English": "Love",
                            "German": "Liebe",
                            "uri": "61",
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
                current_data: this.clone_and_standardize(this.item_data),
                original_data: this.clone_and_standardize(this.item_data),
                // Scrub some data, so that it won't show up in the tabular format
                // NOTE: clone_and_standardize() gets called twice

                expanded_row: false,

                in_links_schema: [],    // List of the names of all Inbound links as specified by the Schema
                out_links_schema: [],   // List of the names of all Outbound links as specified by the Schema (except for "INSTANCE_OF")

                in_links: [],           // List of the names/counts of all the actual Inbound links
                out_links: [],          // List of the names/counts of all the actual Outbound links
                links_status: '',
                links_error_indicator: false,
                waiting_for_links: false,   // Note that we have 2 different "wait for server" flags: this one is specific to getting the links

                linked_records: [],
                // For now, just one set of linked records (linked thru a given relationship) is shown at a time
                link_name: '',
                rel_dir: 'IN',

                // Note that we have 2 different "wait for server" flags
                waiting_for_server: (this.item_data.uri < 0) ? this.get_fields_from_server(this.item_data) : false, // Negative URI means "new Item"

                waiting_mode: false,
                status: "",
                error_indicator: false
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            show_linked_records(rel_name, dir)
            {
                const record_id = this.item_data.uri;

                console.log(`Show the records linked to record URI '${record_id}' by the ${dir}-bound relationship '${rel_name}'`);
                this.get_linked_records_from_server(record_id, rel_name, dir);
            },


            expand_links_cell()
            // Expand the table cell that will show the summary of the inbound/outbound links
            {
                this.expanded_row = true;
                this.get_link_summary_from_server(this.item_data);
            },


            determine_headers()
            /*  Return a list of field names for this Content Item.
                The Item's fields in the schema go first, in the schema order,
                followed by any other field not in the Schema, in order of appearance.

                Note: this is quite similar to the canonical_field_list() method in the
                     Vue root component.  TODO: eventually merge
             */
            {
                if (this.schema_data.length == 0)
                    return Object.keys(this.current_data);      // Fallback, if Schema info isn't available

                //console.log("In determine_headers(): schema_data = ", this.schema_data);
                //console.log("this.current_data = ", this.current_data);
                //console.log("All keys of the above: ", Object.keys(this.current_data));
                let all_keys = [];

                for (let i = 0; i < this.schema_data.length; i++) { // Loop thru all field names prescribed by the Schema...
                    key_in_schema = this.schema_data[i];
                    if (key_in_schema in this.current_data)         // ... if the field name is actually present, add it to the all_keys array
                        all_keys.push(key_in_schema);
                }

                let field_list = Object.keys(this.current_data);     // All the fields in record (pre-scrubbed for special ones)
                // Add all the item's fields that aren't in its Schema (non-standard fields, if any)
                for (let i = 0; i < field_list.length; i++)
                    if (! this.schema_data.includes(field_list[i]))
                        all_keys.push(field_list[i]);

                //console.log("   all_keys = ", all_keys);

                //return Object.keys(this.current_data);
                return all_keys;
            },

            determine_cells()
            {
                //return this.current_data;
                //return Object.keys(this.current_data);
                return this.determine_headers();        // TODO: maybe save, to avoid re-computing
            },


            // Used to copy cell contents into the system clipboard (NOT in current use)
            onCopy: function (e) {
                console.log('You just copied: ' + e.text);
            },
            onError: function (e) {
                alert('Failed to copy texts');
            },


            render_cell(cell_data)
            /*  If the passed argument is a string that appears to be a URL, convert it into a string with HTML code
                for a hyperlink that opens in a new window;
                if the URL is very long, show it in abbreviated form in the hyperlink text.
                In all other cases, just return the argument.

                Note: this function is also found in single_records.js
             */
            {
                const max_url_len = 35;     // For text to show, NOT counting the protocol part (such as "https://")

                if (typeof cell_data != "string")
                     return cell_data;

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
                SERVER CALLS
             */

            get_linked_records_from_server(record_id, rel_name, dir)
            /* Initiate request to server, to get the list of the properties
               of the data nodes linked to the one specified by uri,
               by the relationship named by rel_name, in the direction specified by dir
             */
            {
                console.log(`Getting the properties of data nodes linked to record with uri ${record_id} by means of the ${dir}-bound relationship '${rel_name}'`);

                let url_server = "/BA/api/get_records_by_link";
                let post_obj = {uri: record_id, rel_name: rel_name, dir: dir};
                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);

                ServerCommunication.contact_server(url_server,
                            {post_obj: post_obj,
                             callback_fn: this.finish_get_linked_records_from_server,
                             custom_data: [rel_name, dir]});
            },

            finish_get_linked_records_from_server(success, server_payload, error_message, custom_data)
            /*  Callback function to wrap up the action of get_linked_records_from_server() upon getting a response from the server.
                The server returns a JSON value.
              */
            {
                console.log("Finalizing the get_linked_records_from_server() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: " , server_payload);
                    /*  EXAMPLE:
                            [
                                {uri: 100, name: "mushrooms pie", eval: "+", schema_code: "r"},
                                {uri: 180, name: "Margherita pie", eval: "OK", schema_code: "r"}
                            ]
                     */
                    this.linked_records = server_payload;
                    this.link_name = custom_data[0];
                    this.rel_dir = custom_data[1];
                }
                else  {             // Server reported FAILURE
                   //this.links_status = `FAILED server lookup of link data`;
                   //this.links_error_indicator = true;
                }

                // Final wrap-up, regardless of error or success
                //this.waiting_for_links = false;

            }, // finish_get_link_summary_from_server



            get_link_summary_from_server(item)
            // Initiate request to server, to get the list of the names/counts of all the actual Inbound and Outbound links
            {
                console.log(`Getting the links info for a Content Item of type 'r', with uri = ${item.uri}`);
                let url_server = "/BA/api/get_link_summary/" + item.uri;
                console.log(`About to contact the server at ${url_server}`);
                this.waiting_for_links = true;
                ServerCommunication.contact_server(url_server,
                            {callback_fn: this.finish_get_link_summary_from_server});
            },

            finish_get_link_summary_from_server(success, server_payload, error_message)
            /*  Callback function to wrap up the action of get_link_summary_from_server() upon getting a response from the server.
                The server returns a JSON value.
              */
            {
                console.log("Finalizing the get_link_summary_from_server() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: " , server_payload);
                    /*  EXAMPLE:
                            {"in":  [
                                        ["BA_served_at", 3]
                                    ],
                            "out":  [
                                        ["BA_located_in", 1],
                                        ["BA_cuisine_type", 1]
                                    ]
                            }
                     */
                     this.in_links = server_payload.in;
                     this.out_links = server_payload.out;
                }
                else  {             // Server reported FAILURE
                   this.links_status = `FAILED server lookup of link data`;
                   this.links_error_indicator = true;
                }

                // Final wrap-up, regardless of error or success
                this.waiting_for_links = false;

            }, // finish_get_link_summary_from_server



            get_fields_from_server(item)
            // Initiate request to server, to get all the field and link names specified by the Schema for this Record
            {
                console.log(`Looking up Schema info for a Content Item of type 'r', of Class '${item.class_name}'`);

                // The following works whether it's a new record or an existing one (both possess a "class_name" attribute)
                let url_server = "/BA/api/get_class_schema";
                let post_obj = {class_name: item.class_name};
                console.log(`About to contact the server at ${url_server}.  POST object:`);
                console.log(post_obj);
                ServerCommunication.contact_server(url_server,
                            {post_obj: post_obj, callback_fn: this.finish_get_fields_from_server});

                return true;
            },

            finish_get_fields_from_server(success, server_payload, error_message)
            /*  Callback function to wrap up the action of get_fields_from_server() upon getting a response from the server.
                The server returns a JSON value.
                TODO: maybe save the returned values in the root component, to reduce server calls
              */
            {
                console.log("Finalizing the get_fields_from_server() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: " , server_payload);
                    /*  EXAMPLE:
                            {
                            "properties":   [
                                              "name",
                                              "website",
                                              "address"
                                            ],
                            "in_links":     ["BA_served_at"],
                            "out_links":    ["BA_located_in", "BA_cuisine_type"]
                            }
                     */

                    let properties = server_payload["properties"];
                    // EXAMPLE:  [ "Note", "English", "French" ]

                    // Create new cloned objects (if one just alters existing objects, Vue doesn't detect the change!)
                    new_current_data = Object.assign({}, this.current_data);    // Clone the object

                    for (let i = 0; i < properties.length; i++) {
                        field_name = properties[i]

                        /* Only add fields not already present
                         */
                        if (!(field_name in this.current_data))  {
                            //console.log("    Adding missing field: ", field_name);
                            new_current_data[field_name] = "";   // Blank field value
                        }
                    }

                    this.current_data = new_current_data;  // Replace the record bound to the UI

                    this.in_links_schema = server_payload["in_links"];
                    this.out_links_schema = server_payload["out_links"];
                }
                else  {             // Server reported FAILURE
                    //this.status = `FAILED lookup of extra fields`;
                    //this.error_indicator = true;
                }

                // Final wrap-up, regardless of error or success
                this.waiting_for_server = false;

            }, // finish_get_fields_from_server


            clone_and_standardize(obj)
            // Clone the passed object; then remove some keys that shouldn't get shown nor edited
            {
                clone_obj = Object.assign({}, obj);     // Clone the object

                // Scrub some data, so that it won't show up in the tabular format
                delete clone_obj.uri;
                delete clone_obj.schema_code;
                delete clone_obj.class_name;
                delete clone_obj.insert_after;  // TODO: is this field still present?
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
                console.log(`'Records' component received Event to edit content item of type '${item.schema_code}' , id ${item.uri}`);
                this.editing_mode = true;

                this.get_fields_from_server(item);      // Consult the schema
                this.waiting_for_server = true;
            },


            save()
            // Invoked when the user asks to save the edit-in-progress
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
                            "uri": 61,
                            "schema_code": "r",
                            "insert_after": 123,
                            "class_name": "German Vocabulary",
                            "pos": 0
                        }
                */

                // Start the body of the POST to send to the server
                var post_obj = {schema_code: this.item_data.schema_code};

                if (this.item_data.uri < 0)  {     // The negative URI is a convention indicating a new Content Item to create
                    // Needed for NEW Content Items
                    post_obj["category_id"] = this.category_id;
                    post_obj["class_name"] = this.item_data.class_name;
                    post_obj["insert_after"] = this.item_data.insert_after;   // URI of Content Item to insert after, or keyword "TOP" or "BOTTOM"

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data)  {
                        // Only pass non-blank values
                        if (this.current_data[key] != "")  {
                            post_obj[key] = this.current_data[key];
                        }
                    }

                    var url_server_api = `/BA/api/add_item_to_category`;   // URL to communicate with the server's endpoint
                }
                else  {
                    // Update an EXISTING record
                    post_obj["uri"] = this.item_data.uri;
                    post_obj["class_name"] = this.item_data.class_name;

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data) {
                        if ( (this.current_data[key] != "")  ||  (key in this.original_data) )  {
                            // Non-blanks always lead to updates; blanks only if the field was originally present
                            post_obj[key] = this.current_data[key];
                        }
                    }

                    var url_server_api = `/BA/api/update_content_item`;   // URL to communicate with the server's endpoint
                }


                console.log(`'vue-plugin-r' : about to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                                                   {post_obj: post_obj, callback_fn: this.finish_save});

                this.waiting_mode = true;
                this.error_indicator = false;   // Clear possible past message

            }, // save

            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned URI
             */
            {
                console.log("Finalizing the Record saving operation...");
                if (success)  {     // Server reported SUCCESS
                    this.status = `Successful edit`;

                    // Eliminate some un-needed fields from the display
                    for (field in this.current_data)  {
                        if (this.current_data[field] != "")
                            console.log("Field still needed because non-empty: ", field);
                        else if (field in this.original_data)  {
                            //console.log("Field blank but was in original data [deleted anyway]: ", field);
                            delete this.current_data[field];     // Zap b/c blank,
                        }
                        else {
                            //console.log("Eliminating field no longer in need to display: ", field);
                            delete this.current_data[field];    // Zap b/c blank [NO LONGER DONE:, and not present before edit]
                        }
                    }

                    // If this was a new item (with the temporary negative URI), update its ID with the value assigned by the server
                    if (this.item_data.uri < 0)
                        this.current_data.uri = server_payload;

                    // Inform the ancestral root component of the new state of the data
                    console.log("Records component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the accepted baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);  // Clone

                    this.editing_mode = false;      // Exit the editing mode
                }
                else  {             // Server reported FAILURE
                    this.status = `FAILED edit`;
                    this.error_indicator = true;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.waiting_mode = false;      // Make a note that the asynchronous operation has come to an end

            }, // finish_save


            cancel_edit()
            // Invoked when the user cancels the edit-in-progress, or when the save operation fails
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.uri < 0) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Records component sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }

                this.editing_mode = false;      // Exit the editing mode
            } // cancel_edit

        }  // METHODS

    }
); // end component