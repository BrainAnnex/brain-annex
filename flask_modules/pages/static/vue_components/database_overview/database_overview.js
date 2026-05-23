/*  Vue component
 */

Vue.component('vue-database-summary',
    {
        props: ['all_database_labels'],

        template: `
            <div>	<!-- Outer container, serving as Vue-required template root  -->

                Value: {{my_var}}<br>

                <button @click="my_var=true">CLICK ME</button>

            </div>		<!-- End of outer container -->
            `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                my_var: false
            }
        }, // data




        // ------------------------------------   METHODS   ------------------------------------
        methods: {


        }  // METHODS

    }
); // end component