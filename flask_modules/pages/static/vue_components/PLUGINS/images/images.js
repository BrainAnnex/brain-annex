/*  Vue component to display and edit Content Items of type "i" (Images)
    TODO: rename 'vue-plugin-images'
 */

Vue.component('vue-plugin-i',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:  EXAMPLE: {"uri":52,"pos":10,"schema_code":"i","basename":"my pic","suffix":"jpg","class_name":"Image",
                                                    "caption":"my 1st pic", width:450, height:760}
                                 (if uri is -1, it means that it's a newly-created header, not yet registered with the server)
                                 TODO: take "pos" and "class_name" out of item_data !

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Image on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <!-- Image container -->
                <div v-bind:class="{'edit': edit_metadata}">
                    <a class='i-image-link' v-bind:href="image_url(item_data)" target="_blank">
                        <img v-bind:src="image_url_thumb(item_data)" width=300>
                    </a>


                    <!----------  VIEW-ONLY version (show when NOT in editing mode)  ---------->
                    <div v-show="!edit_metadata" class='i-line'   @dblclick="edit_metadata=true">
                        <span v-if="'caption' in item_data"class='i-caption'>{{current_metadata.caption}}</span>

                        <p v-if="current_metadata.comments" v-html="render_newlines(current_metadata.comments)" style="margin-left: 0; margin-bottom: 0; margin-top: 3px; color:#888"></p>
                    </div>

                    <!----------  EDITABLE version (show when in editing mode)  ---------->
                    <div v-show="edit_metadata">
                        <br><br>
                        <span class="label">Caption</span>
                        <input v-model="current_metadata.caption" size="40">

                        <span class="label">Filename</span>
                        <textarea v-model="current_metadata.basename" rows="2" cols="40" style="color:#666"></textarea>
                        <b>.{{item_data.suffix}}</b>
                        <br><br>

                        <span class="label">Comments</span><br>
                        <textarea v-model="current_metadata.comments" name="myNAME" rows="3" cols="40"></textarea>

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
                                  v-on:edit-content-item="edit_content_item(item_data)">
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
                current_metadata: Object.assign({}, this.item_data),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                pre_edit_metadata: Object.assign({}, this.item_data),   // Clone from the original data passed to this component


                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data



        // ------------------------------   METHODS   ------------------------------
        methods: {
            image_url(item_data)
            // Return the URL of the full image
            {
                return '/BA/api/serve_media/Image/' + item_data.uri;           // Invoke the file server
             },

            image_url_thumb(item_data)
            // Return the URL of the thumbnail version of the image
            {
                return '/BA/api/serve_media/Image/' + item_data.uri + '/th';  // Invoke the file server, with the thumbnail option
             },


            edit_content_item()
            // Enable the document edit mode
            {
                //console.log(`Image component received signal to edit image's metadata'`);
                this.edit_metadata = true;
            },


            cancel_edit()
            /* Invoked when the user cancels the edit-in-progress, or when the save operation fails.
               Revert any changes, and exit the edit mode
             */
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_metadata = Object.assign({}, this.pre_edit_metadata);  // Clone from pre_edit_metadata

                this.edit_metadata = false;      // Exit the editing mode
            },


            save_edit()
            // Send a request to the server, to update the image's metadata
            {
                console.log(`In save_edit(): attempting to save the new metadata , for image with URI '${this.item_data.uri}'`);

                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item";
                const post_obj = {uri: this.item_data.uri,
                                  class_name: "Image",
                                  basename: this.current_metadata.basename,
                                  caption: this.current_metadata.caption,
                                  comments: this.current_metadata.comments
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
                    this.$emit('updated-item', this.current_metadata);

                    // Synchronize the baseline data to the finalized current data
                    this.pre_edit_metadata = Object.assign({}, this.current_metadata);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    // Revert to pre-edit data
                    this.current_metadata = Object.assign({}, this.pre_edit_metadata);  // Clone
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