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
                                <button @click="set_limit(0)" class="btn btn-primary btn-lg">Start</button>

                                <button @click="timer_pause()" class="btn btn-warning" >Pause</button>

                                <button @click="rset_tmr()" id="stop" class="btn btn-danger">Reset</button>
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
                show_timer: "00:00:00",

                hrs: 0,
                min: 0,
                sec: 0,

                pause: false,               // Boolean indicating whether timer is in pause mode

                timeup_message: "TIME UP",	// Time-is-up message (shown in lieu of the time display)

                parselimit:0,

                st:0,
                limit:null,
                curhour:null,
                curmin:null,
                cursec:null
            }
        },



        // ------------------------------   METHODS   ------------------------------
        methods: {
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
                console.log(`In add_time_clock(): units = "${units}"`);

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
                console.log(`In sub_time_clock(): units = "${units}"`);

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
            // strtstop is either 0 or 1
            {
                console.log(`In set_limit(): strtstop = "${strtstop}"`);

                // Prevent multiple settimeouts
                if (this.st)
                    clearTimeout(this.st);

                if (this.pause == 1)    // If in a paused state
                    limit = this.show_timer;
                else
                    limit = this.format(this.hrs) + ":" + this.format(this.min) + ":" + this.format(this.sec);
                    //limit=document.getElementById("hours").value + ":" + document.getElementById("min").value + ":" + document.getElementById("sec").value;

                console.log(`    limit = "${limit}"`);      // EXAMPLE: "00:00:05"

                parselimit = limit.split(":");
                // Convert to seconds
                parselimit = parselimit[0]*3600 + parselimit[1]*60 + parselimit[2];

                this.parselimit = parseInt(parselimit);  // Convert to integer

                // exit if timer wasn't set
                console.log(`    this.parselimit = ${this.parselimit}`);    // EXAMPLE: 5
                if (this.parselimit <= 0)
                    return;

                if (strtstop == 1)  {
                    console.log(`    calling clearTimeout()`);
                    clearTimeout(this.st);
                }
                else  {
                    console.log(`    calling setTimeout()`);
                    this.st = setTimeout(this.begintimer, 1000);
                }
            },


            begintimer()
            {
                console.log(`In begintimer(): this.parselimit = ${this.parselimit}`);

                if (this.parselimit==1) {
                    console.log("    ringing alarm...");
                    //ding ding ding
                    this.show_timer = this.timeup_message;	    // Show our standard time-is-up message

                    var x = document.getElementById("my_audio");

                    x.play();

                    //$(".my_audio").trigger('play');
                    //alert(timeup_message);
                    return;
                }
                else {
                    console.log("    decreasing this.parselimit");
                    this.parselimit-=1;

                    this.curhour = Math.floor(this.parselimit/3600);

                    //alert(parselimit)
                    /* 	if greater than an hour divide by
                        60 but subtract the hours */
                    if (this.parselimit > 3600) {
                        //first convert hours back into seconds
                        this.curmin = this.curhour * 3600;
                        //subtract that from total to get minutes left.
                        this.curmin = this.parselimit - this.curmin;
                        this.curmin = Math.floor(this.curmin/60);
                        //alert(curmin);
                    }
                    else {
                        this.curmin = Math.floor(this.parselimit/60);
                    }
                    this.cursec = this.parselimit%60;
                }

                this.curhour = this.format(this.curhour);   // Convert to zero-padded 2-char string

                this.curmin += "";      // Convert to string
                if(this.curmin.length == 1 || this.curmin==9) {
                    this.curmin = "0" + this.curmin;
                }
                this.cursec += "";      // Convert to string
                //alert(cursec);
                if(this.cursec.length == 1 || this.cursec==9)
                    this.cursec = "0" + this.cursec;

                console.log(`    this.curhour = ${this.curhour} | this.curmin = ${this.curmin} | this.cursec = ${this.cursec}`);
                this.curtime = this.curhour + ":" + this.curmin + ":" + this.cursec;

                //alert(document.getElementById("show_timer").innerHTML);
                this.show_timer = this.curtime;

                this.st = setTimeout(this.begintimer, 1000);
            },



            timer_pause()
            // Set the timer in a paused state
            {
                this.set_limit('1');
                this.pause = true;           // Set in paused state
            },



            rset_tmr()
            // Reset the timer
            {
                this.show_timer = "00:00:00";
                this.pause = false;         // Clear the paused state (if applicable)
            }

        }  // METHODS
    }
); // end component