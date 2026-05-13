/*  Vue component to display and edit Content Items for "flash cards"
 */

Vue.component('vue-plugin-f',
    {
        props: ['item_fields', 'item_metadata',
                'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_fields:    An object with the editable properties of this Flash-Card item.
                                EXAMPLE: {source_label: "French Vocabulary",
                                          sideA_field: "French",
                                          sideB_field: "English"}

            item_metadata:  An object with the metadata of this Site Link item.
                                For a newly-created Content Item, not yet registered with the server,
                                the value of `entity_id` will be a negative number (unique on the page),
                                and there will be the additional keys `insert_after_uri` and `insert_after_class`
                                EXAMPLE of existing Site Link item:
                                        {class_name":"Flash Card",
                                         pos:0,
                                         schema_code:"f",
                                         entity_id:"8809"
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


                <!----------  Display when in NORMAL (non-editing) mode  ---------->
                <div v-if="(!editing_mode) && (side_shown=='A')" class='flash-card'
                    @click="flip_card()"
                >
                    <div class="card-header">FLASH CARD</div>
                    <br><br><br>
                    French:
                    <p>
                        {{cards[deck_position][["A"]]}}
                    </p>
                    <br><br><br><br><br>
                    <span class="instructions">Click anywhere to FLIP the card</span>
                </div>


                <div v-if="(!editing_mode) && (side_shown=='B')" class='flash-card'
                    @click="advance_card()"
                >
                    <div class="card-header">ANSWER</div>
                    <br><br><br>
                    English:
                    <p>
                        {{cards[deck_position][["B"]]}}
                    </p>
                    <br><br><br><br><br>
                    <span class="instructions">Click anywhere to ADVANCE to the next card</span>
                </div>



                <!----------  Display when in EDITING MODE  ---------->
                <div v-if="editing_mode">

                    EDITING MODE TBA

                </div>



                <br>

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

                side_shown: "A",        // Either "A" or "B"

                deck_position: 0,

                cards: [ {A: "Chat", B: "Cat"},  {A: "Mot", B: "Word"}],

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {

            flip_card()
            {
                this.side_shown = "B";
            },

            advance_card()
            {
                this.side_shown = "A";

                if (this.deck_position == this.cards.length - 1)
                    this.deck_position = 0;
                else
                    this.deck_position += 1;
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

                    var url_server_api = `/BA/api/add_item_to_category`;   // URL to communicate with the server's endpoint
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