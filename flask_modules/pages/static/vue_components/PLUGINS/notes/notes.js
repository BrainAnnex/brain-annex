/*  Vue component to display and edit Content Items of type "n" (a single "note", i.e. HTML-formatted text)
 */

Vue.component('vue-plugin-n',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count'],
        /*   item_data:  EXAMPLE: {"uri":"52","pos":10,"schema_code":"n","basename":"notes-123","suffix":"htm",
                                   "class_name":"Note","title":"My TO-DO list"}
                                  (if uri is negative, it means that it's a newly-created header, not yet registered with the server)
            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this Note is displayed (used when creating new documents)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

            <!----------  VIEW-ONLY version (show when NOT in editing mode)  ---------->
            <div class="notes" v-if="!editing_mode" v-html="body_of_note"   @dblclick="enter_editing_mode">
                <!-- Body of Note, and status of last edit  -->
                <span v-bind:class="{'n-waiting': waiting}">{{status_message}}</span>
            </div>


            <!----------  EDITABLE version (show when in editing mode)  ---------->
            <div v-show="editing_mode" class='note-editor'>
                <!-- CK Editor, and edit controls  -->
                <div ref="julian"></div>  <!-- The content of this <div> gets replaced by the HTML online editor CKeditor when fired up
                                               TODO: maybe use a Vue conditional to call a function that return a CK object body -->

                <!-- The Editor Controls (with the SAVE and CANCEL buttons) -->
                <div class='editor-controls'>
                    <button @click="save_edit()">SAVE</button>
                    <button @click="cancel_edit()">CANCEL</button>
                    <span style='margin-left:10px'>Title:</span>
                    <input type="text" v-model="current_data['title']" placeholder="Optionally specify a title" size="60">
                </div>

            </div>  <!--  Terminate the wrapper DIV "note-editor" -->


            <!--  Start of STANDARD CONTROLS (inline elements that can be extended with extra controls)
                  Signals from the Vue child component "vue-controls" below
                  get relayed to the parent of this component,
                  but some get intercepted and handled here, namely:

                          v-on:edit-content-item
            -->
                <img v-if="edit_mode" src="/BA/pages/static/graphics/copy_16_172587.png"
                     class="control" title="COPY TO CLIPBOARD (Not yet implemented)" alt="COPY TO CLIPBOARD (Not yet implemented)">

                <vue-controls v-bind:edit_mode="edit_mode" v-bind:index="index"  v-bind:item_count="item_count"
                              v-on="$listeners"
                              v-on:edit-content-item="edit_content_item(item_data)">
                </vue-controls>

            <!--  End of STANDARD CONTROLS -->

            </div>		<!-- End of outer container box -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                editing_mode: (this.item_data.uri < 0 ? true : false),    // Negative URI means "new Item"

                body_of_note: (this.item_data.uri < 0 ? "NEW NOTE" : "Retrieving note id " + this.item_data.uri + "..."),

                note_editor: null,          // CKeditor object
                old_note_value: "",         // The pre-edit value.  TODO: switch to using the "original_data" Object
                new_note_value: "",         // Value of the tentative edit (subject to successful server update)

                /*
                        current_data:   Object with the values bound to the editing fields, cloned from the "prop" data;
                                        it'll change in the course of the edit-in-progress

                        original_data:  Object with pre-edit data,
                                        used to restore the data in case of an edit Cancel or failed save
                 */

                // This object contains the values bound to the editing field, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data),

                waiting: true,              // Whether any server request is still pending
                save_waiting_mode: false,   // To distinguish from "waiting" (used for fetching value)
                error: false,               // Whether the last server communication resulted in error
                status_message: ""          // Message for user about status of last operation upon server response (NOT for "waiting" status)
            }
        }, // data



        // ------------------------------------   WATCH   ------------------------------------
        watch: {
            body_of_note() {
                console.log('The data attribute `body_of_note` has changed!');
                //this.reload_mathjax();
            }
       },



        // ------------------------------------   HOOKS   ------------------------------------

        mounted()
        /* Note: the "mounted" Vue hook is invoked later in the process of launching this component;
                 waiting this late is needed to make sure that the 'CKeditor_0' DIV element
                 is present in the DOM
         */
        {
            console.log(`the Notes component has been mounted`);
            //alert("The Notes component has been mounted");

            if (this.item_data.uri < 0)
                this.create_new_editor("");     // We're dealing with an "ADD" operation; so, we start with an empty Note
            else
                this.get_note(this.item_data);  // Fetch contents of existing Note from the server
        },


        updated() {
            /* The "updated" Vue hook
             */
            console.log("Invoking the `updated` Vue hook");
            this.reload_mathjax();  // TODO: maybe let process_mathjax() call this, and only if MathJax is undefined
            this.process_mathjax(); // TODO: maybe only invoke if the note contains math text
        },

        beforeDestroy()
        // For debugging purposes, for now...
        {
            //alert(`Invoking the 'beforeDestroy' Vue hook`);
            console.log(`Invoking the 'beforeDestroy' Vue hook`);
        },



        // ------------------------------   METHODS   ------------------------------
        methods: {

            get_note(item_data)
            {
                //console.log("In get_note. Item to look up has URI: `" + item_data.uri + "`");

                this.waiting = true;

                // Prepare a URL to communicate with the server's endpoint
                const url_server_api = "/BA/api/get_text_media/" + item_data.uri;

                ServerCommunication.contact_server(url_server_api,
                                                  {callback_fn: this.finish_get_note});

                console.log("    SENT REQUEST TO SERVER to retrieve Note whose URI is `" + item_data.uri + "`...");
            }, // get_note


            finish_get_note(success, server_payload, error_message, index)
            // Callback function to wrap up the action of get_note() upon getting a response from the server
            {
                console.log("Finalizing the get_note operation...");
                if (success)  {     // Server reported SUCCESS
                    this.body_of_note = server_payload;
                    // (Re)load MathJax, if the note contains MathJax code;
                    // only a weak check is performed for the presence of the substring "\("
                    //if (this.body_of_note.includes("\\("))
                        //this.reload_mathjax();
                }
                else  {             // Server reported FAILURE
                    this.body_of_note = "Unable to retrieve note contents. " + error_message;
                }
                this.waiting = false;

            }, // finish_get_note



            enter_editing_mode()
            // Switch to the editing mode of this Vue component
            {
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


            edit_content_item(item)
            /*  Handler for the "edit_content_item" Event received from the child component "vue-controls"
                (which is generated there when clicking on the Edit button)
             */
            {
                console.log(`'Note' component received received Event to edit its contents`);
                this.enter_editing_mode();
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
                    alert("'destroy' notification: CKeditor got destroyed (editor ID = " + evt.editor.id + ")");
                });
                */

                // Update the visibility of the various remaining elements (i.e. the controls)
                //setControlsEditMode(0);

            }, // create_new_editor


            save_edit()
            // Invoked by clicking on the "SAVE" link (only visible in editing mode)
            {
                noteID = this.item_data.uri;    // Negative values indicates a new Note

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
                If noteID < 0 then we're adding a new note; otherwise, we're editing the existing note with the specified ID
             */
            {
                var invocation;
                var keyID;

                console.log("Inside do_box_save() : noteID = " + noteID);
                console.log("newBody :" + newBody);

                this.new_note_value = newBody;					// Save the value of the tentative edit (subject to successful server update)

                var positionID = this.item_data.pos;

                // Start the body of the POST to send to the server
                var post_obj = {schema_code: this.item_data.schema_code};

                if (noteID < 0)  {	// Add NEW note
                    const insert_after = this.item_data.insert_after;   // ID of Content Item to insert after, or keyword "TOP" or "BOTTOM"

                    post_obj.category_id = this.category_id;
                    post_obj.body = newBody;
                    post_obj.insert_after = insert_after;
                    post_obj.class_name = this.item_data.class_name;
                    if (this.current_data['title'] != "")
                        post_obj.title = this.current_data['title'];        // TODO: implement a title creator, if not supplied by user

                    var url_server = "/BA/api/add_item_to_category";
                }
                else  {				    // Edit EXISTING note
                    post_obj.uri = noteID;
                    post_obj.body = newBody;
                    post_obj.title = this.current_data['title'];
                    post_obj.basename = this.current_data['basename'];
                    post_obj.class_name = this.item_data.class_name;
                    if (post_obj.basename === undefined)
                        alert("Attempting to call /BA/api/update_content_item with an undefined basename!");

                    var url_server = "/BA/api/update_content_item";
                }


                this.save_waiting = true;
                this.error = false;   // Clear possible past message

                //console.log("In 'vue-plugin-n', do_box_save().  post_obj: ", post_obj);
                ServerCommunication.contact_server(url_server, {post_obj: post_obj,
                                                                callback_fn: this.finish_save});

            },  // do_box_save()


            finish_save(success, server_payload, error_message)
            /*	Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned ID.

                Exit the editing mode.  Invoked upon a SAVE operation on an existing note.
                Restore all <input> fields to strings, using the values saved in the Vue object.
                Turn the SAVE & CANCEL buttons back into edit links
             */
            {
                var boxValue;

                console.log("Finalizing the Note save operation...");

                /* Turn the note box into its final value

                    NOTE:   new_note_value is the counterpart of this.current_data
                            old_note_value is the counterpart of this.original_data
                 */

                if (success) {          // Server reported SUCCESS
                    this.status_message = "Successful edit";
                    this.error = false;

                    console.log(`--- URI is: ${this.item_data.uri}`);

                    // If this was a new item (with the temporary negative ID),
                    // update its URI (in this Vue component) with the value assigned by the server;
                    // also, update its basename accordingly
                    if (this.item_data.uri < 0)  {
                        this.current_data.uri = server_payload;
                        console.log(`updating front-end value of 'basename' to 'notes-${server_payload}'`);
                        this.current_data.basename = `notes-${server_payload}`; // TODO: change this convention
                    }

                    // Inform the parent component of the new state of the data
                    console.log("Notes component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    boxValue = this.new_note_value;

                    // Synchronize the accepted baseline data to the current one
                    this.original_data = Object.assign({}, this.current_data);      // Clone
                }
                else  {		            // Server reported FAILURE
                    this.status_message = "FAILED SAVE. " + error_message;
                    this.error = true;
                    boxValue = this.old_note_value;         // Restore the old value
                    this.inform_component_root_of_cancel();
                    //alert(oldValue);
                }
                console.log("boxValue = " + boxValue);


                // Final wrap-up, regardless of error or success

                this.body_of_note = boxValue;   // Set the Note content (to either the new value or the restored old value)

                this.editing_mode = false;      // Exit the editing mode
                this.save_waiting = false;

                //console.log("attempting to reload mathjax just before exiting finish_save()");
                //this.reload_mathjax();    // NOT WORKING! [Presumably b/c Vue then refreshes the page from the change in this.editing_mode]

            },  // finish_save


            cancel_edit()
            // Invoked by clicking on the "CANCEL" link (only visible in editing mode)
            {
                noteID = this.item_data.uri;    // A negative value indicates a new Note

                console.log("Inside cancel_edit().  noteID = " + noteID);

                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                this.note_editor.setData(this.old_note_value);

                this.inform_component_root_of_cancel();

                this.editing_mode = false;

                // TODO: maybe destroy the CKeditor object, if there are too many on the page
                // self.destroy_editor();

                //this.reload_mathjax();    // NOT WORKING! [Presumably b/c Vue then refreshes the page from the change in this.editing_mode]
            },

            inform_component_root_of_cancel()
            // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
            {
                if (this.current_data.uri < 0) {    // A negative number indicates a new Note, by convention
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
            },



            reload_mathjax()
            /*
                See: https://docs.mathjax.org/en/v2.7-latest/advanced/dynamic.html
             */
            {
                console.log(`Re-loading the MathJax script for note ${this.item_data.uri}...`);

                var script = document.createElement("script");
                script.type = "text/javascript";
                script.src  = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS_HTML";

                //script.defer = true;            // Seems to make no difference
                //script.async = false;
                //script.innerHTML = config;      // Seems to make no difference

                document.getElementsByTagName("head")[0].appendChild(script);
                //document.head.appendChild(script);    // Apparent alternative
                //document.body.append(script);         // Presumed alternative
            },

            process_mathjax()
            /*  This is needed after editing a Note, or whenever the component gets reloaded
                See: http://docs.mathjax.org/en/v2.7-latest/advanced/typeset.html
             */
            {
                console.log("Entering process_mathjax()");

                // MathJax.Hub is the parser and typesetter
                // Because MathJax.Hub is asynchronous, add the request to a queue

                // The typeof check is used because the variable MathJax
                // might not even be declared yet, if the MathJax library hasn't loaded
                if (typeof MathJax !== 'undefined') {
                    console.log("Adding to MathJax queue");
                    MathJax.Hub.Queue(["Typeset",MathJax.Hub]);
                }
                else
                    console.log("No action taken by process_mathjax() because MathJax isn't defined");
            }

        } // END methods

    }
); // end component