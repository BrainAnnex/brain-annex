/*  MIT License.  Copyright (c) 2021 Julian A. West
    This file is part of the "Brain Annex" project (https://BrainAnnex.org)
 */

Vue.component('vue-plugin-n',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count'],
        /*   item_data:  EXAMPLE: {"item_id":52,"pos":10,"schema_code":"n","basename":"notes-123","suffix":"htm"}
                                  (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)
            index:      the zero-based position of the Record on the page
            item_count: the total number of Content Items (of all types) on the page
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <div class="notes" v-if="!editing_mode" v-html="body_of_note">
                <span v-bind:class="{'n-waiting': waiting_mode}">{{status}}</span>
            </div>

            <div v-show="editing_mode" class="add-form">
                <div id='addNoteBlock' style='margin-top:10px; width:967px'>

                    <div class="notes" v-bind:data_category="category_id" style='display:none'>
                        <b>THE EDITOR WILL GO HERE</b>
                    </div>

                    <div ref="julian"></div>  <!-- The content of this <div> gets replaced by the HTML online editor CKeditor when fired up
                                                               TODO: maybe use a Vue conditional to call a function that return a CK object body -->

                    <!-- The editor Controls (with the SAVE and CANCEL buttons) are initially hidden -->
                    <div class='editor-controls'>
                        <button @click="save_edit()">SAVE</button>
                        <button @click="cancel_edit()">CANCEL</button>
                    </div>

                </div>  <!--  Terminate the wrapper DIV "addNoteBlock" -->
            </div> <!--  Terminate the wrapper DIV "add-form" -->


            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
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
                editing_mode: (this.item_data.item_id == -1 ? true : false),    // -1 means "new Item"

                //body_of_note: this.get_note(this.item_data)
                body_of_note: (this.item_data.item_id == -1 ? "NEW NOTE" : this.get_note(this.item_data)),
                note_editor: null,          // CKeditor object
                old_note_value: "",         // The pre-edit value
                new_note_value: "",         // Value of the tentative edit (subject to successful server update)

                // This object contains the values bound to the editing field, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                waiting_mode: true,         // Flag to indicate whether the Note is still being fetched from the server
                save_waiting_mode: false,   // To distinguish from waiting_mode (from fetching value)
                error_indicator: false,
                status: ""
            }
        }, // data



        mounted() {
            /* Note: the "mounted" Vue hook is invoked later in the process of launching this component; waiting this late is
                     needed to make sure that the 'CKeditor_0' DIV element is present in the DOM.
             */
            console.log("the Notes component has been mounted");

            if (this.item_data.item_id == -1)
                this.create_new_editor("");   // We're dealing with an "ADD" operation; so, we start with an empty Note
        },



        // ---------------------------  METHODS  ---------------------------
        methods: {

            get_note: function (item_data) {
                console.log("In get_note. New item to look up : `" + item_data.item_id + "`");

                this.waiting_mode = true;

                // Prepare a URL to communicate with the server's endpoint
                url_server = "/BA/api/simple/get_media/" + item_data.item_id;

                //ServerCommunication.contact_server_TEXT(url_server, "", this.finish_get_note);
                ServerCommunication.contact_server(url_server, {callback_fn: this.finish_get_note});

                return "Retrieving note id " + item_data.item_id + "...";
            }, // get_note


            finish_get_note(success, server_payload, error_message, index)
            // Callback function to wrap up the action of delete_content_item() upon getting a response from the server
            {
                console.log("Finalizing the get_note operation...");
                if (success)  {     // Server reported SUCCESS
                    this.body_of_note = server_payload;
                }
                else  {             // Server reported FAILURE
                    this.body_of_note = "Unable to retrieve note contents. " + error_message;
                }
                this.waiting_mode = false;
            }, // finish_get_note



            edit_content_item(item)
            // Handler for the 'edit-content-item' signal received from child component
            {
                console.log(`'Note' component received signal to edit content item of type '${item.schema_code}' , id ${item.item_id}`);

                this.old_note_value = this.body_of_note;    // Save the current Note contents, in case of aborted or failed edit
                this.editing_mode = true;

                // Retrieve the CKEDITOR object, if present from an earlier edit (or Note creation), or create a new one
                editor_obj = this.note_editor;
                if (!editor_obj) {
                    console.log("Creating a new CKEDITOR object");
                    noteCurrentValue = this.body_of_note;
                    this.create_new_editor(noteCurrentValue);
                }
                else
                    console.log("Re-using existing CKEDITOR object");
            },



            create_new_editor(noteCurrentValue)
            /*	This is the entry point for adding a new note (which is HTML text inside a DIV element).

                [In the PHP version, this function also handles existing Notes]

                Create a "CK editor" object, to be placed inside a <div ref="julian"> element.

                Fire up (and save) a new instance of a CK Editor

                noteCurrentValue is the initial HTML to place in the editor.
             */
            {
                console.log("Inside create_new_editor()");

                if ( this.note_editor )  {
                    alert("WARNING: the CKeditor already exists for this note!  It shouldn't!");
                    return;					// If an open CK Editor already exists for this note, do nothing (normally, this should never happen)
                }


                /* 	Create and save a new CK editor instance inside the <div ref="julian"> element,
                    setting its value to the html in the note being edited
                 */
                //var editorBlockID = 'CKeditor_0';					// ID of the DIV block containing the CKeditor
                //document.getElementById(editorBlockID).style.display = '';	// Since we are now in editing mode, make visible the DIV element hosting the CK editing area
                //var noteCurrentValue = "";      // We're dealing with an "ADD" operation; so, we start with an empty Note
                var config = {};

                console.log(CKEDITOR);

                // Make sure that the DIV element in which to place the CKeditor exists
                var element = this.$refs.julian;
                if (! element)  {
                    //alert(`ERROR: no DOM element present with ID '${editorBlockID}'`);
                    alert(`ERROR: no DOM element present for editing new Note`);
                    console.log(element);
                    return;
                }

                var newEditor = CKEDITOR.appendTo(element, config, noteCurrentValue);	// Create and save a new CKeditor instance at the end of the specified DOM element (a DIV)

                this.note_editor = newEditor;       // Save the CKEDITOR object, for later edits


                // Instruct CKeditor to output HTML rather than the default XHTML
                newEditor.on( 'instanceReady', function( ev ) {
                    // The following operations are done when the CKeditor is finished loading
                    // Event fired when the CKEDITOR instance is completely created, fully initialized and ready for interaction.
                    // See https://ckeditor.com/docs/ckeditor4/latest/api/CKEDITOR_editor.html#event-instanceReady
                    //alert("'instanceReady' notification: CKeditor is ready (noteID = " + noteID + ", editor ID = " + ev.editor.id + ")");
                    ev.editor.dataProcessor.writer.selfClosingEnd = '>';	// Output self-closing tags the HTML5 way, like <br>

                    // TODO: maybe restore the auto-scrolling, as done below
                    // Scroll to the top of the note (applicable to new notes and existing ones)
                    //anchorName = 'n_' + noteID;
                    //alert("About to scroll to anchor named: `" + anchorName + "`");

                    //location.hash = anchorName;		# ALTERNATE APPROACH for the next 2 lines (also works, but messes up the URL in the browser)

                    //var element_to_scroll_to = document.getElementsByName(anchorName)[0];
                    //element_to_scroll_to.scrollIntoView();

                    //alert("Finished scrolling");
                });


                /* FOR TESTING
                newEditor.on( 'destroy', function( evt ) {
                    alert("'destroy' notification: CKeditor got destroyed (noteID = -1, editor ID = " + evt.editor.id + ")");
                });
                */

                // Update the visibility of the various remaining elements (i.e. the controls)
                //setControlsEditMode(0);

            }, // create_new_editor


            save_edit()
            // Invoked by clicking on the "SAVE" link (only visible in editing mode)
            {
                noteID = this.item_data.item_id;    // -1 indicates a new Note

                console.log("Inside save_edit().  noteID = " + noteID);

                if (!this.note_editor)  {
                    alert("ERROR: unable to locate the CKeditor object.  Save the contents of the Note in a separate document, then refresh page and re-edit");
                    return;
                }

                // Retrieve the CKeditor's content.  This data will be sent to the server
                var html = this.note_editor.getData();

                console.log("Edited value is: " + html);

                // Bring all controls back to non-edit mode:
                // show the note, and update the visibility of the various controls
                this.editing_mode = false;

                // Destroy the editor
                // self.destroy_editor();

                this.do_box_save(noteID, html);

            },  // save_edit


            do_box_save(noteID, newBody)
            /* 	Invoked when the "SAVE" button is pressed on the specified note.
                Carry out, asynchronously, the record update operation.
                If noteID = -1 then we're adding a new note; otherwise, we're editing the existing note with the specified ID
             */
            {
                var invocation;
                var keyID;

                console.log("Inside do_box_save() : noteID = " + noteID);
                console.log("newBody :" + newBody);

                this.new_note_value = newBody;					// Save the value of the tentative edit (subject to successful server update)

                var positionID = this.item_data.pos;

                // Start the body of the POST to send to the server
                var post_body = "schema_code=" + this.item_data.schema_code;

                // Make the value safe for inclusion in a URL
                // encodeURIComponent() is needed because newBody may contain "&" or "=" characters.  TODO: switch to new API
                if (noteID == -1)  {	// Add NEW note
                    post_body += "&category_id=" + this.category_id + "&body=" + encodeURIComponent(newBody);
                    const insert_after = this.item_data.insert_after;   // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                    post_body += "&insert_after=" + insert_after;

                    var url_server = "/BA/api/simple/add_item_to_category";
                }
                else  {				    // Edit EXISTING note
                    post_body += "&item_id=" + noteID + "&body=" + encodeURIComponent(newBody);
                    var url_server = "/BA/api/simple/update";
                }


                this.save_waiting_mode = true;
                this.error_indicator = false;   // Clear possible past message

                //console.log(url_server);
                console.log("In 'vue-plugin-n', save().  post_body: ", post_body);      // TODO: only show first few chars
                ServerCommunication.contact_server_TEXT(url_server, post_body, this.finish_save);
            },  // do_box_save()


            finish_save(success, server_payload, error_message)
            /*	Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID.

                Exit the editing mode.  Invoked upon a SAVE operation on an existing note.
                Restore all <input> fields to strings, using the values saved in global arrays
                Turn the SAVE & CANCEL buttons back into edit links
             */
            {
                var boxValue;

                console.log("Finalizing the Note save operation...");

                /* Turn the note box into its final value

                    NOTE:   new_note_value is the counterpart of this.current_data
                            old_note_value is the counterpart of this.original_data
                 */

                if (success) {    // Server reported SUCCESS
                    this.status = "Successful edit";
                    this.error_indicator = false;

                    // If this was a new item (with the temporary ID of -1), update its ID with the value assigned by the server
                    if (this.item_data.item_id == -1)
                        this.current_data.item_id = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Notes component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    boxValue = this.new_note_value;
                }
                else  {		        // Server reported FAILURE
                    this.status = "FAILED SAVE. " + error_message;
                    this.error_indicator = true;
                    boxValue = this.old_note_value;         // Restore the old value
                    this.inform_component_root_of_cancel();
                    //alert(oldValue);
                }
                console.log("boxValue = " + boxValue);


                // Final wrap-up, regardless of error or success

                this.body_of_note = boxValue;   // Set the DIV data box content (to either the new value or the restored old value)

                this.editing_mode = false;      // Exit the editing mode
                this.save_waiting_mode = false;

            },  // finish_save


            cancel_edit()
            // Invoked by clicking on the "CANCEL" link (only visible in editing mode)
            {
                noteID = this.item_data.item_id;    // -1 indicates a new Note

                console.log("Inside cancel_edit().  noteID = " + noteID);

                this.note_editor.setData(this.old_note_value);

                this.inform_component_root_of_cancel();

                this.editing_mode = false;

                // TODO: maybe destroy the CKeditor object, if there are too many on the page
                // self.destroy_editor();
            },

            inform_component_root_of_cancel()
            // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
            {
                if (this.current_data.item_id == -1) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Headers sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }
            },


            destroy_editor()
            // NOT IN CURRENT USE.  Not sure if needed.  TODO: maybe use if too many editor objects are lying around?
            {
                var editor = this.note_editor;
                editor.destroy();
                this.note_editor = null;
            }

        } // END methods

    }
); // end component