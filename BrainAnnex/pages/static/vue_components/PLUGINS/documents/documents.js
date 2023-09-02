/*  Vue component to display and edit Content Items of type "d" (Documents)
 */

Vue.component('vue-plugin-d',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count'],
        /*  item_data:  EXAMPLE: {"basename": "test", "caption": "My first document", "class_name": "Documents",
                                  "item_id": 4849, "pos": 0, "schema_code": "d", "suffix": "txt"}
                                 (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)

            allow_editing:  A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this document is displayed (used when creating new documents)
            index:          The zero-based position of this Document on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <!-- Document container -->
            <div class='doc'>
                <img src="/BA/pages/static/graphics/document_48_8168668.png" style="float: left; margin-right: 5px">
                <span style='font-weight:bold; font-size:12px'>&ldquo;{{item_data.caption}}&rdquo;</span><br><br>
                <a href v-bind:href="document_url(item_data)"
                        v-bind:title="item_data.caption" v-bind:alt="item_data.caption"
                        target="_blank"
                >
                    {{item_data.basename}}.{{item_data.suffix}}
                </a>
                <br><br>
            </div>		<!-- End of Document container -->


            <!--  STANDARD CONTROLS
                  (signals from them get relayed to the parent of this component, but some get handled here)
                  Intercept the following signal from child component:
                        v-on:edit-content-item
            -->
            <vue-controls v-bind:allow_editing="allow_editing"  v-bind:index="index"  v-bind:item_count="item_count"
                          v-on="$listeners"
                          v-on:edit-content-item="edit_content_item(item_data)">
            </vue-controls>

            \n</div>\n		<!-- End of outer container box -->
            `,


        data: function() {
            return {
                // This object contains the values bound to the editing field, cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data: Object.assign({}, this.item_data),

                // Clone, used to restore the data in case of a Cancel or failed save
                original_data: Object.assign({}, this.item_data)
            }
        }, // data


        // ------------------------------   METHODS   ------------------------------
        methods: {
            document_url(item_data)
            // Return the URL of the full documents
            {
                return '/BA/api/simple/serve_media/' + item_data.item_id;           // Invoke the file server
             },


            edit_content_item(item)
            {
                console.log(`Documents component received signal to edit content item of type '${item.schema_code}' , id ${item.item_id}`);
                alert("Editing of Documents not yet implemented");
            }

        }

    }
); // end component