/*  Vue component to display and edit Content Items for "flash cards"
 */

Vue.component('vue-plugin-f',
    {
        props: ['item_fields', 'item_metadata',
                'edit_mode', 'category_id', 'schema_data', 'data_for_controls'],
        /*  item_fields:    An object with the editable properties of this Flash-Card item.
                                EXAMPLE: {source_label: "French Vocabulary",
                                          sideA_field: "French",
                                          sideB_field: "English",
                                          reverse_odds: 0.5
                                          }
                                `reverse_odds` is the probability of temporarily inverting the given A/B sides,
                                        on any single showing, from the designated order.
                                        Use 0 to remain consistent, up to 0.5 for complete randomness

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

            edit_mode:      A boolean indicating whether the page containing this element is in editing mode
                                (to pass to the controls)  TODO: rename to "page_edit_mode"
            category_id:    The entity ID of the Category page where this record is displayed (used when creating new records)
            index:          The zero-based position of this Site Link item on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names, in Schema order.
                                EXAMPLE: ["url","name","date","comments","rating","read"]
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->


                <!----------  Display when in NORMAL (non-editing) mode, for side A  ---------->
                <!-- SIDE A of the card -->
                <div v-if="(!editing_mode) && (side_shown=='A')" class='flash-card'
                    @click="flip_card()"
                >
                    <div class="card-header">
                        FLASH CARD<br>
                        <span class="card-name">{{current_data.source_label}}</span>
                    </div>

                    <br><br>
                    <span class="field-name">
                        {{current_data.sideA_field}}:
                    </span>
                    <p>
                        {{cards[deck_position][current_data.sideA_field]}}
                    </p>
                    <br><br><br><br><br><br><br>
                    <span class="instructions">{{deck_position+1}} out of {{number_cards}}.  Click anywhere to FLIP the card</span>
                </div>


                <!----------  Display when in NORMAL (non-editing) mode, for side B  ---------->
                <!-- SIDE B of the card -->
                <div v-if="(!editing_mode) && (side_shown=='B')" class='flash-card'
                    @click="advance_card()"
                >
                    <div class="card-header-answer">ANSWER</div>
                    <br><br>

                    <span class="field-name">{{current_data.sideA_field}}:</span>
                    <p>
                        {{cards[deck_position][current_data.sideA_field]}}

                        <button @click.stop="copy_to_clipboard(0, cards[deck_position][current_data.sideA_field])">
                            {{ copied[0] ? "Copied!" : "Copy" }}
                        </button>
                    </p>



                    <br><hr>
                    <span class="field-name">{{current_data.sideB_field}}:</span>
                    <p>
                        {{cards[deck_position][current_data.sideB_field]}}

                        <button @click.stop="copy_to_clipboard(1, cards[deck_position][current_data.sideB_field])">
                            {{ copied[1] ? "Copied!" : "Copy" }}
                        </button>
                    </p>

                    <p v-for='(val, key) in cards[deck_position]'>
                        <span v-if="(key != current_data.sideA_field)
                                        && (key != current_data.sideB_field)
                                        && (key[0] != '_')
                                        && (key != 'entity_id')"
                              class="extra-fields"
                        >
                            {{key}} : {{val}}
                        </span>
                    </p>

                    <br>
                    <span class="instructions">Click anywhere to ADVANCE to the next card</span>
                </div>



                <!----------  Display when in EDITING MODE  ---------->
                <div v-show="editing_mode" class='flash-card'>

                    <br>

                    <span class="label">Source Label</span> <input v-model="current_data.source_label" size="40">
                    <br><br>

                    <span class="label">Name of 'side A' field</span> <input v-model="current_data.sideA_field" size="40">
                    <br><br>

                    <span class="label">Name of 'side B' field</span> <input v-model="current_data.sideB_field" size="40">
                    <br><br>

                    <span class="label">Odds of reversing sides</span> <input v-model="current_data.reverse_odds" size="3">
                    <br><span class="instructions">Use 0 to remain consistent, up to 0.5 for complete randomness</span>
                    <br><br>

                    <!-- CONTROLS to edit the document fields -->
                    <p style="text-align: right">
                        <span @click="cancel_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                        <button @click="save_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                        <br>
                        <span v-if="waiting" class="waiting">Performing the update</span>
                    </p>

                    <!-- STATUS line -->
                    <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>

                </div>



                <br>

                <!--  Start of STANDARD CONTROLS (a <SPAN> element that can be extended with extra controls).
                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component,
                      but some get intercepted and handled here, namely:

                              v-on:edit-content-item
                -->

                    <!-- OPTIONAL MORE CONTROLS to the LEFT of the standard ones would go here -->

                    <vue-controls v-bind:edit_mode="edit_mode"  v-bind:data_for_controls="data_for_controls"
                                  v-on="$listeners"
                                  v-on:edit-content-item="edit_content_item">
                    >
                    </vue-controls>

                    <!-- OPTIONAL MORE CONTROLS to the RIGHT of the standard ones would go here -->

                <!--  End of STANDARD CONTROLS -->

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                editing_mode: (this.item_metadata.entity_id < 0  ? true : false), // Negative entity_id means "new Item"

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data:   Object.assign({}, this.item_fields),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                original_data:  Object.assign({}, this.item_fields),    // Clone from the original data passed to this component

                /* Private copy of the metadata
                        For new Content Items, it only contains:
                            `class_name`, `schema_code`, `entity_id` (a negative integer), `insert_after_uri`
                        For existing Content Items, it contains:
                             `class_name`, `schema_code`, `entity_id`, `pos`
                */
                current_metadata:   Object.assign({}, this.item_metadata),

                side_shown: "A",        // Either "A" (Question side) or "B" (Answer side)

                cards: [ {French: "Chat", English: "Cat"},  {French: "Mot", English: "Word", Notes: "some note"}],
                                        // Extra fields allowed - and will be shown with the answer card

                deck_position: 0,       // Index in the randomized deck
                number_cards: 2,        // Size of the deck

                copied: [false, false], // Array of "copied" status, for each of the buttons offering that function

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------------   HOOKS   ------------------------------------

        /**
         * the "mounted" Vue hook is invoked later in the process of launching this component.
         */
        mounted()
        {
            console.log(`The flash_card component has been mounted`);

            if (this.item_metadata.entity_id < 0)  {  // A negative entity_id is a convention to indicate a just-created Flash Card
                //this.edit_recordset();
                return;
            }

            this.fetch_card_data();      // Fetch from the server all the cards' data
        },



        // ------------------------------------   METHODS   ------------------------------------
        methods: {

            /**
             * Show the side with all the info (the "answer")
             */
            flip_card()
            {
                this.side_shown = "B";
            },


            /**
             * Move onto the next card in the deck.  If at the end of it, cycle back to the beginning
             */
            advance_card()
            {
                this.side_shown = "A";

                if (this.deck_position == this.cards.length - 1)
                    this.deck_position = 0;
                else
                    this.deck_position += 1;

                if (Math.random() < this.current_data.reverse_odds) {   // Flip the sideA/B order, with some probability
                    console.log(`In advance_card(): temporarily flipping the sides for this round`);
                    //[this.current_data.sideA_field, this.current_data.sideB_field] = [this.current_data.sideB_field, this.current_data.sideA_field];
                    [this.current_data.sideA_field, this.current_data.sideB_field] = [this.item_fields.sideB_field, this.item_fields.sideA_field];
                }
                else    // Use the normal order
                    [this.current_data.sideA_field, this.current_data.sideB_field] = [this.item_fields.sideA_field, this.item_fields.sideB_field];
            },



            /**
             * Enable the flash_card edit mode.
             * Handler for the "edit-content-item" SIGNAL received from the child component "vue-controls"
             * (which is generated there when clicking on the Edit button)
             */
            edit_content_item()
            {
                console.log(`'flash_card' component received Event to edit its contents`);
                this.enter_editing_mode();
            },


            /**
             * Switch to the editing mode of this Vue component
             */
            enter_editing_mode()
            //
            {
                console.log(`In enter_editing_mode()`);

                // Clear any old value.  TODO: verify that this is really necessary
                this.waiting = false;
                this.error = false;
                this.status_message = "";

                this.editing_mode = true;       // Enter editing mode
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



            /**
             * Shuffle the deck.  Return an in-place modification of the array containing the deck data
             */
            reshuffle_deck(arr)
            {
                this.deck_position = 0;
                return this.shuffle_array(arr);
            },


            /**
             * Randomly re-arrange in-place an array using the Fisher–Yates algorithm (also called the Knuth shuffle)
             */
            shuffle_array(arr)
            {
                for (let i = arr.length - 1; i > 0; i--) {

                    // Generate a random integer from 0 to i
                    const j = Math.floor(Math.random() * (i + 1));

                    // Swap the i and j-the array elements
                    [arr[i], arr[j]] = [arr[j], arr[i]];
                }

                return arr;
            },



            /**
             * Copy the given value to the clipboard.
             * The index refers to multiple buttons offering the "copy to clipboard" function
             */
            async copy_to_clipboard(index, text)
            {
                try {
                    await navigator.clipboard.writeText(text);
                    console.log("Copied:", text);

                    // The following lines are used to flash a "Copied!" message to the user
                    Vue.set(this.copied, index, true);
                    setTimeout(() => {
                        Vue.set(this.copied, index, false);
                    }, 1500);   // In milliseconds
                }
                catch (err) {
                    console.error("Clipboard copy failed:", err);
                }
            },




            /*
                 ---------------------  SERVER CALLS  ---------------------
             */


            /**
             * Obtain the data for all the flash cards
             */
            fetch_card_data()
            {
                console.log(`In fetch_card_data()`);

                // Send the request to the server, using a GET
                const url_server_api = "/BA/api/get-filtered";

                const get_obj = {label: this.current_data.source_label,
                                 limit: 1000};

                console.log(`About to contact the server at ${url_server_api} .  GET object:`);
                console.log(get_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {   method: "GET",
                                data_obj: get_obj,
                                json_encode_send: true,
                                callback_fn: this.finish_fetch_card_data
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation

            },  // fetch_card_data


            /** Callback function to wrap up the action of fetch_card_data() upon getting a response from the server.
             *
             * @param {bool} success - Boolean indicating whether the server call succeeded
             * @param server_payload - Whatever the server returned (stripped of information about the success of the operation)
             * @param {string} error_message - Only applicable in case of failure
             * @param custom_data            - NOT USED
             */
            finish_fetch_card_data(success, server_payload, error_message, custom_data)
            {
                console.log("Finalizing the fetch_card_data() operation...");
                //console.log(`Custom data passed: ${custom_data}`);
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = "";       // `Operation completed`
                    this.cards = this.reshuffle_deck(server_payload.recordset);
                    /* EXAMPLE:  [{English: "to slice", French: "trancher",
                                   grammar: "verb", notes: 'sounds like "trench"',
                                   _CLASS: "French Vocabulary", entity_id: "515",
                                   _internal_id: 59, _node_labels: Array [ "BA", "French Vocabulary" ]
                                  }]
                     */
                    this.number_cards = server_payload.total_count;

                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end

            }, // finish_fetch_card_data



            /**
             * Perform an EDIT operation.
             * Send a request to the server, to update the flash card's fields.
             * TODO: maybe save/cancel should be a sub-component shared among various plugins?
             */
            save_edit()
            {
                // Enforce required fields
                if (! 'source_label' in this.current_data) {
                    alert("Cannot save an empty `source_label`. If you want to get rid of this Flash Card, delete it instead");
                    return;
                }
                if (! 'sideA_field' in this.current_data) {
                    alert("Cannot save an empty `sideA_field`. If you want to get rid of this Flash Card, delete it instead");
                    return;
                }
                if (! 'sideB_field' in this.current_data) {
                    alert("Cannot save an empty `sideB_field`. If you want to get rid of this Flash Card, delete it instead");
                    return;
                }
                if (! 'reverse_odds' in this.current_data) {
                    // TODO: also enforce data type and range [0-0.5]
                    alert("Cannot save an empty `reverse_odds`. If you want to get rid of this Flash Card, delete it instead");
                    return;
                }

                if (this.current_metadata.entity_id < 0)     // Negative entity_id is a convention indicating a new Content Item to create
                    // Needed for NEW Content Items
                    this.save_new_item();
                else
                    // Update an EXISTING Flash Card
                    this.save_existing_item();


                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },


            /**
             * Create a NEW Flash Card
             */
            save_new_item()
            {
                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/add_item_to_category";

                const post_obj = {
                                  class_name: "Flash Card",

                                  category_id: this.category_id,

                                  insert_after_uri: this.current_metadata.insert_after_uri,       // entity_id of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                                  insert_after_class: this.current_metadata.insert_after_class,   // Class of Content Item to insert after

                                  source_label: this.current_data.source_label,
                                  sideA_field:  this.current_data.sideA_field,
                                  sideB_field:  this.current_data.sideB_field,
                                  reverse_odds: this.current_data.reverse_odds
                                  };

                console.log(`In 'vue-plugin-f'.  About to contact the server at "${url_server_api}" .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server, using POST data
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
                             callback_fn: this.finish_save_edit});
            },


            /**
             * Update an EXISTING Flash Card
             */
            save_existing_item()
            {
                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item_JSON";

                const post_obj = {entity_id: this.current_metadata.entity_id,
                                  class_name: "Flash Card",

                                  source_label: this.current_data.source_label,
                                  sideA_field:  this.current_data.sideA_field,
                                  sideB_field:  this.current_data.sideB_field,
                                  reverse_odds: this.current_data.reverse_odds
                                  };

                console.log(`In 'vue-plugin-f'.  About to contact the server at "${url_server_api}" .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: true,
                             callback_fn: this.finish_save_edit
                            });
            },


            /** Callback function to wrap up the action of save_edit() upon getting a response from the server.
             *  In case of newly-created items, if successful, the server_payload will contain the newly-assigned entity_id
             *
             * @param {bool} success - Boolean indicating whether the server call succeeded
             * @param server_payload - Whatever the server returned (stripped of information about the success of the operation)
             * @param {string} error_message - Only applicable in case of failure
             */
            finish_save_edit(success, server_payload, error_message)
            {
                console.log("Finalizing the FlashCard save_edit() operation...");

                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
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
                    console.log("'flash_card' component sending `updated-item` signal to its parent");
                    console.log(structuredClone(signal_data));     // Log a frozen deep snapshot of the object
                    this.$emit('updated-item', signal_data);


                    // Synchronize the baseline data to the finalized current data
                    this.original_data = Object.assign({}, this.current_data);  // Clone


                    // Reload the flash cards with the new parameters
                    this.fetch_card_data();
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    // Revert to pre-edit data
                    this.current_data = Object.assign({}, this.original_data);  // Clone
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;       // Make a note that the asynchronous operation has come to an end
                this.editing_mode = false;  // Leave the editing mode

            } // finish_save_edit

        }  // METHODS

    }
); // end component