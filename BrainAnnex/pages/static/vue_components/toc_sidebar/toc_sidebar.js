/*  Left sidebar (with the page's Table of Contents)
    Used by page_viewer.htm and search.htm
    Show the headers, and varying details of some of Content Items under them
 */

Vue.component('vue-toc-sidebar',
    {
        props: {

            /*  Array containing item-data objects.  EXAMPLE:
                                [{pos:0,"uri":5,schema_code:"h",text:"GENERAL METHODS", class_name: "Headers"},
                                 {pos:50,"uri":8,schema_code:"i",caption:"some title",basename:"mypix",suffix:"png", class_name: "Images"}
                                ]
             */
            content_array: {
            },

            /* Flag indicating whether this sidebar is to be shown */
            show_left_sidebar : {
            },

            /* Flag indicating whether the "Details?" checkbox is to be shown */
            show_hide_details:  {
                type: Boolean,
                default: true
            }
        },

        /*  content_array:  Array containing item-data objects.  EXAMPLE:
                            [{pos:0,"uri":5,schema_code:"h",text:"GENERAL METHODS", class_name: "Headers"},
                             {pos:50,"uri":8,schema_code:"i",caption:"some title",basename:"mypix",suffix:"png", class_name: "Images"}
                            ]
            show_left_sidebar: Flag indicating whether this sidebar is to be shown
         */

        template: `
            <div>

                <!--
                    EXPANDED (normal) version of the left sidebar
                  -->
                <div v-show='show_left_sidebar' class='sidebar-left'>

                    <img @click='set_sidebar_state(false)'  src='/BA/pages/static/graphics/thin_left_arrow_32.png' align='right'
                         class='clickable-icon'
                         title='Click to collapse sidebar' alt='Click to collapse sidebar'>

                    <!-- Page navigation section -->
                    <a href='#' style='font-size:14px; font-weight:bold'>TOP</a>
                        <span v-if="show_hide_details">
                            <input type="checkbox" v-model="expand_categories" style='margin-left:8px'>
                            Details?
                        </span>
                    <br>

                    <div class="page-toc">
                        <template v-for="item in content_array">
                            <p v-if="item.schema_code == 'h'" class="header">
                                <br><a v-bind:href="'#h_' + item.uri">{{item.text}}</a><br>
                            </p>

                            <template v-if="expand_categories">
                                <!-- Case-by-case, based on the type of Content Item -->
                                <p v-if="item.schema_code == 'cd'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.uri" v-bind:title="item.name">{{item.name}}</a>
                                    <br>
                                </p>

                                <p v-if="item.schema_code == 'i'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.uri" v-bind:title="item.caption">{{item.caption}}</a>
                                    <img src='/BA/pages/static/graphics/image_14_1814111.png'>
                                    <br>
                                </p>

                                <p v-if="item.schema_code == 'd'">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.uri" v-bind:title="item.caption">{{item.caption}}</a>
                                    <img src='/BA/pages/static/graphics/document_14_2124302.png'>
                                    <br>
                                </p>

                                <p v-if="item.schema_code == 'n' && item.title">&nbsp; &diams;
                                    <a v-bind:href="'#' + item.schema_code + '_' + item.uri" v-bind:title="item.caption">{{item.title}}</a>
                                    <br>
                                </p>
                            </template>

                        </template>
                    </div>      <!-- END of page-toc -->

                    <br><a href='#BOTTOM' style='font-size:14px; font-weight:bold'>BOTTOM</a>

                    <br><br>

                </div>		<!-- END OF class 'sidebar-left' -->


                <!--
                    COLLAPSED version of the left sidebar
                  -->
                <div v-show='!show_left_sidebar' class='sidebar-left-collapsed'>
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