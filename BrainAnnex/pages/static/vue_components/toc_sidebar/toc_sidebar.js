/*  Left sidebar (with the page's Table of Contents)
    Used in page_viewer.htm
 */

Vue.component('vue-toc-sidebar',
    {
        props: ['content_array', 'show_left_sidebar'],
        /*  content_array:  Array containing item-data objects.  EXAMPLE:
                            [{pos:0,"item_id":5,schema_code:"h",text:"GENERAL METHODS", class_name: "Headers"},
                             {pos:50,"item_id":8,schema_code:"i",basename:"mypix",suffix:"png", class_name: "Images"}
                            ]
            show_left_sidebar
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
                        <span style='color:#AAA; margin-left:10px; font-size:10px;'>PAGE CONTENTS</span>
                    <br>

                    <div class="page-toc">
                        <template v-for="item in content_array">
                            <p v-if="item.schema_code == 'h'" class="header">
                                <br><a v-bind:href="'#h_' + item.item_id">{{item.text}}</a><br>
                            </p>
                            <p v-if="item.schema_code == 'cd'">&nbsp; &diams;
                                <a v-bind:href="'#' + item.schema_code + '_' + item.item_id" v-bind:title="item.name">{{item.name}}</a>
                                <br>
                            </p>
                        </template>
                    </div>      <!-- END of page-toc -->

                    <br><a href='#BOTTOM' style='font-size:14px; font-weight:bold'>BOTTOM</a>

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