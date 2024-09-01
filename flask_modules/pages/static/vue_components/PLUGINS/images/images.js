/*  Vue component to display and edit Content Items of type "i" (Images)
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

                    <!-- Image caption (or editable version) -->
                    <p v-show="!edit_metadata" class='i-line'>
                        <span v-if="'caption' in item_data"class='i-caption'>{{current_caption}}</span>
                    </p>
                    <p v-show="edit_metadata">
                        <input v-model="current_caption" size="40">
                        <!-- File name -->
                        <br><br><span style="color:#888">File: &ldquo;{{item_data.basename}}.{{item_data.suffix}}&rdquo;</span>
                    </p>

                    <!-- Controls to edit the image metadata -->
                    <p v-show="edit_metadata" style="text-align: right">
                        <span @click="cancel_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                        <button @click="save_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                        <br>
                        <span v-if="waiting" class="waiting">Performing the update</span>
                    </p>
                    <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
                </div>		<!-- End of Image container -->


                <!--  STANDARD CONTROLS (a <SPAN> element that can be extended with extra controls)
                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component,
                      but some get intercepted and handled here, namely:

                            v-on:edit-content-item
                -->
                <!-- OPTIONAL MORE CONTROLS to the LEFT of the standard ones would go here -->

                <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                              v-on="$listeners"
                              v-on:edit-content-item="edit_content_item(item_data)">
                </vue-controls>

                <!-- OPTIONAL MORE CONTROLS to the RIGHT of the standard ones would go here -->

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                // This object contains the values bound to the editing field, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                //current_data: Object.assign({}, this.item_data),  // NOT in current use; just saving the caption for now

                // Clone, used to restore the data in case of a Cancel or failed save
                //original_data: Object.assign({}, this.item_data)

                current_caption: this.item_data.caption,
                original_caption: this.item_data.caption,

                edit_metadata: false,

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
                return '/BA/api/serve_media/' + item_data.uri;           // Invoke the file server
             },

            image_url_thumb(item_data)
            // Return the URL of the thumbnail version of the image
            {
                return '/BA/api/serve_media/' + item_data.uri + '/th';    // Invoke the file server, with the thumbnail option
             },


            edit_content_item()
            // Enable the document edit mode
            {
                console.log(`Image component received signal to edit image`);
                this.edit_metadata = true;
            },


            cancel_edit()
            // Revert any changes, and exit the edit mode
            {
                //console.log(`In cancel_edit()`);
                this.current_caption = this.original_caption;
                this.edit_metadata = false;
            },


            save_edit()
            // Send a request to the server, to update the image's caption
            {
                console.log(`In save_edit(): attempting to save the new caption (${this.current_caption}) , for document with URI '${this.item_data.uri}'`);

                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item";
                const post_obj = {uri: this.item_data.uri,
                                  class_name: "Images",
                                  caption: this.current_caption};
                const my_var = null;        // Optional parameter to pass, if needed

                console.log(`About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {post_obj: post_obj,
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
                    this.original_caption = this.current_caption;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                    this.current_caption = this.original_caption;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;       // Make a note that the asynchronous operation has come to an end
                this.edit_metadata = false; // Leave the editing mode
            }

        }  // methods

    }
); // end component