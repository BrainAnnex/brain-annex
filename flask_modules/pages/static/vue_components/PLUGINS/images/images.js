/*  Vue component to display and edit Content Items of type "i" (Images)
    TODO: rename 'vue-plugin-images'
 */

Vue.component('vue-plugin-i',
    {
        props: ['item_fields', 'item_metadata',
                'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_fields:    An object with the editable properties of this Image item.
                                EXAMPLE: {"basename":"my pic", "suffix":"jpg", "caption":"my 1st pic"}

            item_metadata:  An object with the metadata of this Image item.
                                For a newly-created Content Item, not yet registered with the server,
                                the value of `entity_id` will be a negative number (unique on the page),
                                and there will be the additional keys `insert_after_uri` and `insert_after_class`
                                EXAMPLE of existing Image item:
                                        {"class_name":"Image",
                                        "pos":0,
                                        "schema_code":"timer",
                                        "entity_id":"8809",
                                        "schema_code":"i",
                                        "width":450, "height":760
                                        }

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The Entity ID of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Image on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <!-- Image container -->
                <div v-bind:class="{'edit': edit_metadata}">
                    <a class='i-image-link' v-bind:href="image_url()" target="_blank">
                        <img v-bind:src="image_url_thumb()" width=300>
                    </a>


                    <!----------  VIEW-ONLY version (show when NOT in editing mode)  ---------->
                    <div v-show="!edit_metadata" class='i-line'   @dblclick="edit_metadata=true">
                        <span v-if="'caption' in current_data"class='i-caption'>{{current_data.caption}}</span>

                        <p v-if="current_data.comments" v-html="render_newlines(current_data.comments)" style="margin-left: 0; margin-bottom: 0; margin-top: 3px; color:#888"></p>
                    </div>

                    <!----------  EDITABLE version (show when in editing mode)  ---------->
                    <div v-show="edit_metadata">
                        <br><br>
                        <span class="label">Caption</span>
                        <input v-model="current_data.caption" size="40">

                        <span class="label">Filename</span>
                        <textarea v-model="current_data.basename" rows="2" cols="40" style="color:#666"></textarea>
                        <b>.{{current_data.suffix}}</b>
                        <br><br>

                        <span class="label">Comments</span><br>
                        <textarea v-model="current_data.comments" name="myNAME" rows="3" cols="40"></textarea>

                        <!-- CONTROLS to edit the image METADATA -->
                        <p v-show="edit_metadata" style="text-align: right">
                            <span @click="cancel_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                            <button @click="save_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                            <br>
                            <span v-if="waiting" class="waiting">Performing the update</span>
                        </p>

                        <!-- STATUS line -->
                        <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
                    </div>


                </div>		<!-- End of Image container -->


                <!--  Start of STANDARD CONTROLS (inline elements that can be extended with extra controls)
                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component,
                      but some get intercepted and handled here, namely:

                              v-on:edit-content-item

                      Optional EXTRA controls may be placed before (will appear to the left)
                      or after (will appear to the right) of the standard controls
                -->

                    <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                                  v-on="$listeners"
                                  v-on:edit-content-item="edit_content_item()">
                    </vue-controls>

                <!-- End of STANDARD CONTROLS -->

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                edit_metadata: false,   // Editing mode for the metadata

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_fields),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_fields),   // Clone from the original data passed to this component

                // Private copy of the metadata
                current_metadata:   Object.assign({}, this.item_metadata),
                
                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            image_url()
            // Return the URL of the full image
            {
                return '/BA/api/serve_media/Image/' + this.current_metadata.entity_id;           // Invoke the file server
            },

            image_url_thumb()
            // Return the URL of the thumbnail version of the image
            {
                return '/BA/api/serve_media/Image/' + this.current_metadata.entity_id + '/th';  // Invoke the file server, with the thumbnail option
            },


            /**
             * Enable the document edit mode
             * Handler for the "edit-content-item" SIGNAL received from the child component "vue-controls"
             * (which is generated there when clicking on the Edit button)
             */
            edit_content_item()
            {
                console.log(`'Images' component received SIGNAL to edit its contents`);
                this.edit_metadata = true;
            },


            /**
             * Invoked by clicking on the "CANCEL" link (only visible in editing mode)
             */
            cancel_edit()
            /* Invoked when the user cancels the edit-in-progress, or when the save operation fails.
               Revert any changes, and exit the edit mode
             */
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                this.edit_metadata = false;      // Exit the editing mode
            }, // cancel_edit


            save_edit()
            // Send a request to the server, to update the image's metadata
            {
                console.log(`In save_edit(): attempting to save the new metadata , for image with Entity ID '${this.current_metadata.entity_id}'`);

                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item";
                const post_obj = {entity_id: this.current_metadata.entity_id,
                                  class_name: "Image",
                                  basename: this.current_data.basename,
                                  caption: this.current_data.caption,
                                  comments: this.current_data.comments
                                  };
                const my_var = null;        // Optional parameter to pass, if needed

                console.log(`About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             callback_fn: this.finish_save_edit,
                             custom_data: my_var
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },


            finish_save_edit(success, server_payload, error_message, custom_data)
            // Callback function to wrap up the action of save_edit() upon getting a response from the server
            {
                console.log("Finalizing the save_edit() operation...");
                console.log(`Custom data passed: ${custom_data}`);
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;

                    // Inform the parent component of the new state of the document's metadata
                    console.log("Images component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the baseline data to the finalized current data
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    // Revert to pre-edit data
                    this.current_data = Object.assign({}, this.original_data);  // Clone
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;       // Make a note that the asynchronous operation has come to an end
                this.edit_metadata = false; // Leave the editing mode
            },


            render_newlines(text)
            // Return all the newlines in the given text replaced as HTML line breaks: "<br>"
            {
                return text.replace(/\n/g, "<br>");
            }

        }  // methods

    }
); // end component