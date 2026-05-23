/*  Vue component
 */

Vue.component('vue-database-summary',
    {
        props: ['all_database_labels'],

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

                <h2>{{all_labels.length}} <i>labels</i> found in graph database:</h2>

                <div v-for="(label, index) in all_labels" >
                    Value: {{my_var}}<br>

                    <button @click="my_var=true">CLICK ME</button>

                    *
                    <img @click="foo_schema(index)" class="clickable-icon"
                                src="/BA/pages/static/graphics/info_16.png"
                                title="Show info" alt="Show info">
                    &nbsp;
                    <img @click="my_var=!my_var" class="clickable-icon"
                                src="/BA/pages/static/graphics/tabular_16_9040670.png"
                                title="Show sample node (record)" alt="Show sample node (record)">
                    <br>

                    <div v-if="show_schema_arr[index]" style="border: 1px solid gray; margin-bottom:10px">
                        YO schema!
                    </div>

                </div>

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                all_labels: this.all_database_labels,
                my_var: false,
                show_schema_arr: Array(this.all_database_labels.length).fill(false),
                show_sample_arr: Array(this.all_database_labels.length).fill(false)
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {
            foo_schema(index)
            {
                console.log(index);
                Vue.set(this.show_schema_arr, index, !this.show_schema_arr[index]);
            }

        }  // METHODS

    }
); // end component