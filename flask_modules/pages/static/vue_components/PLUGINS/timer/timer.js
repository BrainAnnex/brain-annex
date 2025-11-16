/*  Vue component to display and edit Content Items of type "timer" (clock timer).
    Set the desired amount of time, and the clock will count down until it reaches zero - then ring an alarm.

    Adapted from "Javascript Countdown Timer", by Jason Russo http://thescriptcenter.com (modified Jason Chan with sound).
    Alarms courtesy of https://pixabay.com/sound-effects/search/alarm%20clock%20gentle
    and https://www.zedge.net/find/alarm%20gentle

    TODO: maybe pass volume as a parameter and/or provide a control for it.
          Grey out "Reset" as appropriate
 */

Vue.component('vue-plugin-timer',
    {
        props: ['item_data', 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_data:      EXAMPLE :
                                        {"class_name":"Timer Widget",
                                        "pos":0,
                                        "ringtone":"dreamscape-alarm-clock-117680.mp3",
                                        "schema_code":"timer",
                                        "uri":"8809"
                                        }
                                      (if uri is negative, it means that it's a newly-created header, not yet registered with the server)
                                TODO: separate regular properties from control values
                                     (`class_name`, `schema_code`, `insert_after_uri`, `pos`)

            edit_mode:      A boolean indicating whether in editing mode
                            TODO: possibly add a new parameter "create_mode" that won't show the usual
                                  delete/tag/move controls

            category_id:    The URI of the Category page where this recordset is displayed (used when creating new recordsets)
            index:          The zero-based position of this Recordset on the page
            item_count:     The total number of Content Items (of all types) on the page [passed thru to the controls]
            schema_data:    A list of field names, in Schema order.
                                EXAMPLE: ["ringtone"]
         */

        template: `
            <div>	<!-- Outer container box, serving as Vue-required template root  -->

                <!-- Display in NORMAL (non-editing) mode  -->
                <div v-if="!editing_mode" class='timerShell'>

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

                        <tr style='height:80px'>
                            <td align="center" colspan="3">
                                <button @click="set_limit(false)" class="btn btn-primary btn-lg">
                                    {{button_name()}}
                                </button>

                                <button @click="timer_pause()" class="btn btn-warning" >Pause</button>

                                <button @click="reset_timer()" id="stop" class="btn btn-danger">Reset</button>
                            </td>
                        </tr>


                        <tr style='height:40px'>
                            <td align="center" colspan="3">
                                <!-- preload="none"  -->
                                <audio v-bind:id="'my_audio' + item_data.uri" controls style="display:none">
                                    <source v-bind:src="'/BA/pages/static/vue_components/PLUGINS/timer/alarms/' + current_data.audio_file" type="audio/mpeg">
                                </audio>
                                <button @click="play_audio('stop')" class='alarmButtons' style="color:red">SILENCE ALARM</button>
                                <button @click="play_audio('play')" class='alarmButtons' style="color:gray">TEST ALARM</button>
                                <br><span style="color:#999">{{current_data.audio_file}}</span><br>
                            </td>
                        </tr>

                    </tbody>
                    </table>

                </div>      <!-- End class='timerShell' -->


                <!-- Display when in EDITING MODE -->
                <div v-if="editing_mode" style="border: 1px solid #888; box-shadow: 5px 5px 10px #555; padding: 10px; background-color: #d0ffff">
                    <span style="font-size:22px"><b>TIMER WIDGET</b></span>
                    <br><br>
                    Desired ringtone <span style="color:gray">(audio filename)</span>:
                    <input type="text" size="40" v-model="current_data.audio_file">
                    <button @click="save">SAVE</button>
                    <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
                    <br><br>
                    <span style="color:gray">AVAILABLE: alarm_good_morning_song.mp3 , dreamscape-alarm-clock-117680.mp3 , gentle_alarm.mp3</span>
                </div>


                <br>

                <!--  STANDARD CONTROLS (a <SPAN> element that can be extended with extra controls),
                      EXCEPT for the "edit" control, which is provided by this Vue component itself.
                      Signals from the Vue child component "vue-controls", below,
                      get relayed to the parent of this component;
                      none get intercepted and handled here
                -->
                    <!-- OPTIONAL MORE CONTROLS to the LEFT of the standard ones would go here -->

                    <vue-controls v-bind:edit_mode="edit_mode"  v-bind:index="index"  v-bind:item_count="item_count"
                                  v-bind:controls_to_hide="['edit']"
                                  v-on="$listeners"
                    >
                    </vue-controls>

                    <!-- OPTIONAL MORE CONTROLS to the RIGHT of the standard ones would go here -->


            </div>		<!-- End of outer container -->
        `,



        // ------------------------------------   DATA   ------------------------------------
        data: function() {
            return {
                editing_mode: this.item_data.uri < 0 ? true : false,   // Negative URI means "new Item" (automatically placed in editing mode)

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                //      Note: for new Content Items, it only contains
                //              `class_name`, `schema_code`, `uri`, `insert_after_uri`, PLUS anything dynamically added by v-model during data entry
                //            For existing Content Items, it contains
                //              `class_name`, `schema_code`, `uri`, `pos`, and Content-specific fields
                current_data:   Object.assign({}, this.item_data),

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                original_data:  Object.assign({}, this.item_data),

                //audio_file: "dreamscape-alarm-clock-117680.mp3", //this.item_data.ringtone,    // See list of available files in "alarms" subfolder
                                                        // TODO: it might be good to have a default here

                show_timer: "00:00:00",                 // The timer's display

                // The following 3 are the parts of the value that the alarm gets set to
                hrs: 0,
                min: 0,
                sec: 0,

                // The following 3 are the parts of the display
                show_hrs: 0,
                show_min: 0,
                show_sec: 0,

                stopped: true,              // Boolean indicating whether timer is in stopped state (initially, and upon reaching final time)
                pause: false,               // Boolean indicating whether timer is in pause mode

                timeup_message: "TIME UP",	// Time-is-up message (shown in lieu of the time display)

                parselimit: 1,              // Number of seconds to the alarm; the alarm rings when parselimit gets down to 1

                st: 0                       // Timer ID from JavaScript setTimeout() method invocation
            }
        },



        // --------------------------   METHODS   --------------------------
        methods: {
            button_name()
            // Pick a name for the Start/Resume button
            {
                if (this.stopped)
                    return "Start";

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

                var audio = document.getElementById("my_audio"+ this.item_data.uri);    // HTML DOM Audio Object.  It inherits from HTMLMediaElement
                                                                    // https://www.w3schools.com/jsref/dom_obj_audio.asp

                if (task == 'play')  {
                    audio.volume = 0.15;    // Play at low volume (note: 1.0 = 100% volume)
                    console.log(`    volume = "${audio.volume}"`);
                    audio.play();
                }

                if (task == 'stop')
                    audio.pause();
                    audio.currentTime = 0;  // Reset the current playback position to the start
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

                    if (!strtstop)  {
                        this.pause = false;     // Take out of paused state
                        this.stopped = false;
                    }
                }
                else  {
                    var parselimit_arr = [this.hrs, this.min, this.sec];
                    if (!strtstop)
                        this.stopped = false;
                }

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
                    this.st = setTimeout(this.begin_timer, 1000);
                }
            },


            begin_timer()
            // Handler function for JavaScript's setTimeout()
            {
                //console.log(`In begin_timer(): this.parselimit = ${this.parselimit}`);

                if (this.parselimit==1) {       // It's time to ring the alarm
                    //console.log("    ringing alarm...");
                    this.show_timer = this.timeup_message;	    // Show our standard time-is-up message

                    this.play_audio("play");

                    this.pause = false;         // Clear the paused state (if applicable)
                    this.stopped = true;

                    return;
                }
                else {
                    //console.log("    decreasing this.parselimit");
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

                this.st = setTimeout(this.begin_timer, 1000);    // 1-sec timeout
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
                this.stopped = true;
            },


            /*
                --------  SERVER CALLS  --------
             */

            save()
            // Conclude an EDIT operation.  TODO: maybe save/cancel should be a sub-component shared among various plugins?
            {
                // Start the body of the POST to send to the server
                var post_obj = {class_name: this.item_data.class_name};

                if (this.item_data.uri < 0)  {     // Negative uri is a convention indicating a new Content Item to create,
                     // Needed for NEW Content Items
                     post_obj.category_id = this.category_id;
                     post_obj.insert_after_uri = this.item_data.insert_after_uri;       // URI of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                     post_obj.insert_after_class = this.item_data.insert_after_class;   // Class of Content Item to insert after

                     url_server_api = `/BA/api/add_item_to_category`;       // URL to communicate with the server's endpoint
                }
                else {   // Update an EXISTING Content Item
                    post_obj.uri = this.item_data.uri;

                    url_server_api = `/BA/api/update_content_item`;        // URL to communicate with the server's endpoint
                }

                //console.log("this.current_data: ");
                //console.log(this.current_data);

                // Enforce required field
                if ('audio_file' in this.current_data) // For new records, this attribute gets dynamically added by v-model during data entry
                    post_obj.audio_file = this.current_data.audio_file;
                else  {
                    alert("Cannot save an empty audio file");
                    return;
                }

                console.log(`In 'vue-plugin-timer', save().  About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server.  TODO: maybe switch to a JSON-based web app
                ServerCommunication.contact_server(url_server_api,
                            {method: "POST",
                             data_obj: post_obj,
                             json_encode_send: false,
                             callback_fn: this.finish_save
                            });

                this.waiting = true;        // Entering a waiting-for-server mode
                this.error = false;         // Clear any error from the previous operation
                this.status_message = "";   // Clear any message from the previous operation
             }, // save


            finish_save(success, server_payload, error_message)
            /*  Callback function to wrap up the action of save() upon getting a response from the server.
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned URI
             */
            {
                console.log("Finalizing the Timer Widget save() operation...");
                if (success)  {     // Server reported SUCCESS
                    //console.log("    server call was successful");
                    this.status_message = `Successful edit`;

                    // If this was a new item (with the temporary negative URI), update its URI with the value assigned by the server
                    if (this.item_data.uri < 0)
                        this.current_data.uri = server_payload;

                    // Inform the parent component of the new state of the data
                    console.log("Timer Widget component sending `updated-item` signal to its parent");
                    this.$emit('updated-item', this.current_data);

                    // Synchronize the baseline data to the finalized current data
                    this.original_data = Object.assign({}, this.current_data);  // Clone
                }
                else  {             // Server reported FAILURE
                    this.status_message = `FAILED edit`;
                    this.error = true;
                    this.cancel_edit();         // Restore the data to how it was prior to the failed changes. TODO: maybe leave in edit mode?
                }

                // Final wrap-up, regardless of error or success
                this.waiting = false;           // Make a note that the asynchronous operation has come to an end
                this.editing_mode = false;      // Exit the editing mode

            }, // finish_save


            cancel_edit()
            {
                // Restore the data to how it was prior to the aborted changes
                this.current_data = Object.assign({}, this.original_data);  // Clone from original_data

                if (this.current_data.uri < 0) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Timer Widget sending `cancel-edit` signal to its parent");
                    this.$emit('cancel-edit');
                }
                else
                    this.editing_mode = false;      // Exit the editing mode

            } // cancel_edit


        }  // METHODS
    }
); // end component