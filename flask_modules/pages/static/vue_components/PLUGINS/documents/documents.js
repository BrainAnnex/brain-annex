/*  Vue component to display and edit Content Items of type "d" (Document)
    TODO: rename 'vue-plugin-documents'
 */

Vue.component('vue-plugin-d',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*  item_data:      EXAMPLE: {"class_name": "Document",
                                      "basename": "test", "suffix": "pdf",
                                      "caption": "My first document", "url": "https://arxiv.org/pdf/2402.09090",
                                      "entity_id": "4849", "schema_code": "d",
                                      "pos": 0,
                                      "internal_id": 123}
                                      (if entity_id is -1, it means that it's a newly-created header, not yet registered with the server)
                                      TODO: take "pos", "class_name", "class_handler", "schema_code" out of item_data !

            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The Entity ID of the Category page where this document is displayed (used when creating new documents)
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
                    <div v-show="!edit_metadata"   @dblclick="edit_content_item()">
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


                        <!-- Show cover image, if present -->
                        <img
                            v-if="show_cover_image"
                            v-bind:src="cover_image(current_metadata.entity_id)"
                            @error="show_cover_image = false"
                            width=200
                        >


                        <!--
                            Various metadata that may be present
                          -->

                        <span v-if="current_metadata.year" style="margin-left:25px; color:#555">
                            <template v-if="current_metadata.month">{{current_metadata.month}} / </template>
                            {{current_metadata.year}}
                        </span>

                        <p v-if="current_metadata.authors" style="margin-bottom:0; color:#555">{{current_metadata.authors}}</p>
                        <p v-if="current_metadata.comments" v-html="render_newlines(current_metadata.comments)" style="margin-bottom:0; color:#555"></p>

                        <p v-if="current_metadata.rating || current_metadata.read" style="margin-bottom:0; color:#555">
                            <span v-if="current_metadata.rating">{{current_metadata.rating}}</span><span v-if="current_metadata.rating" class="star-yellow">&#9733;</span>
                            <span style="margin-left:45px">{{current_metadata.read}}</span>
                        </p>

                    </div>


                    <!----------  EDITABLE version (shown when in editing mode)  ---------->
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
                        <span class="label">Rating</span>
                        <select v-model="current_metadata.rating">
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

                        &nbsp;&nbsp; <span class="label">Read?</span> <input v-model="current_metadata.read" size="8">
                        &nbsp;&nbsp; <span style="color: gray">Entity ID: &#96;{{current_metadata.entity_id}}&#96;</span>
                        <br>

                        <p style="position: relative; z-index: 100;">
                            <span class="label">Storage (not yet editable):</span><br>

                            <select @change='change_storage_dir' v-model="location" style="font-size: 10px">
                                <option v-for="dir in all_directories"
                                        v-bind:value="dir">
                                    {{dir}}
                                </option>
                            </select>
                        </p>

                        <!-- CONTROLS to edit the document METADATA -->
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
                edit_metadata: false,   // Editing mode for the metadata

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_metadata: Object.assign({}, this.item_data),    // Clone from the original data passed to this component

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                pre_edit_metadata: Object.assign({}, this.item_data),   // Clone from the original data passed to this component

                show_cover_image: true,

                location : null,    // The storage directory for this document; null indicates the default, or to be looked up
                                    //  EXAMPLE: "documents/Ebooks & Articles/SYSTEMS BIO"

                all_directories: null,  // Array of names of all available storage directories
                                        /* EXAMPLE:
                                            [
                                                "documents/Ebooks & Articles/Biomedical",
                                                "documents/Ebooks & Articles/SYSTEMS BIO",
                                                "documents/Ebooks & Articles/math"
                                            ]
                                         */

                waiting: false,         // Whether any server request is still pending
                error: false,           // Whether the last server communication resulted in error
                status_message: ""      // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data




        // ------------------------------   METHODS   ------------------------------
        methods: {

            document_url(item)
            // Return the URL of the document's body
            {
                return '/BA/api/serve_media/Document/' + item.entity_id;      // URL that generates the desired document
            },


            cover_image(entity_id)
            // Return the URL of the document's cover image (possibly a 404 error)
            {
                return '/BA/api/serve_document_cover/' + entity_id;           // URL that generates the desired cover image
            },



            /**
             * Enable the document edit mode
             */
            edit_content_item()
            {
                //console.log(`Received request to edit document metadata`);
                this.edit_metadata = true;

                console.log("Retrieving folder location");
                this.retrieve_document_folders(this.item_data.internal_id);
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
            },


            change_storage_dir()
            {
                alert("Change of storage location not yet implemented");
            },



            /*
                ------------   SERVER CALLS   ------------
             */

            save_edit()
            // Send a request to the server, to update the document's metadata
            {
                //console.log(`In save_edit(): attempting to save the new metadata, for document with entity_id '${this.item_data.entity_id}'`);

                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/update_content_item_JSON";

                const post_obj = {entity_id: this.item_data.entity_id,
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

                console.log(`In 'vue-plugin-d'.  About to contact the server at "${url_server_api}" .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: true,
                             callback_fn: this.finish_save_edit
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_save_edit(success, server_payload, error_message)
            /* Callback function to wrap up the action of save_edit() upon getting a response from the server

                success:        Boolean indicating whether the server call succeeded
                server_payload: Whatever the server returned (stripped of information about the success of the operation)
                error_message:  A string only applicable in case of failure
            */
            {
                console.log("Finalizing the save_edit() operation...");

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
                    // Revert to pre-edit data
                    this.current_metadata = Object.assign({}, this.pre_edit_metadata);  // Clone
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;       // Make a note that the asynchronous operation has come to an end
                this.edit_metadata = false; // Leave the editing mode
            },


            /**
             * Initiate request to server, to obtain the names of all storage folders,
             * as well as the folder where this document is kept (a null for this latter value
             * is taken to mean "default folder for documents")
             */
            retrieve_document_folders(internal_id)
            {
                // Send the request to the server, using a POST
                const url_server_api = "/BA/api/directories-stored-in";

                const post_data = {node_internal_id: internal_id};

                console.log(`In server_communication_POST(): about to contact the server at "${url_server_api}" .  POST data:`);
                console.log(post_data);

                // Initiate asynchronous contact with the server
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_data,
                             json_encode_send: true,
                             callback_fn: this.finish_retrieve_document_folders
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
            },

            finish_retrieve_document_folders(success, server_payload, error_message, custom_data)
            /* Callback function to wrap up the action of get_data_from_server() upon getting a response from the server.

                success:        Boolean indicating whether the server call succeeded
                server_payload: Whatever the server returned (stripped of information about the success of the operation)
                error_message:  A string only applicable in case of failure
                custom_data:    Whatever JavaScript pass-thru value, if any, was passed by the contact_server() call
            */
            {
                console.log("Finalizing the retrieve_document_folders() operation...");
                if (success)  {     // Server reported SUCCESS
                    console.log("    server call was successful; it returned: ", server_payload);
                    this.status_message = `Operation completed`;
                    console.log(`server_payload.location: ${server_payload.location}`);

                    this.all_directories = server_payload.all_directories;

                    if (server_payload.location === null)  {
                        console.log("    falling back on standard default");
                        this.location = "[STANDARD DEFAULT FOLDER FOR DOCUMENTS]";
                        this.all_directories.push(this.location);
                        }
                    else
                        this.location = server_payload.location;
                }
                else  {             // Server reported FAILURE
                    this.error = true;
                    this.status_message = `FAILED operation: ${error_message}`;
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;      // Make a note that the asynchronous operation has come to an end
            }


        }  // methods

    }
); // end component