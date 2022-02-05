Vue.component('vue-category-navbox',
    {
        props: ['category_name', 'subcategories', 'all_categories'],
        /*  category_name:
            subcategories:
            all_categories:
         */

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <span class="sidebox-section">PINNED</span>
            <br>&bull; <a href='/BA/pages/viewer/TBA' title="TBA">TBA</a>

            <hr>

            <span class="sidebox-section">RELATED</span>
            <br>
            <!-- All parent categories -->
            <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Parent Categories:</span>
            <br>
            TBA
            <br><br>

            <!-- The current category -->
            <div style='color:brown; font-weight:bold; font-size:12px; background-color:#F3F3F3; text-align: center'>
                {{category_name}}
            </div>

            <br>

            <!-- All sibling categories -->
            <div style='border:1px solid #AAA; padding:2px'>
                <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Sibling Categories:</span>
                <br>TBA
            </div>

            <br>

            <!-- All subcategories -->
            <span style='color:#BBBBBB; font-size:8px; font-style:italic'>Sub-categories:</span>
            <template v-for="category in subcategories">
                <br>&deg; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
            </template>

            <hr>

            <!-- All categories -->
            <span class="sidebox-section">ALL</span>
            <br>
            <template v-for="category in all_categories">
                <br>&diams; <a v-bind:href="'/BA/pages/viewer/' + category['id']">{{category.name}}</a>
            </template>
            <br>
            <br>

            </div>		<!-- End of outer container -->
            `,



        data: function() {
            return {
                my_count: 0,
                nickname: this.some_data_a
            }
        },



        watch: {
            /*
            some_data_b() {
                console.log('The prop `some_data_b` has changed!');
            }
            */
        },



        mounted() {
           //console.log('The component is now mounted');
        },



        // ----------------  COMPUTED  -----------------
        computed: {
            example() {
                return this.my_count+ 10;
            }
        },



        // ----------------  METHODS  -----------------
        methods: {
            foo: function () {
                alert("In foo. some_data_a= " + this.some_data_a);
            }

        }  // METHODS

    }
); // end component