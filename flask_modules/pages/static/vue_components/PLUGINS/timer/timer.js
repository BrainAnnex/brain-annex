/*  Vue component to display and edit Content Items of type "timer" (clock timer)
 */

Vue.component('vue-plugin-timer',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_data:      EXAMPLE :    {class_name:"Recordset",
                                          class:"YouTube Channel"
                                          n_group:10,
                                          order_by:"name",
                                          pos:100,
                                          schema_code:"rs",
                                          uri:"rs-7"
                                         }
                                      (if uri is negative, it means that it's a newly-created header, not yet registered with the server)
                            TODO: take "pos" and "class_name" out of item_data !
            edit_mode:      A boolean indicating whether in editing mode
            category_id:    The URI of the Category page where this recordset is displayed (used when creating new recordsets)
            index:          The zero-based position of this Recordset on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names (for the Recordset entity, not its records!), in Schema order.
                                EXAMPLE: ["class", "order_by", "clause", "n_group", "caption"]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <div id="set_timer" class='timerShell'>

                    <table border="0" class='timerTable' width="220px">
                    <tbody>

                        <tr>
                            <td align="center" colspan="3" height="25" class="simple-timer">
                                <span class='timeDisplay'>{{show_timer}}</span>
                            </td>
                        </tr>

                        <tr class="caption">
                            <td align="center">Hrs</td>
                            <td align="center">Min</td>
                            <td align="center">Sec</td>
                        </tr>

                        <tr class="inputNumbers">
                            <td align="right">
                                <input type="text" v-model="hrs" id="hours" maxlength="2" size="1"> :
                            </td>
                            <td align="right">
                                <input type="text" v-model="min" id="min" maxlength="2" size="1"> :
                            </td>
                            <td align="center">
                                <input type="text" v-model="sec" id="sec" maxlength="2" size="1">
                            </td>
                        </tr>

                        <tr>
                        <td align="center">
                                <img @click="add_time_clock('hrs')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/plus_24_173078.png">
                                <img @click="sub_time_clock('hrs')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/minus_24_173056.png">
                            </td>
                            <td align="center">
                                <img @click="add_time_clock('min')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/plus_24_173078.png">
                                <img @click="sub_time_clock('min')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/minus_24_173056.png">
                            </td>
                            <td align="center">
                                <img @click="add_time_clock('sec')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/plus_24_173078.png">
                                <img @click="sub_time_clock('sec')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/minus_24_173056.png">
                            </td>
                        </tr>

                        <tr style='height:100px'>
                            <td align="center" colspan="3">
                                <button @click="set_limit(false)" class="btn btn-primary btn-lg">
                                    {{button_name()}}
                                </button>

                                <button @click="timer_pause()" class="btn btn-warning" >Pause</button>

                                <button @click="reset_timer()" id="stop" class="btn btn-danger">Reset</button>
                            </td>
                        </tr>
                    </tbody>
                    </table>

                    <!-- preload="none"  -->
                    <audio id="my_audio" controls style="display:none" >
                        <source src="/BA/pages/static/vue_components/PLUGINS/timer/alarm_ringing.mp3" type="audio/mpeg">
                    </audio>
                    <button @click="play_audio('stop')" class='alarmButtons' style="color:red">SILENCE ALARM</button>
                    <button @click="play_audio('play')" class='alarmButtons' style="color:gray">TEST ALARM</button>

                </div>      <!-- End class='timerShell' -->

            </div>		<!-- End of outer container -->
        `,



        // ----------------  DATA  -----------------
        data: function() {
            return {
                show_timer: "00:00:00",     // The timer's display

                // The following 3 are the parts of the value that the alarm gets set to
                hrs: 0,
                min: 0,
                sec: 0,

                // The following 3 are the parts of the display
                show_hrs: 0,
                show_min: 0,
                show_sec: 0,


                pause: false,               // Boolean indicating whether timer is in pause mode

                timeup_message: "TIME UP",	// Time-is-up message (shown in lieu of the time display)

                parselimit: 1,              // Number of seconds to the alarm; the alarm rings when parselimit gets down to 1

                st:0,
                limit:null
            }
        },



        // ------------------------------   METHODS   ------------------------------
        methods: {
            button_name()
            {
                if (this.pause)
                    return "RESUME!";

                return "Start";
            },

            format(num)
            // Convert the given integer value to zero-padded 2-char string
            {
                if (num >= 10)
                    return num.toString();  // Convert to string

                return "0" + num;           // The concatenation forces a conversion to string
            },



            play_audio(task)
            // Play or Pause the alarm, depending on whether `task` is "play" or "stop"
            {
                console.log(`In play_audio(): task = "${task}"`);

                var x = document.getElementById("my_audio");    // Audio object

                if (task == 'play')  {
                    //alert("about to play alarm. x = " + x);
                    x.play();
                }
                if (task == 'stop')  {
                    x.pause();
                }
            },



            add_time_clock(units)
            /*
                units: Either 'hrs', 'min' or 'sec'
             */
            {
                //console.log(`In add_time_clock(): units = "${units}"`);

                if (units == "hrs")
                    this.hrs = this.increment_time(this.hrs, 23);
                else if (units == "min")
                    this.min = this.increment_time(this.min, 59);
                else
                    this.sec = this.increment_time(this.sec, 59);
            },

            sub_time_clock(units)
            /*
                units: Either 'hrs', 'min' or 'sec'
             */
            {
                //console.log(`In sub_time_clock(): units = "${units}"`);

                if (units == "hrs")
                    this.hrs = this.decrement_time(this.hrs, 23);
                else if (units == "min")
                    this.min = this.decrement_time(this.min, 59);
                else
                    this.sec = this.decrement_time(this.sec, 59);
            },

            increment_time(num, max)  {
                if (num+1 > max)
                    return 0;

                return num+1;
            },

            decrement_time(num, max)  {
                if (num == 0)
                    return 0;       // return max;

                return num-1;
            },



            set_limit(strtstop)
            // Invoked by clicking on the Start/Resume button, as well as by clicking on the Pause button
            // strtstop is a boolean, indicating whether the timer is being stopped
            {
                console.log(`In set_limit(): strtstop = ${strtstop}`);

                // Prevent multiple settimeouts
                if (this.st)
                    clearTimeout(this.st);

                if (this.pause)  {  // If in a paused state
                    limit = this.show_timer;
                    console.log(`    limit = "${limit}" [NO LONGER USED]`);      // EXAMPLE: "00:00:05"
                    var parselimit_arr = [this.show_hrs, this.show_min, this.show_sec];

                    if (!strtstop)
                        this.pause = false;     // Take out of paused state
                }
                else
                    var parselimit_arr = [this.hrs, this.min, this.sec];

                console.log(`    parselimit_arr = ${parselimit_arr}`);      // EXAMPLE: [1, 23, 40]


                // Convert to seconds
                this.parselimit = parselimit_arr[0]*3600 + parselimit_arr[1]*60 + parselimit_arr[2];   // TODO: in some cases, this could be NaN !
                console.log(`    this.parselimit = ${this.parselimit}`);    // EXAMPLE: 105
                
                // Exit if timer wasn't set
                if (this.parselimit <= 0)
                    return;

                if (strtstop)  {
                    console.log(`    calling clearTimeout()`);
                    clearTimeout(this.st);
                }
                else  {
                    console.log(`    calling setTimeout()`);
                    this.st = setTimeout(this.begintimer, 1000);
                }
            },


            begintimer()
            // Handler function for JavaScript's setTimeout()
            {
                console.log(`In begintimer(): this.parselimit = ${this.parselimit}`);

                if (this.parselimit==1) {
                    console.log("    ringing alarm...");
                    //ding ding ding
                    this.show_timer = this.timeup_message;	    // Show our standard time-is-up message

                    var x = document.getElementById("my_audio");

                    x.play();

                    this.pause = false;         // Clear the paused state (if applicable)  [TODO: experimental]

                    //alert(timeup_message);
                    return;
                }
                else {
                    console.log("    decreasing this.parselimit");
                    this.parselimit-=1;

                    // Asseble the 3 parts of what is shown in the display
                    var curhour = Math.floor(this.parselimit/3600);
                    var curmin;
                    var cursec;

                    //alert(parselimit)
                    /* 	if greater than an hour divide by
                        60 but subtract the hours */
                    if (this.parselimit > 3600) {
                        //first convert hours back into seconds
                        curmin = curhour * 3600;
                        //subtract that from total to get minutes left.
                        curmin = this.parselimit - curmin;
                        curmin = Math.floor(curmin/60);
                        //alert(curmin);
                    }
                    else {
                        curmin = Math.floor(this.parselimit/60);
                    }
                    cursec = this.parselimit % 60;
                }

                //console.log(`    curhour = ${curhour} | curmin = ${curmin} | cursec = ${cursec}`);

                this.show_hrs = curhour;
                this.show_min = curmin;
                this.show_sec = cursec;

                // Format as 3 padded groups of characters, separated by ":"
                this.show_timer = this.format(this.show_hrs) + ":" + this.format(this.show_min) + ":" + this.format(this.show_sec);

                this.st = setTimeout(this.begintimer, 1000);    // 1-sec timeout
            },



            timer_pause()
            // Set the timer in a paused state
            {
                this.set_limit(true);
                this.pause = true;           // Set in paused state
            },



            reset_timer()
            // Reset the timer
            {
                this.show_timer = "00:00:00";
                this.pause = false;         // Clear the paused state (if applicable)
            }

        }  // METHODS
    }
); // end component