/*  MIT License.  Copyright (c) 2021 Julian A. West
    This file is part of the "Brain Annex" project (https://BrainAnnex.org)
 */

Vue.component('vue-plugin-i',
    {
        props: ['item_data', 'allow_editing', 'category_id', 'index', 'item_count'],
        /*  item_data:  EXAMPLE: {"item_id":52,"pos":10,"schema_code":"i","basename":"my pic","suffix":"jpg",
                                                    "caption":"my 1st pic", width:450, height:760}
                                 (if item_id is -1, it means that it's a newly-created header, not yet registered with the server)
            index:      the zero-based position of the Record on the page
            item_count: the total number of Content Items (of all types) on the page
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

            <a class='i-image-link' v-bind:href="image_url(item_data)" target="_blank">
                <img v-bind:src="image_url_thumb(item_data)">
            </a>
            <template v-if="'caption' in item_data"><br><span class='i-caption'>{{item_data.caption}}</span></template>

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
            image_url(item_data)
            // Return the URL of the full image
            {
                return '/BA/api/simple/serve_media/' + item_data.item_id;           // Invoke the file server
             },

            image_url_thumb(item_data)
            // Return the URL of the thumbnail
            {
                return '/BA/api/simple/serve_media/' + item_data.item_id + '/th';    // Invoke the file server, with the thumbnail option
             },

            edit_content_item(item)
            {
                console.log(`Image component received signal to edit content item of type '${item.schema_code}' , id ${item.item_id}`);
                alert("Editing of Images not yet implemented");
            }

        }

    }
); // end component