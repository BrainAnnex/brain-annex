Vue.component('vue-some-name',  <!-- NOTE:  Only lower cases in component names! -->
    {
        props: ['some_data_a', 'some_data_b'],  <!-- NOTE:  Only lower cases in props names! -->
        /*  some_data_a:
            some_data_b:
         */

        my_optional_component_metadata: 123,   <!-- Available thru this.$options.metadata -->

        template: `
            <div>  <!-- Outer container, serving as Vue-required template root.  OK to use a <section> instead -->

            <button @click="count++">{{ count }}</button>
            <input type='text' v-model="nickname" placeholder="Specify nickname">

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