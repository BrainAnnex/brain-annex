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
        props: ['item_fields', 'item_metadata',
                 'edit_mode', 'category_id', 'index', 'item_count', 'schema_data'],
        /*  item_fields:    An object with the editable properties of this Header item.
                                EXAMPLE: {"ringtone":"dreamscape-alarm-clock-117680.mp3"}

            item_metadata:  An object with the metadata of this Header item.
                                For a newly-created Content Item, not yet registered with the server,
                                the value of `entity_id` will be a negative number (unique on the page),
                                and there will be the additional keys `insert_after_uri` and `insert_after_class`
                                EXAMPLE of existing Timer Widget:
                                        {"class_name":"Timer Widget",
                                        "pos":0,
                                        "schema_code":"timer",
                                        "entity_id":"8809"
                                        }

            edit_mode:      A boolean indicating whether in editing mode
                            TODO: possibly add a new parameter "create_mode" that won't show the usual
                                  delete/tag/move controls

            category_id:    The entity_id of the Category page where this recordset is displayed (used when creating new recordsets)
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
                            <td align="right">Min</td>
                            <td>&nbsp;</td>
                            <td align="center">Sec</td>
                        </tr>

                        <tr class="inputNumbers">
                            <td align="right">
                                <input type="text" v-model="min" id="min" maxlength="2" size="1">
                            </td>
                            <td align="center">&nbsp; : &nbsp;</td>
                            <td align="center">
                                <input type="text" v-model="sec" id="sec" maxlength="2" size="1">
                            </td>
                        </tr>

                        <tr>
                            <td align="right">
                                <img @click="add_time_clock('min')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/plus_24_173078.png">
                                <img @click="sub_time_clock('min')" class="clickable-icon" src="/BA/pages/static/vue_components/PLUGINS/timer/minus_24_173056.png">
                            </td>
                            <td>&nbsp;</td>
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
                                <audio v-bind:id="'my_audio' + current_metadata.entity_id" controls style="display:none">
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
                <div v-if="editing_mode"
                    style="border: 1px solid #888; padding: 15px; box-shadow: 5px 5px 10px #555; background-color: rgba(185,53,152,0.4)"
                >
                    <span style="font-size:22px"><b>TIMER WIDGET</b></span>
                    <br><br><br>
                    Select desired ringtone:

                    <select v-model="current_data.audio_file">
                        <option disabled value=''>[Choose an option]</option>
                        <option value='alarm_good_morning_song.mp3'>alarm_good_morning_song.mp3</option>
                        <option value='dreamscape-alarm-clock-117680.mp3'>dreamscape-alarm-clock-117680.mp3</option>
                        <option value='gentle_alarm.mp3'>gentle_alarm.mp3</option>
                    </select>

                    <br><br>
                    <button @click="save" v-bind:disabled="Object.keys(current_data).length === 0" title='Save the selected ringtone'>
                        SAVE
                    </button>
                    <a @click.prevent="cancel_edit()" href="#" style="margin-left:15px">Cancel</a>
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
                editing_mode: this.item_metadata.entity_id < 0 ? true : false,   // Negative entity_id means "new Item" (automatically placed in editing mode)

                // This object contains the values bound to the editing fields, initially cloned from the prop data;
                //      it'll change in the course of the edit-in-progress
                current_data:   Object.assign({}, this.item_fields),

                // Clone of the above object, used to restore the data in case of a Cancel or failed save
                original_data:  Object.assign({}, this.item_fields),

                // Private copy of the metadata
                current_metadata:   Object.assign({}, this.item_metadata),

                show_timer: "00:00",                 // The timer's display

                // The following 2 are the parts of the value that the alarm gets set to
                min: 0,
                sec: 0,

                // The following 2 are the parts of the display
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
            // Pick a text to show on the Start/Resume button
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

                var audio = document.getElementById("my_audio"+ this.current_metadata.entity_id);    // HTML DOM Audio Object.  It inherits from HTMLMediaElement
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



            /**
             * Invoked when the user clicks on the '+' icon.
             * It sets the "min" and "sec" Vue data variables.
             *
             * @param {string} units    - Either 'min' or 'sec'
             *
             * @returns {void}
             */
            add_time_clock(units)
            {
                //console.log(`In add_time_clock(): units = "${units}"`);

                if (units == "min")
                    this.min = this.increment_time(this.min, 59);
                else
                    this.sec = this.increment_time(this.sec, 59);
            },


            /**
             * Invoked when the user clicks on the '-' icon.
             * It sets the "min" and "sec" Vue data variables.
             *
             * @param {string} units    - Either 'min' or 'sec'
             *
             * @returns {void}
             */
            sub_time_clock(units)
            {
                //console.log(`In sub_time_clock(): units = "${units}"`);

                // To address a browser (at least Firefox) flaw that
                // turns Vue integer values into strings upon re-starting the browser on the cached page
                this.min = parseInt(this.min);
                this.sec = parseInt(this.sec);

                if (units == "min")
                    this.min = this.decrement_time(this.min);
                else
                    this.sec = this.decrement_time(this.sec);
            },

            /**
             * Increment by 1, modulo max
             */
            increment_time(num, max)
            {
                if (num+1 > max)
                    return 0;

                return num+1;
            },

            /**
             * Decrement by 1, but don't go below 0
             */
            decrement_time(num)
            {
                if (num == 0)
                    return 0;

                return num-1;
            },



            set_limit(strtstop)
            // Invoked by clicking on the Start/Resume button, as well as by clicking on the Pause button
            // strtstop is a boolean, indicating whether the timer is being stopped
            {
                console.log(`In set_limit(): strtstop = ${strtstop}`);

                // To address a browser (at least Firefox) flaw that
                // turns Vue integer values into strings upon re-starting the browser on the cached page
                this.min = parseInt(this.min);
                this.sec = parseInt(this.sec);

                // Prevent multiple settimeouts
                if (this.st)
                    clearTimeout(this.st);

                if (this.pause)  {  // If in a paused state
                    limit = this.show_timer;
                    console.log(`    limit = "${limit}" [NO LONGER USED]`);      // EXAMPLE: "00:05"
                    var parselimit_arr = [this.show_min, this.show_sec];

                    if (!strtstop)  {
                        this.pause = false;     // Take out of paused state
                        this.stopped = false;
                    }
                }
                else  {
                    var parselimit_arr = [this.min, this.sec];
                    if (!strtstop)
                        this.stopped = false;
                }

                console.log(`    parselimit_arr = ${parselimit_arr}`);      // EXAMPLE: [1, 23, 40]


                // Convert the min/sec pair to seconds
                this.parselimit = parselimit_arr[0]*60 + parselimit_arr[1];
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

                //console.log(`    curmin = ${curmin} | cursec = ${cursec}`);

                this.show_min = curmin;
                this.show_sec = cursec;

                // Format as 3 padded groups of characters, separated by ":"
                this.show_timer = this.format(this.show_min) + ":" + this.format(this.show_sec);

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
                this.show_timer = "00:00";
                this.pause = false;         // Clear the paused state (if applicable)
                this.stopped = true;
            },



            /*
                ---------------  SERVER CALLS  ---------------
             */

            save()
            // Conclude an EDIT operation.  TODO: maybe save/cancel should be a sub-component shared among various plugins?
            {
                // Start the body of the POST to send to the server
                var post_obj = {class_name: this.current_metadata.class_name};

                if (this.current_metadata.entity_id < 0)  {     // Negative entity_id is a convention indicating a new Content Item to create,
                     // Needed for NEW Content Items
                     post_obj.category_id = this.category_id;
                     post_obj.insert_after_uri = this.current_metadata.insert_after_uri;       // entity_id of Content Item to insert after, or keyword "TOP" or "BOTTOM"
                     post_obj.insert_after_class = this.current_metadata.insert_after_class;   // Class of Content Item to insert after

                     url_server_api = `/BA/api/add_item_to_category`;       // URL to communicate with the server's endpoint
                }
                else {   // Update an EXISTING Content Item
                    post_obj.entity_id = this.current_metadata.entity_id;

                    url_server_api = `/BA/api/update_content_item`;        // URL to communicate with the server's endpoint
                }

                // Enforce required field
                if ('audio_file' in this.current_data) // For new records, this attribute gets dynamically added by v-model during data entry
                    post_obj.audio_file = this.current_data.audio_file;
                else  {
                    alert("Cannot save an empty audio file");
                    return;
                }

                console.log(`In 'vue-plugin-timer', save().  About to contact the server at ${url_server_api} .  POST object:`);
                console.log(post_obj);

                // Initiate asynchronous contact with the server.  TODO: maybe switch to a JSON-based web API
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
                In case of newly-created items, if successful, the server_payload will contain the newly-assigned entity_id
             */
            {
                console.log("Finalizing the Timer Widget save() operation...");
                if (success)  {     // Server reported SUCCESS
                    //console.log("    server call was successful");
                    this.status_message = `Successful edit`;

                    // If this was a new item (with the temporary negative entity_id), update its entity_id with the value assigned by the server
                    if (this.current_metadata.entity_id < 0)  {
                        this.current_metadata.entity_id = server_payload;      // Update with the value assigned by the server
                        delete this.current_metadata.insert_after_uri;         // No longer needed
                        delete this.current_metadata.insert_after_class;       // No longer needed
                    }

                    // Inform the parent component of the new state of the data; pass clones of the relevant objects
                    const signal_data = {
                        item_fields:   Object.assign({}, this.current_data),
                        item_metadata: Object.assign({}, this.current_metadata)
                    };
                    console.log("Timer Widget component sending `updated-item` SIGNAL to its parent with the following data:");
                    console.log(structuredClone(signal_data));     // Log a frozen deep snapshot of the object
                    this.$emit('updated-item', signal_data);

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

                if (this.current_metadata.entity_id < 0) {
                    // If the editing being aborted is of a NEW item, inform the parent component to remove it from the page
                    console.log("Timer Widget sending `cancel-edit` SIGNAL to its parent");
                    this.$emit('cancel-edit');
                }
                else
                    this.editing_mode = false;      // Exit the editing mode

            } // cancel_edit


        }  // METHODS
    }
); // end component