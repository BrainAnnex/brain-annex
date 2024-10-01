// TODO: the special handling for "closing" Headers
// TODO: maybe Headers should be regarded as "Page Elements", rather than "Content Items"

/*  Vue component to display and edit Content Items of type "h" (Headers)
 */

Vue.component('vue-plugin-h',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      An object with the relevant data about this Header item;
                                if the "uri" attribute is negative,
                                it means that it's a newly-created header, not yet registered with the server
                                EXAMPLE: {"uri":"52","pos":10,"schema_code":"h","text":"MY NEW SECTION","class_name":"Header"}
                                TODO: take "pos" and "class_name" out of item_data !

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this Header is displayed (used when creating new records)
            index:          The zero-based position of this Header item on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <div class='h-text'  @dblclick="enter_editing_mode">
                    <span v-if="!editing_mode" class='h-text'>{{ current_data.text }}</span>
                    <span v-else><input type="text" size="40" v-model="current_data.text">
                        <button @click="save">SAVE</button>
                        <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                    </span>
                    <span v-if="waiting" style="margin-left:15px">saving...</span>
                    <br>
                </div>

                <span v-if="status_message!='' && !editing_mode">Status : {{status_message}}</span>


                <!--  Start of STANDARD CONTROLS (inline elements that can be extended with extra controls),
                      EXCEPT for the "tag" control, which is omitted.

                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component,
                      but some get intercepted and handled here, namely:

                              v-on:edit-content-item

                      Optional EXTRA controls may be placed before (will appear to the left)
                      or after (will appear to the right) of the standard controls
                -->
                    <vue-controls v-bind:edit_mode="edit_mode" v-bind:index="index"  v-bind:item_count="item_count"
                                  v-bind:controls_to_hide="['tag']"
                                  v-on="$listeners"
                                  v-on:edit-content-item="edit_content_item">
                    </vue-controls>
                <!--  End of STANDARD CONTROLS -->

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                editing_mode: (this.item_data.uri < 0 ? true : false),    // Negative URI means "new Item" (automatically placed in editing mode)

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------   METHODS   ------------------------------
        methods: {

            enter_editing_mode()
            // Switch to the editing mode of this Vue component
            {
                console.log(`In enter_editing_mode()`);

                // Clear any old value
                this.waiting = false;
                this.error = false;
                this.status_message = "";

                this.editing_mode = true;          // Enter editing mode
            },


            edit_content_item()
            /*  Handler for the "edit_content_item" Event received from the child component "vue-controls"
                (which is generated there when clicking on the Edit button)
             */
            {
                console.log(`'Headers' component received Event to edit its contents`);
                this.enter_editing_mode();
            },



            save()
            {
                // Start the body of the POST to send to the server
                var post_obj = {class_name: this.item_data.class_name};

                if (this.item_data.uri < 0)  {     // Negative URI is a convention indicating a new Content Item to create,
                     // Needed for NEW Content Items
                     post_obj.category_id = this.category_id;
                     post_obj.insert_after = this.item_data.insert_after;   // URI of Content Item to insert after, or keyword "TOP" or "BOTTOM"

                     url_server_api = `/BA/api/add_item_to_category`;       // URL to communicate with the server's endpoint
                }
                else {   // Update an EXISTING header
                    post_obj.uri = this.item_data.uri;

                    url_server_api = `/BA/api/update_content_item`;        // URL to communicate with the server's endpoint
                }

                // Go over each field.  TODO: generalize
                if ('text' in this.current_data)
                    post_obj.text = this.current_data.text;
                else  {
                    alert("Cannot save an empty header text. If you want to get rid of this header, delete it instead");
                    return;
                }

                console.log(`In 'vue-plugin-h'.  About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_NEW(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
                             callback_fn: this.finish_save
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
             }, // save


            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned URI
             */
            {
                console.log("Finalizing the Header save() operation...");
                if (success)  {     // Server reported SUCCESS
                    //console.log("    server call was successful");
                    this.status_message = `Successful edit`;

                    // If this was a new item (with the temporary negative URI), update its URI with the value assigned by the server
                    if (this.item_data.uri < 0)
                        this.current_data.uri = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Headers component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the baseline data to the finalized current data
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.status_message = `FAILED edit`;
                    this.error = true;
                    this.cancel_edit();         // Restore the data to how it was prior to the failed changes. TODO: maybe leave in edit mode?
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end
                this.editing_mode = false;      // Exit the editing mode

            }, // finish_save


            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.uri < 0) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Headers sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }
                else
                    this.editing_mode = false;      // Exit the editing mode

            } // cancel_edit

        }  // METHODS

    }
); // end component