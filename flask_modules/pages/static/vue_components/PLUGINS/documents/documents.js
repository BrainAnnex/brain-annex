/*  Vue component to display and edit Content Items of type "d" (Document)
 */

Vue.component('vue-plugin-d',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      EXAMPLE: {"class_name": "Document",
                                      "basename": "test", "suffix": "pdf",
                                      "caption": "My first document", "url": "https://arxiv.org/pdf/2402.09090",
                                      "uri": "4849", "schema_code": "d",
                                      "pos": 0}
                                      (if uri is -1, it means that it's a newly-created header, not yet registered with the server)

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <!-- Document container -->
                <div class='doc'>
                    <!-- Document icon -->
                    <img src="/BA/pages/static/graphics/document_48_8168668.png" style="float: left; margin-right: 5px">


                    <!----------  VIEW-ONLY version (show when NOT in editing mode)  ---------->
                    <div v-show="!edit_metadata"   @dblclick="edit_metadata=true">
                        <span style='font-weight:bold; font-size:12px'>&ldquo;{{current_metadata.caption}}&rdquo;</span>
                        <br><br>

                        <!-- Clickable link to document file -->
                        <a href v-bind:href="document_url(item_data)"
                                v-bind:title="current_metadata.caption" v-bind:alt="current_metadata.caption"
                                target="_blank"
                        >
                            {{current_metadata.basename}}.{{current_metadata.suffix}}
                        </a>
                        <br><br>

                        <!-- Clickable URL -->
                        <span v-html="render_url(current_metadata.url)"></span>

                        <span v-if="current_metadata.year" style="margin-left:25px; color:#555">
                            <template v-if="current_metadata.month">{{current_metadata.month}} / </template>
                            {{current_metadata.year}}
                        </span>

                        <p v-if="current_metadata.authors" style="margin-bottom:0; color:#555">{{current_metadata.authors}}</p>
                        <p v-if="current_metadata.comments" v-html="render_newlines(current_metadata.comments)" style="margin-bottom:0; color:#555"></p>

                        <p v-if="current_metadata.rating || current_metadata.read" style="margin-bottom:0; color:#555">
                            <span v-if="current_metadata.rating">{{current_metadata.rating}} &#9733;</span>
                            <span style="margin-left:45px">{{current_metadata.read}}</span>
                        </p>
                    </div>


                    <!----------  EDITABLE version (show when in editing mode)  ---------->
                    <div v-show="edit_metadata">
                        <br><br>
                        <span class="label">Caption</span>
                        <textarea v-model="current_metadata.caption" rows="2" cols="40" style="font-weight: bold"></textarea>
                        <br><br>

                        <span class="label">Filename</span>
                        <textarea v-model="current_metadata.basename" rows="2" cols="40" style="color:#666"></textarea>
                        <b>.{{item_data.suffix}}</b>
                        <br><br>

                        <span class="label">URL</span> <input v-model="current_metadata.url" size="40">
                        <br><br>

                        <span class="label">Month</span> <input v-model="current_metadata.month" size="2">
                            &nbsp;&nbsp; <span class="label">Year</span> <input v-model="current_metadata.year" size="4">
                        <br><br>

                        <span class="label">Authors</span> <input v-model="current_metadata.authors" size="35">
                        <br><br>

                        <span class="label">Comments</span><br>
                        <textarea v-model="current_metadata.comments" name="myNAME" rows="3" cols="45"></textarea>

                        <br><br>
                        <span class="label">Rating</span> <input v-model="current_metadata.rating" size="3">
                        &nbsp;&nbsp; <span class="label">Read?</span> <input v-model="current_metadata.read" size="8">
                        &nbsp;&nbsp; <span style="color: gray">URI: &#96;{{current_metadata.uri}}&#96;</span>

                        <!-- CONTROLS to edit the document metadata -->
                        <p v-show="edit_metadata" style="text-align: right">
                            <span @click="cancel_edit" class="clickable-icon" style="color:blue">CANCEL</span>
                            <button @click="save_edit" style="margin-left: 15px; font-weight: bold; padding: 10px">SAVE</button>
                            <br>
                            <span v-if="waiting" class="waiting">Performing the update</span>
                        </p>

                        <!-- STATUS line -->
                        <span v-bind:class="{'error-message': error, 'status-message': !error }">{{status_message}}</span>
                    </div>


                </div>		<!-- End of Document container -->


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
                                  v-on:edit-content-item="edit_content_item">
                    </vue-controls>

                <!--  End of STANDARD CONTROLS -->


            </div>		<!-- End of outer container -->
            `,



        // ------------------------------   DATA   ------------------------------
        data: function() {
            return {
                edit_metadata: false,

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
            document_url(item)
            // Return the URL of the full documents
            {
                return '/BA/api/serve_media/' + item.uri;           // Invoke the file server
             },


            edit_content_item()
            // Enable the document edit mode
            {
                //console.log(`Documents component received signal to edit document`);
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
            // Send a request to the server, to update the document's caption
            {
                //console.log(`In save_edit(): attempting to save the new caption (${this.current_metadata.caption}) , for document with URI '${this.item_data.uri}'`);

                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item";
                const post_obj = {uri: this.item_data.uri,
                                  class_name: "Document",
                                  caption: this.current_metadata.caption,
                                  basename: this.current_metadata.basename,
                                  url: this.current_metadata.url,
                                  month: this.current_metadata.month,
                                  year: this.current_metadata.year,
                                  authors: this.current_metadata.authors,
                                  comments: this.current_metadata.comments,
                                  rating: this.current_metadata.rating,
                                  read: this.current_metadata.read
                                  };
                const my_var = null;        // Optional parameter to pass, if needed

                console.log(`In 'vue-plugin-d'.  About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server_NEW(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
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
                    console.log("Documents component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_metadata);

                    // Synchronize the baseline data to the finalized current data
                    this.pre_edit_metadata = Object.assign({}, this.current_metadata);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
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
            },


            render_url(cell_data)
            /*  If the passed argument is a string that appears to be a URL,
                convert it into a string with HTML code for a hyperlink that opens in a new window;
                if the URL is very long, show it in abbreviated form in the hyperlink text.
                In all other cases, just return the argument.

                Note: this function is also found in records.js, single_record.js and site_links.js
             */
            {
                const max_url_len = 35;     // For text to show, NOT counting the protocol part (such as "https://")

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
                        dest_name = dest_name.substring(0, max_url_len) + "...";    // Display long links in abbreviated form

                    return `<a href='${cell_data}' target='_blank' style='font-size:10px'>${dest_name}<a>`;
                }
                else
                    return cell_data;
            }

        }  // methods

    }
); // end component