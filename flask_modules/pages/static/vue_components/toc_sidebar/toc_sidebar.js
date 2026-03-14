/*  Left sidebar (with the page's Table of Contents)
    Used by page_viewer.htm and by search.htm
    Show clickable entries the page headers, and for the Content Items
 */

Vue.component('vue-toc-sidebar',
    {
        props: {

            /*  Array containing item-data objects.  EXAMPLE:
                        [{pos:0,"entity_id":"5",schema_code:"h",text:"GENERAL METHODS", class_name: "Header"},
                         {pos:50,"entity_id":"8",schema_code:"i",caption:"some title",basename:"mypix",suffix:"png", class_name: "Image"}
                        ]
             */
            content_array: {
                required: true
            },

            /* Flag indicating whether this sidebar is to be shown */
            show_left_sidebar : {
                type: Boolean,
                required: true
            },

            /* Flag indicating whether the "Details?" checkbox is to be included */
            show_hide_details:  {
                type: Boolean,
                default: true
            }
        },



        template: `
            <div>

                <!--
                    EXPANDED (normal) version of the left sidebar
                  -->
                <div v-show='show_left_sidebar' class='sidebar-toc-left  sidebar-left-expanded'>

                    <!--Non-scrollable "stick" portion at the top -->
                    <p class="toc-header">

                        <!-- Icon to collapse the sidebar -->
                        <img @click='set_sidebar_state(false)'  src='/BA/pages/static/graphics/thin_left_arrow_32.png' align='right'
                             class='clickable-icon'
                             title='Click to collapse sidebar' alt='Click to collapse sidebar'>

                        <!-- Page navigation section -->
                        <a href='#' style='font-size:14px; font-weight:bold'>TOP</a>
                            <span v-if="show_hide_details">
                                <input type="checkbox" v-model="expand_categories" style='margin-left:8px'>
                                Details?
                            </span>
                    </p>


                    <div class="page-toc">
                        <template v-for="item in content_array">
                            <p v-if="item.schema_code == 'h'" class="header">
                                <br><a v-bind:href="'#h_' + item.entity_id">{{item.text}}</a><br>
                            </p>

                            <template v-if="expand_categories">
                                <!-- Case-by-case, based on the type of Content Item -->
                                <p v-if="item.schema_code == 'cd'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" v-bind:title="item.name">{{item.name}}</a>
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code == 'i'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" v-bind:title="item.caption">{{item.caption}}</a>
                                    <img src='/BA/pages/static/graphics/image_14_1814111.png' title="image" alt="image">
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code == 'd'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" v-bind:title="item.caption">{{item.caption}}</a>
                                    <img src='/BA/pages/static/graphics/document_14_2124302.png' title="document" alt="document">
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code == 'n' && item.title">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" v-bind:title="item.caption">{{item.title}}</a>
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code == 'rs' && item.class">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" v-bind:title="item.caption">{{item.class}}</a>
                                    <img src='/BA/pages/static/graphics/tabular_16_9040670.png' title="recordset" alt="recordset">
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code == 'sl' && item.name">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id" title="Bookmark (site link)">{{item.name}}</a>
                                    <img src='/BA/pages/static/graphics/16_bookmark_1904655.png' title="bookmark" alt="bookmark">
                                    <br>
                                </p>

                                <p v-else-if="item.schema_code != 'h'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.entity_id">
                                        {{item.class_name}}
                                    </a>
                                    <img src='/BA/pages/static/graphics/13_database_record.png'>
                                </p>
                            </template>

                        </template>

                        <br>
                        <a href='#BOTTOM' style='font-size:14px; font-weight:bold'>BOTTOM</a>
                        <br><br><br>

                    </div>      <!-- END of page-toc -->

                </div>		<!-- END OF class 'sidebar-left-expanded' -->


                <!--
                    COLLAPSED version of the left sidebar
                  -->
                <div v-show='!show_left_sidebar' class='sidebar-toc-left  sidebar-left-collapsed'>
                    <img @click='set_sidebar_state(true)' src='/BA/pages/static/graphics/thin_right_arrow_32.png' align='left'
                         class='clickable-icon'
                         title='Click to expand sidebar' alt='Click to expand sidebar'>
                </div> 	 <!-- END of Collapsed version of sidebar-left -->


            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                expand_categories: true     // Whether to show details of some Content Items under the various headers
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            set_sidebar_state(state)
            {
                console.log("Component 'vue-toc-sidebar' sending `adjust-left-sidebar` signal to its parent, with parameter: ", state);
                this.$emit('adjust-left-sidebar', state);
            }
        }  // METHODS

    }
); // end component