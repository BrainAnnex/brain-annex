// TODO: the special handling for "closing" Headers

/*  MIT License.  Copyright (c) 2021 Julian A. West
    This file is part of the "Brain Annex" project (https://BrainAnnex.org)
 */

Vue.component('vue-plugin-h',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count'],
        /*  item_data:  EXAMPLE: {"item_id":52,"pos":10,"schema_code":"h","text":"MY NEW SECTION"}
                                 (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)
            index:      the zero-based position of the Record on the page
            item_count: the total number of Content Items (of all types) on the page
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <div class='h-text'>
                <span v-if="!editing_mode" class='h-text'>{{ current_data.text }}</span>
                <span v-else><input type="text" size="40" v-model="current_data.text">
                    <button @click="save">SAVE</button>
                    <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                </span>
                <span v-if="waiting" style="margin-left:15px">saving...</span>
            <br>
            <!-- In the PHP version, the controls were placed here -->
            </div>
            <span v-if="status!='' && !editing_mode">Status : {{status}}</span>

            <!--  STANDARD CONTROLS
                  (all signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item
            -->
            <vue-controls v-bind:allow_editing="allow_editing" v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item(item_data)">
            </vue-controls>

            \n</div>\n		<!-- End of outer container box -->
            `,


        data: function() {
            return {
                editing_mode: (this.item_data.item_id == -1 ? true : false),    // -1 means "new Item" (automatically placed in editing mode)

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                waiting: false,
                status: "",
                error_indicator: false
            }
        }, // data


        // ------------------------------   METHODS   ------------------------------
        methods: {

            edit_content_item(item)
            {
                console.log(`Header component received signal to edit content item of type '${item.schema_code}' , id ${item.item_id}`);
                this.editing_mode = true;       // Enter the editing mode
            },


            save()
            {
                // Start the body of the POST to send to the server
                post_body = "schema_code=" + this.current_data.schema_code;

                if (this.item_data.item_id == -1)  {     // -1 is a convention indicating a new Content Item to create,
                     // Needed for NEW Content Items
                     post_body += "&category_id=" + this.category_id;
                     const insert_after = this.item_data.insert_after;      // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                     post_body += "&insert_after=" + insert_after;

                     url_server = `/BA/api/simple/add_item_to_category`;    // URL to communicate with the server's endpoint
                }
                else {   // Update an EXISTING header
                    post_body += "&item_id=" + this.item_data.item_id;

                    url_server = `/BA/api/simple/update`;                   // URL to communicate with the server's endpoint
                }

                // Go over each field.  TODO: generalize
                if ('text' in this.current_data)
                    post_body += "&text=" + encodeURIComponent(this.current_data.text);
                else  {
                    alert("Cannot save an empty header. If you want to get rid of it, delete it instead");
                    return;
                }

                this.waiting = true;
                this.status = "";                    // Clear any message from the previous operation
                this.error_indicator = false;       // Clear any error from the previous operation

                console.log("In 'vue-plugin-h', save().  post_body: ", post_body);
                ServerCommunication.contact_server_TEXT(url_server, post_body, this.finish_save);
            }, // save


            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID
             */
            {
                console.log("Finalizing the Header save operation...");
                if (success)  {     // Server reported SUCCESS
                    this.status = `Successful edit`;

                    // If this was a new item (with the temporary ID of -1), update its ID with the value assigned by the server
                    if (this.item_data.item_id == -1)
                        this.current_data.item_id = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Headers component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the baseline data to the finalized current data
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.status = `FAILED edit`;
                    this.error_indicator = true;
                    this.cancel_edit();         // Restore the data to how it was prior to the failed changes. TODO: maybe leave in edit mode?
                }

                // Final wrap-up, regardless of error or success
                this.editing_mode = false;      // Exit the editing mode
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end

            }, // finish_save


            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.item_id == -1) {
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