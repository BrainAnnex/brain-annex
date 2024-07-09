/*  Vue component to display and edit Content Items of type "sl" (Site Links, aka Bookmarks)
 */

Vue.component('vue-plugin-sl',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*
            item_data:      An object with the relevant data about this Site Link item;
                                if the "uri" attribute is negative,
                                it means that it's a newly-created header, not yet registered with the server
            edit_mode:  A boolean indicating whether in editing mode
            category_id:    The ID of the Category page where this record is displayed (used when creating new records)
            index:          The zero-based position of this Site Link item on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names, in Schema order.
                                EXAMPLE: ["url","name","date","comments","rating","read"]

            EXAMPLE: {"item_data": {class_name:"Site Link",
                                            uri: 4912, position: 20,  schema_code: "sl"

                                            [whatever other fields were set in this item; for example]
                                            url:"http://example.com",
                                            name:"test"
                                           },
                              "edit_mode": false, "category_id": 123,
                              "index": 2, "item_count": 10,
                              "schema_data": ["url","name","date","comments","rating","read"]
                             }

         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <table class='sl-main'>

                <tr v-if = "!editing_mode" @dblclick="enter_editing_mode">
                    <td rowspan=2 class="no-borders">
                        <img src="/BA/pages/static/graphics/bookmark_32_60162.png">
                    </td>

                    <td v-html="render_cell(item_data.url)"></td>
                    <td class="name">{{item_data.name}}</td>
                    <td class="small">{{item_data.read}}</td>
                </tr>
                <tr v-else @dblclick="enter_editing_mode">
                    <td>
                        <span class="hint">url</span><br>
                        <textarea rows="4" cols="20"  v-model="current_data.url"  @change="set_name">
                        </textarea>
                    </td>
                    <td>
                        <span class="hint">name</span><br>
                        <textarea rows="4" cols="60"  v-model="current_data.name">
                        </textarea>
                    </td>
                    <td>
                        <span class="hint">read?</span><br><input type="text" size="6" v-model="current_data.read">
                    </td>
                </tr>


                <tr v-if = "!editing_mode" @dblclick="enter_editing_mode">
                    <td class="small">{{item_data.date}}</td>
                    <td class="comments">{{item_data.comments}}</td>
                    <td>{{item_data.rating}}</td>
                </tr>
                <tr v-else @dblclick="enter_editing_mode">
                    <td><span class="hint">date</span><br><input type="text" size="6" v-model="current_data.date"></td>
                    <td>
                        <span class="hint">comments</span><br>
                        <textarea rows="4" cols="60"  v-model="current_data.comments">
                        </textarea>
                    </td>
                    <td><span class="hint">rating</span><br><input type="text" size="1" v-model="current_data.rating"></td>
                </tr>

            </table>


            <!-- Area below the table, with SAVE/Cancel controls (if in editing mode) -->
            <p v-if="editing_mode" style="border-left:1px solid #DDD; padding-left:5px">
                <button @click="save()">SAVE</button>
                <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                <span v-if="waiting" style="margin-left:15px">saving...</span>
            </p>

            <span v-if="status_message!='' && !editing_mode">Status : {{status_message}}</span>

            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item   (which is not listened to by the root component)
            -->
            <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item">
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
                        current_data:   Object with the values bound to the editing fields,
                                        initially cloned from (part of) the "prop" data;
                                        it'll change in the course of the edit-in-progress

                        original_data:  Object with pre-edit data, initially cloned from (part of) the "prop" data;
                                        used to restore the data in case of an edit Cancel or failed save

                    EXAMPLE of item_data (a PROP, not a variable of this component!):
                        {
                            class_name:"Site Link",
                            uri: 4912,

                            [whatever other fields were set in this item; for example]
                            url:"http://example.com",
                            name:"some website",

                            position: 20,
                            schema_code: "sl"
                       }

                    EXAMPLE of current_data and original_data:
                        {
                            url:"http://example.com",
                            name:"some website"
                        }

                    Note that the objects may lack some of the fields specified by the Schema
                 */


                // Note: negative uri means "new Item"
                current_data: (this.item_data.uri < 0  ? this.prepare_blank_record() : this.clone_and_standardize(this.item_data)),
                original_data: (this.item_data.uri < 0  ? this.prepare_blank_record() : this.clone_and_standardize(this.item_data)),

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {

            set_name()
            /* Invoked whenever a change of the URL field is detected while in editing mode
                (upon the user clicking away from that field);
                it attempts to retrieve the webpage title of the URL just entered by the user,
                and it sets the "name" field (on the editing form) to it
             */
            {
                const url = this.current_data.url;
                console.log(`Detected change in the URL ; new value: ${url}`);

                this.current_data.name = "[Fetching the page title...]";
                this.get_webpage_title(url);
            },


            determine_headers()
            /* Note: this is quite similar to the canonical_field_list() method in the
                     Vue root component.  TODO: eventually merge
                     TODO: maybe un-necessary now that we have the "schema_data" prop
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



            render_cell(cell_data)
            /*  If the passed string appears to be a URL, convert it into a hyperlink, opening in a new window;
                and if the URL is very long, show it in abbreviated form
             */
            {
                const max_url_len = 35;     // NOT counting the protocol part (such as "https://")

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
            },


            prepare_blank_record()
            /*  Meant to be invoked upon entering Editing mode with a new record
             */
            {
                console.log("In prepare_blank_record()");

                let properties = this.schema_data;
                console.log("    properties looked up: " , properties);
                // EXAMPLE:  ['url', 'name', 'date', 'comments', 'rating', 'read']

                // Create a new  object based on the schema data
                new_blank_record = {};    // Empty object

                for (let i = 0; i < properties.length; i++) {
                    field_name = properties[i];

                    console.log("    Adding field from Schema: ", field_name);
                    new_blank_record[field_name] = "";
                }

                return new_blank_record;
            },


            display_all_fields()
            /*  Meant to be invoked upon entering Editing mode:
                present all the fields declared in the Schema (including any hidden before because it lacked data.)

                Modify the "current_data" property, to also include any fields in the Schema.
                Perform this operation in a matter than will be detected by Vue
             */
            {
                console.log("In show_all_fields()");

                let properties = this.schema_data;
                console.log("    properties looked up: " , properties);
                // EXAMPLE:  ['url', 'name', 'date', 'comments', 'rating', 'read']

                // Create a new cloned object based on the current record data
                // (that's because if one just alters existing objects, Vue doesn't detect the change!)
                new_current_data = Object.assign({}, this.current_data);    // Clone the current_data object

                for (let i = 0; i < properties.length; i++) {
                    field_name = properties[i];

                    /* Only add fields not already present
                     */
                    if (!(field_name in this.current_data))  {
                        console.log("    Adding missing field: ", field_name);
                        new_current_data[field_name] = "";
                    }
                }

                this.current_data = new_current_data;   // This assignment will get Vue's attention!
            },


            clone_and_standardize(obj)
            // Clone first; then remove some keys that shouldn't get shown nor edited
            {
                clone_obj = Object.assign({}, obj);     // Clone the object

                // Scrub some data, so that it won't show up in the tabular format
                delete clone_obj.uri;
                delete clone_obj.schema_code;
                delete clone_obj.class_name;
                delete clone_obj.insert_after;
                delete clone_obj.pos;           // TODO: this might be getting phased out

                return clone_obj;
            },



            enter_editing_mode()
            // Switch to the editing mode of this Vue component
            {
                console.log(`In enter_editing_mode()`);

                //this.current_data = this.clone_and_standardize(this.item_data);   // Scrub some data, so that it won't show up in the tabular format
                //this.original_data = this.clone_and_standardize(this.item_data);
                // NOTE: clone_and_standardize() gets called twice

                // Clear any old value
                this.waiting = false;
                this.error = false;
                this.status_message = "";

                this.editing_mode = true;       // Enter editing mode

                this.display_all_fields();      // This will set the "current_data" property
                this.original_data = this.clone_and_standardize(this.item_data);
            },


            edit_content_item()
            /*  Handler for the "edit_content_item" Event received from the child component "vue-controls"
                (which is generated there when clicking on the Edit button)
             */
            {
                console.log(`'Site Links' component received Event to edit its contents`);
                this.editing_mode = true;

                this.display_all_fields();      // Consult the schema
            },



            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.uri == -1) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Records component sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }

                this.editing_mode = false;      // Exit the editing mode
            },




            /*
                SERVER CALLS
             */

            get_webpage_title(url)
            /*  Query the server to find out the title of the webpage identified by the given URL.
                (Note: letting the server handle this, to avoid running afoul of CORS.)
             */
            {
                console.log(`Retrieving title of webpage ${url}`);

                let url_server = `/BA/api/fetch-remote-title?url=${url}`;
                console.log(`About to contact the server at ${url_server}`);

                ServerCommunication.contact_server(url_server,  {callback_fn: this.finish_get_webpage_title});
            },

            finish_get_webpage_title(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of get_webpage_title() upon getting a response from the server
            {
                console.log("Finalizing the get_webpage_title operation...");

                if (success)  {     // Server reported SUCCESS
                    this.current_data.name = server_payload;
                }
                else  {             // Server reported FAILURE
                    this.current_data.name = "Unable to extract webpage title";
                }
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
                            "uri": 61,
                            "schema_code": "r",
                            "insert_after": 123,
                            "class_name": "German Vocabulary",
                            "pos": 0
                        }
                */
                console.log(`In 'vue-plugin-sl', save()`);

                let post_obj = {schema_code: this.item_data.schema_code};

                if (this.item_data.uri < 0)  {     // Negative uri is a convention indicating a new Content Item to create
                    // Needed for NEW Content Items
                    post_obj["category_id"] = this.category_id;
                    post_obj["class_name"] = this.item_data.class_name;
                    post_obj["insert_after"] = this.item_data.insert_after;   // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data)  {
                        // Only pass non-blank values
                        if (this.current_data[key] != "")
                            post_obj[key] = this.current_data[key];
                    }
                    // EXAMPLE of post_obj for a NEW record:
                    //          "schema_code=r&category_id=12&class_name=German%20Vocabulary&insert_after=123&German=Liebe"

                    url_server_api = `/BA/api/add_item_to_category`;   // URL to communicate with the server's endpoint
                }
                else  {
                    // Update an EXISTING record
                    post_obj["uri"] = this.item_data.uri;

                    // Go over each key (field name); note that keys that aren't field names were previously eliminated
                    for (key in this.current_data) {
                        if ( (this.current_data[key] != "")  ||  (key in this.original_data) )
                            // Non-blanks always lead to updates; blanks only if the field was originally present
                            post_obj[key] = this.current_data[key];
                    }
                    // EXAMPLE of post_obj for an EXISTING record: "schema_code=r&uri=62&English=Love&German=Liebe"

                    url_server_api = `/BA/api/update`;   // URL to communicate with the server's endpoint
                }

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

                console.log(`About to contact the server at ${url_server_api}.  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server, using POST data
                ServerCommunication.contact_server(url_server_api,
                            {post_obj: post_obj,
                             callback_fn: this.finish_save});
            }, // save


            finish_save(success, server_payload, error_message, custom_data)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID

                success:        boolean indicating whether the server call succeeded
                server_payload: whatever the server returned (stripped of information about the success of the operation)
                error_message:  a string only applicable in case of failure
                custom_data:    whatever JavaScript structure, if any, was passed by the contact_server() call
             */
            {
                console.log("Finalizing the SiteLink saving operation...");

                if (success)  {     // Server reported SUCCESS
                    this.status_message = `Successful edit`;

                    // Eliminate some un-needed fields from the display
                    for (field in this.current_data)  {
                        if (this.current_data[field] != "")
                            console.log("Field still needed because non-empty: ", field);
                        else if (field in this.original_data)  {
                            console.log("Field blank but was in original data [deleted anyway]: ", field);
                            delete this.current_data[field];     // Zap b/c blank
                        }
                        else {
                            console.log("Eliminating field no longer in need to display: ", field);
                            delete this.current_data[field];    // Zap b/c blank [NO LONGER DONE:, and not present before edit]
                        }
                    }

                    // If this was a new item (with the temporary negative ID), update its ID with the value assigned by the server
                    if (this.item_data.uri < 0)
                        this.current_data.uri = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Site Links component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the accepted baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);  // Clone

                    this.editing_mode = false;      // Exit the editing mode
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED edit`;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end

            } // finish_save

        }  // METHODS

    }
); // end component