/*  Vue component to display and edit Content Items of type "sl" (Site Links, aka Bookmarks)
    TODO: rename 'vue-plugin-site-link'
 */

Vue.component('vue-plugin-sl',
    {
        props: ['item_fields', 'item_metadata',
                'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_fields:    An object with the editable properties of this Site Link item.
                                EXAMPLE: {url: "http://example.com",
                                          name:"test",
                                          comments: "my test site",
                                          rating: 4.5,
                                          read: "yes",
                                          date: "4/2026"}

            item_metadata:  An object with the metadata of this Site Link item.
                                For a newly-created Content Item, not yet registered with the server,
                                the value of `entity_id` will be a negative number (unique on the page),
                                and there will be the additional keys `insert_after_uri` and `insert_after_class`
                                EXAMPLE of existing Site Link item:
                                        {"class_name":"Site Link",
                                        "pos":0,
                                        "schema_code":"timer",
                                        "entity_id":"8809",
                                        schema_code: "sl"
                                        }

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The entity ID of the Category page where this record is displayed (used when creating new records)
            index:          The zero-based position of this Site Link item on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names, in Schema order.
                                EXAMPLE: ["url","name","date","comments","rating","read"]
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <table class='sl-main'>

                <tr v-if = "!editing_mode" @dblclick="enter_editing_mode">
                    <td rowspan=2 class="no-borders" style="width: 5%">
                        <img src="/BA/pages/static/graphics/bookmark_32_60162.png">
                    </td>

                    <td v-html="render_cell(current_data.url)" style="width: 25%"></td>
                    <td class="name">{{current_data.name}}</td>
                    <td class="small">{{current_data.read}}</td>
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
                    <td class="small">{{current_data.date}}</td>
                    <td class="comments">{{current_data.comments}}</td>
                    <td><span v-show="current_data.rating">{{current_data.rating}}</span><span v-show="current_data.rating" class="star-yellow">&#9733;</span>
                    </td>
                </tr>
                <tr v-else @dblclick="enter_editing_mode">
                    <td><span class="hint">date</span><br><input type="text" size="6" v-model="current_data.date"></td>
                    <td>
                        <span class="hint">comments</span><br>
                        <textarea rows="4" cols="60"  v-model="current_data.comments">
                        </textarea>
                    </td>
                    <td><span class="hint">rating</span><br>
                        <select v-model="current_data.rating">
                            <option disabled value='-1'>[&#9733;]</option>
                            <option value=5>5</option>
                            <option value=4.5>4.5</option>
                            <option value=4>4</option>
                            <option value=3.5>3.5</option>
                            <option value=3 selected>3</option>
                            <option value=2.5>2.5</option>
                            <option value=2>2</option>
                            <option value=1.5>1.5</option>
                            <option value=1>1</option>
                            <option value=0.5>0.5</option>
                            <option value=0>0</option>
                        </select>
                    </td>
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
                editing_mode: (this.item_metadata.entity_id < 0  ? true : false), // Negative entity_id means "new Item"

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                //      Note: for new Content Items, it only contains
                //              `class_name`, `schema_code`, `entity_id`, `insert_after_uri`, PLUS anything dynamically added by v-model during data entry
                //            For existing Content Items, it contains
                //              `class_name`, `schema_code`, `entity_id`, `pos`, and Content-specific fields
                current_data:   Object.assign({}, this.item_fields),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                original_data:  Object.assign({}, this.item_fields),    // Clone from the original data passed to this component

                // Private copy of the metadata
                current_metadata:   Object.assign({}, this.item_metadata),

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {

            set_name()
            /*  Invoked whenever a change of the URL field is detected while in editing mode
                (when the user clicks away from that field);
                if no name field is already present,
                it attempts to retrieve the webpage title of the URL just entered by the user,
                and it sets the "name" field (on the editing form) to it
             */
            {
                const url = this.current_data.url;
                console.log(`Detected change in the URL ; new value: ${url}`);

                const current_name = this.current_data.name;

                if (current_name === null || current_name === undefined
                        ||  (typeof current_name === 'string' && current_name.trim() === '') )
                {
                    // We'll retrieve a name only if the name field is null, undefined or a string of blanks
                    Vue.set(this.current_data, "name", "[Fetching the page title...]"); // Temporary name assignment
                    this.get_webpage_title(url);    // Query the server to find out the page title, and sets the "name" field to it
                }
                else
                    console.log(`set_name(): we already have a name for this webpage; no action taken`);
            },



            render_cell(cell_data)
            /*  If the passed argument is a string that appears to be a URL,
                convert it into a string with HTML code for a hyperlink that opens in a new window;
                if the URL is very long, show it in abbreviated form in the hyperlink text.
                In all other cases, just return the argument.

                Note: this function is also found in records.js, single_record.js and site_links.js
             */
            {
                const max_url_len = 35;     // NOT counting the protocol part (such as "https://")

                if (typeof cell_data != "string")
                     return cell_data;

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



            enter_editing_mode()
            // Switch to the editing mode of this Vue component
            {
                console.log(`In enter_editing_mode()`);

                // Clear any old value
                this.waiting = false;
                this.error = false;
                this.status_message = "";

                this.editing_mode = true;       // Enter editing mode
            },


            edit_content_item()
            /*  Handler for the "edit_content_item" Event received from the child component "vue-controls"
                (which is generated there when clicking on the Edit button)
             */
            {
                console.log(`'Site Links' component received Event to edit its contents`);
                //this.editing_mode = true;
                this.enter_editing_mode();

                //this.display_all_fields();      // Consult the schema
            },


            /**
             * Invoked by clicking on the "CANCEL" link (only visible in editing mode)
             */
            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_metadata.entity_id < 0) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Records component sending `cancel-edit` SIGNAL to its parent");
                    this.$emit('cancel-edit');
                }
                else
                    this.editing_mode = false;      // Exit the editing mode

            },  // cancel_edit




            /*
                ---  SERVER CALLS  ---
             */

            get_webpage_title(url)
            /*  Asynchronously query the server to find out the title of the webpage identified by the given URL,
                and, upon fetching the result, set the data field this.current_data.name to it.
                (Note: letting the server handle this, to avoid running afoul of CORS.)
             */
            {
                console.log(`Attempting to retrieve title of webpage: ${url}`);

                // Send the request to the server, using a GET
                const url_server_api = `/BA/api/fetch-remote-title?url=${url}`;

                console.log(`About to contact the server at ${url_server_api}`);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "GET",
                             callback_fn: this.finish_get_webpage_title
                            });
            },

            finish_get_webpage_title(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of get_webpage_title() upon getting a response from the server
            {
                console.log("Finalizing the get_webpage_title() operation...");

                var new_name;

                if (success)  {     // Server reported SUCCESS
                    new_name = server_payload;
                    // Note: if the user has already saved the record by the time this fetch terminates,
                    //       then the modified field won't get saved in the database, nor shown in the UI
                }
                else  {             // Server reported FAILURE
                    new_name = "Unable to extract webpage title";
                }

                Vue.set(this.current_data, "name", new_name);
            },


            save()
            // Conclude an EDIT operation.  TODO: maybe save/cancel should be a sub-component shared among various plugins?
            {
                // Enforce required field
                if (! 'url' in this.current_data) {
                    post_obj.text = this.current_data.text;
                    alert("Cannot save an empty URL. If you want to get rid of this Site Link (bookmark), delete it instead");
                    return;
                }

                // Start the body of the POST to send to the server
                let post_obj = {class_name: this.current_metadata.class_name,

                                url:        this.current_data.url,
                                name:       this.current_data.name,
                                date:       this.current_data.date,
                                comments:   this.current_data.comments,
                                rating:     this.current_data.rating,
                                read:       this.current_data.read
                               };


                if (this.current_metadata.entity_id < 0)  {     // Negative entity_id is a convention indicating a new Content Item to create
                    // Needed for NEW Content Items
                    post_obj.category_id = this.category_id;
                    post_obj.insert_after_uri = this.current_metadata.insert_after_uri;       // entity_id of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                    post_obj.insert_after_class = this.current_metadata.insert_after_class;   // Class of Content Item to insert after

                    url_server_api = `/BA/api/add_item_to_category`;   // URL to communicate with the server's endpoint
                }
                else  {     // Update an EXISTING Site Link
                    post_obj.entity_id = this.current_metadata.entity_id;

                    url_server_api = `/BA/api/update_content_item`;   // URL to communicate with the server's endpoint
                }


                console.log(`In 'vue-plugin-sl', save().  About to contact the server at ${url_server_api}.  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server, using POST data
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
                             callback_fn: this.finish_save});

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            }, // save


            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned entity_id

                success:        boolean indicating whether the server call succeeded
                server_payload: whatever the server returned (stripped of information about the success of the operation)
                error_message:  a string only applicable in case of failure
             */
            {
                console.log("Finalizing the SiteLink save() operation...");

                if (success)  {     // Server reported SUCCESS
                    this.status_message = `Successful edit`;

                    // If this was a new item (with the temporary negative entity_id),
                    // update its entity_id with the value assigned by the server
                    if (this.current_metadata.entity_id < 0)  {
                        this.current_metadata.entity_id = server_payload;      // Update with the value assigned by the server
                        delete this.current_metadata.insert_after_uri;         // No longer needed
                        delete this.current_metadata.insert_after_class;       // No longer needed
                    }

                    // Inform the parent component of the new state of the data; pass clones of the relevant objects
                    const signal_data = {
                        item_fields:   Object.assign({}, this.current_data),
                        item_metadata: Object.assign({}, this.current_metadata)
                    };
                    console.log("'Site Links' component sending `updated-item` SIGNAL to its parent with the following data:");
                    console.log(structuredClone(signal_data));     // Log a frozen deep snapshot of the object
                    this.$emit('updated-item', signal_data);

                    // Synchronize the baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED edit`;
                    this.cancel_edit();     // Restore the data to how it was prior to the failed changes
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
                this.editing_mode = false;      // Exit the editing mode

            } // finish_save

        }  // METHODS

    }
); // end component