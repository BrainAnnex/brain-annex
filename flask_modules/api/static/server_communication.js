/*
    ----------------------------------------------------------------------------------
	MIT License

    Copyright (c) 2021-24 Julian A. West and the BrainAnnex.org project.

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
	----------------------------------------------------------------------------------

    TODO: maybe relocate under flask_modules/pages/static

 */


class ServerCommunication
/*  STATIC class to communicate with the server using the fetch() API.

    Guide:  https://brainannex.org/docs/server_communication.htm
 */
{
    static contact_server(url_server,
                                        {
                                            method = "GET",
                                            post_obj = {},
                                            post_body = "",
                                            callback_fn = undefined,
                                            custom_data = undefined
                                        } = {} )
    /*  Send a request to the server at the specified URL
        The expected eventual payload is a JSON string

            method:         Either "GET" or "POST" - optional, by default "GET"
                                (however, ignored if a non-empty string is passed to post_body,
                                                     or a non-empty object is passed to post_obj)

            post_obj:       If a non-empty object is passed, the method is automatically forced to POST
                                (and it will disregard the contents of post_body)
                                EXAMPLE:  {uri: 123, text: "Some data"}
            post_body:      If a non-empty string is passed, the method is automatically forced to POST;
                                (disregarded if a non-empty post_obj was passed,
                                 i.e. post_obj has higher priority over post_obj)
                                 TODO: maybe phase out

            callback_fn:    EXAMPLE:    finish_my_op   , assuming there's a function called finish_my_op
            custom_data:    If present, it is passed as a final argument to the callback function

        EXAMPLE of invocation:
            ServerCommunication.contact_server(url_server, {callback_fn: this.finish_get_note});

        EXAMPLE of callback_fn:

            function finish_get_note(success, server_payload, error_message, custom_data)
            //  Callback function to wrap up the action of get_note() upon getting a response from the server
            //      success:        boolean indicating whether the server call succeeded
            //      server_payload: whatever the server returned (stripped of information about the success of the operation)
            //      error_message:  a string only applicable in case of failure
            //      custom_data:    whatever JavaScript structure, if any, was passed by the contact_server() call
            {
                console.log("Finalizing the get_note operation...");

                if (success)  {     // Server reported SUCCESS
                    ...             // do something with the server_payload value
                }
                else  {             // Server reported FAILURE
                    ...             // do something with the error_message value
                }
                ...  // Op to do at the end in either case
            }

     */
    {
        // TODO: more argument checking
        if (typeof post_obj !== 'object') {
            alert("ERROR in invocation of contact_server(): the `post_obj` argument is not an Object");
            return;
        }

        const post_obj_as_string = ServerCommunication.parse_POST_object(post_obj);
        //console.log(`contact_server() converted the POST object to the following string: ${post_obj_as_string}`);
        if (post_obj_as_string != "")
            post_body = post_obj_as_string;     // If a post_body was passed, it will be over-ridden,
                                                // because post_obj has higher priority

        /*
        if (post_body == "")
            console.log('contact_server() - No POST data present');
        else
           console.log(`contact_server() - a POST will be used, with the following data: "${post_body}"`);
        */

        return ServerCommunication.contact_server_JSON(url_server, post_body, callback_fn, custom_data, method);

    } // contact_server - TODO: phase out



    static contact_server_NEW(url_server,
                                        {
                                            method = "GET",
                                            data_obj = {},
                                            json_encode_send = false,
                                            callback_fn = undefined,
                                            custom_data = undefined
                                        } = {} )
    /*  Send a request to the server at the specified URL.
        The expected eventual payload is a JSON string.

        url_server:     Do NOT include a final "/"

            method:         Either "GET" or "POST" - optional, by default "GET"

            data_obj:       To be used with either GET or POST.  EXAMPLE:  {uri: 123, text: "Some data"}

            json_encode_send:    If true, the data in data_obj will get JSON-encoded

            callback_fn:    EXAMPLE:    finish_my_op   , assuming there's a function called finish_my_op
            custom_data:    If present, it is passed as a final argument to the callback function

        EXAMPLE of invocation:
            ServerCommunication.contact_server(url_server, {callback_fn: this.finish_get_note});

        EXAMPLE of callback_fn:

            function finish_get_note(success, server_payload, error_message, custom_data)
            //  Callback function to wrap up the action of get_note() upon getting a response from the server
            //      success:        boolean indicating whether the server call succeeded
            //      server_payload: whatever the server returned (stripped of information about the success of the operation)
            //      error_message:  a string only applicable in case of failure
            //      custom_data:    whatever JavaScript structure, if any, was passed by the contact_server() call
            {
                console.log("Finalizing the get_note operation...");

                if (success)  {     // Server reported SUCCESS
                    ...             // do something with the server_payload value
                }
                else  {             // Server reported FAILURE
                    ...             // do something with the error_message value
                }
                ...  // Op to do at the end in either case
            }

     */
    {
        // TODO: more testing.  Tested so far:  * GET with JSON


        // TODO: more argument checking
        if (typeof data_obj !== 'object') {
            alert("ERROR in invocation of contact_server_NEW(): the `data_obj` argument is not an Object");
            return;
        }


        if (json_encode_send) {
            ServerCommunication.sanitize_data_object(data_obj);    // TODO: unclear if really necessary; JSON.stringify() seems to already ditch "undeclared" values
            var data_str = JSON.stringify(data_obj);
            console.log(`contact_server_NEW(): the data object to send is being converted to JSON as '${data_str}'`);
            data_str = "json=" + data_str;      // Start preparing a query string for the URL
        }
        else {
            var data_str = ServerCommunication.parse_data_object(data_obj);
            console.log(`contact_server_NEW(): the data object to send is being string-encoded as "${data_str}"`);
        }


        if (method == "POST")  {
            console.log(`contact_server_NEW() - a POST will be used, with the following data string: "${data_str}"`);
            if (json_encode_send)
                var fetch_options = ServerCommunication.prepare_POST_options_JSON(data_str);    // An object
            else
                var fetch_options = ServerCommunication.prepare_POST_options(data_str);         // An object
        }
        else  {    // GET
            if (data_str != "")
                url_server += "?" + data_str;       // Append a query string to the URL

            console.log(`contact_server_NEW() - a GET will be used, with the following URL: ${url_server}`);
            var fetch_options = ServerCommunication.prepare_GET_options();              // An object
        }

        return ServerCommunication.send_data_to_server(url_server, fetch_options, callback_fn, custom_data);

    } // contact_server_NEW



    static send_data_to_server(url_server, fetch_options, callback_fn, custom_data)
    // TODO: this is the replacement for contact_server_JSON()
    // TODO: utilize also for the final part of contact_server_UPLOAD()
    {
        var success_flag;           // true if communication with the server succeeds, or false otherwise
        var server_payload = "";    // Only applicable if success_flag is true
        var error_message = "";     // Only applicable if success_flag is false

        console.log("send_data_to_server(): about to start asynchronous call to ", url_server);

        fetch(url_server, fetch_options)
        .then(fetch_resp_obj => ServerCommunication.handle_fetch_errors(fetch_resp_obj))    // Deal with fetch() errors
        .then(fetch_resp_obj => fetch_resp_obj.json())  // Transform the response object into a JS promise that will resolve into a JSON object
                                                        //      TODO: turn into a method that first logs the first part of the response
                                                        //            (helpful in case of parsing errors)
        .then(server_response => {                      // Manage the server response
            console.log("Server response received by send_data_to_server(): ");
            console.log(server_response);
            // Check if the response indicates failure
            const error_msg = ServerCommunication.check_for_server_error_JSON(server_response);
            if (error_msg != "")    // If server reported failure
                throw new Error(error_msg);   // This will take us to the .catch portion, below
            else
            {   // Server reported SUCCESS
                server_payload = ServerCommunication.extract_server_data_JSON(server_response);
                //console.log("server reported success, and returned the following payload: ", server_payload);
                success_flag = true;
            }
        })
        .catch(err => {  // All errors eventually go thru here
            error_message = ServerCommunication.report_fetch_errors(err);
            success_flag = false;
        })
        .finally(() => {  // Final operation regardless of error or success
            //console.log("Completed the server call.  Passing control to the callback function");
            if (callback_fn !== undefined) {
                if (custom_data === undefined)
                    callback_fn(success_flag, server_payload, error_message);
                else
                    callback_fn(success_flag, server_payload, error_message, custom_data);
            }
        });  // fetch

    } // send_data_to_server



    static contact_server_JSON(url_server, post_body, callback_fn, custom_data, method)
    /*  Send a request to the server at the specified URL, with a GET or POST method (depending on the presence of post_body).
        The expected eventual payload is a JSON string

        post_body : if a blank string, a GET is assumed, unless method="POST" is specified
            EXAMPLE of post_body: "uri=62&schema_code=r"

        custom_data is an OPTIONAL argument; if present, it is passed as a final argument to the callback function

        TODO: factor out some parts to contact_server()
     */
    {
        var success_flag;           // true if communication with the server succeeds, or false otherwise
        var server_payload = "";    // Only applicable if success_flag is true
        var error_message = "";     // Only applicable if success_flag is false
        var fetch_options;

        if (post_body != "" || method == "POST") {
            //console.log("About to start asynchronous call to ", url_server, " with POST body: ", post_body);
            fetch_options = ServerCommunication.prepare_POST_options(post_body);
        }
        else
        {
            //console.log("About to start asynchronous call to ", url_server, " with GET method");
            fetch_options = ServerCommunication.prepare_GET_options();
        }

        fetch(url_server, fetch_options)
        .then(fetch_resp_obj => ServerCommunication.handle_fetch_errors(fetch_resp_obj))    // Deal with fetch() errors
        .then(fetch_resp_obj => fetch_resp_obj.json())  // Transform the response object into a JS promise that will resolve into a JSON object
                                                        //      TODO: turn into a method that first logs the first part of the response
                                                        //            (helpful in case of parsing errors)
        .then(server_response => {                      // Manage the server response
            //console.log("Server response received by contact_server_JSON(): ");
            //console.log(server_response);
            // Check if the response indicates failure
            const error_msg = ServerCommunication.check_for_server_error_JSON(server_response);
            if (error_msg != "")   // If server reported failure
                throw new Error(error_msg);   // This will take us to the .catch portion, below
            else
            {   // Server reported SUCCESS
                server_payload = ServerCommunication.extract_server_data_JSON(server_response);
                //console.log("server reported success, and returned the following payload: ", server_payload);
                success_flag = true;
            }
        })
        .catch(err => {  // All errors eventually go thru here
            error_message = ServerCommunication.report_fetch_errors(err);
            success_flag = false;
        })
        .finally(() => {  // Final operation regardless of error or success
            //console.log("Completed the server call.  Passing control to the callback function");
            if (callback_fn !== undefined) {
                if (custom_data === undefined)
                    callback_fn(success_flag, server_payload, error_message);
                else
                    callback_fn(success_flag, server_payload, error_message, custom_data);
            }
        });  // fetch

    }  // contact_server_JSON




    static contact_server_UPLOAD(url_server,
                                            {
                                                file_to_import = undefined,
                                                post_obj = {},
                                                callback_fn = undefined,
                                                custom_data = undefined
                                            } = {} )
    /*  Send a request to the server at the specified URL, with POST method, to perform a single file upload,
        and optionally pass additional POST data.
        The server response is expected to be JSON text.

        custom_data is an OPTIONAL argument; if present, it is passed as a final argument to the callback function

        Note: the fixed key name 'file' is used for the uploaded file.

        TODO: utilize send_data_to_server() for the last part of this function
     */
    {
        var success_flag;           // true if communication with the server succeeds, or false otherwise
        var server_payload = "";    // Only applicable if success_flag is true
        var error_message = "";     // Only applicable if success_flag is false

        console.log("In contact_server_UPLOAD()");

        const post_data = new FormData();
        post_data.append('file', file_to_import);   // 'file' is just an identifier to attach to the upload;
                                                    //       this is the counterpart of <input name="file"> in forms
                                                    // Note: a 3rd argument may be passed with a name to use for the
                                                    //       file being uploaded (rather than its actual name)

        // Prepare the additional POST data, if any
        var k, val;

        for (k in post_obj) {   // Loop thru the keys
            val = post_obj[k];      // Get the corresponding value
            console.log(`    key: ${k}  |  value: ${val} `);

            post_data.append(k, val);   // Similar to passing input values thru a form
        }


        const fetch_options = {     // Important: do NOT set a 'Content-Type' header!
            method: 'POST',
            body: post_data
        };

        console.log("fetch_options : ", fetch_options);


        fetch(url_server, fetch_options)
        .then(fetch_resp_obj => ServerCommunication.handle_fetch_errors(fetch_resp_obj))    // Deal with fetch() errors
        .then(fetch_resp_obj => fetch_resp_obj.json())  // Transform the response object into a JS promise that will resolve into a JSON object
                                                        //      TODO: turn into a method that first logs the first part of the response (helpful in case of parsing errors)
        .then(server_response => {                      // Manage the server response
            console.log("server_response received by contact_server_UPLOAD(): ");
            console.log(server_response);
            // Check if the response indicates failure
            const error_msg = ServerCommunication.check_for_server_error_JSON(server_response);
            if (error_msg != "")   // If server reported failure
                throw new Error(error_msg);   // This will take us to the .catch portion, below
            else
            {   // Server reported SUCCESS
                server_payload = ServerCommunication.extract_server_data_JSON(server_response);
                //console.log("server reported success, and returned the following payload: ", server_payload);
                success_flag = true;
            }
        })
        .catch(err => {  // All errors eventually go thru here
            error_message = ServerCommunication.report_fetch_errors(err);
            success_flag = false;
        })
        .finally(() => {  // Final operation regardless of error or success
            //console.log("Completed the server call.  Passing control to the callback function");
            if (callback_fn !== undefined) {
                if (custom_data === undefined)
                    callback_fn(success_flag, server_payload, error_message);
                else
                    callback_fn(success_flag, server_payload, error_message, custom_data);
            }
        });  // fetch

    }  // contact_server_UPLOAD



    static sanitize_data_object(data_object)
    /*  Drop any undefined or NaN values from the given object literal
     */
    {
        var data_str = "";      // The string version of the object
        var k, val;

        for (k in data_object) {    // Loop thru the keys
            val = data_object[k];      // Get the corresponding value

            if (val === undefined  ||  Number.isNaN(val))
                delete data_object[k];      // Ditch the bad values
        }
    }


    static parse_data_object(data_object)
    /*  Turn an object literal into a string, after transforming its attribute values with encodeURIComponent()

        Any non-blank string in the values gets passed thru encodeURIComponent.
        Any blank strings in the values are left undisturbed.
        Any key/value with an undefined value gets completely dropped.
        Note: if data_object contains no properties, or is null, then an empty string is returned.

        EXAMPLE of usage:
                data_object = {id: 123,  name: "some name",  city: undefined};
                data_str = ServerCommunication.parse_data_object(data_object);

                It will return the string:   "id=123&name=some%20name"

        TODO: this version is for both POST and GET; it will replace parse_POST_object()
     */
    {
        var data_str = "";      // The string version of the object
        var k, val;

        for (k in data_object) {    // Loop thru the keys
            val = data_object[k];      // Get the corresponding value

            if (val === undefined  ||  Number.isNaN(val))
                continue;           // Completely drop any key/value pair, if the value is undefined or a NaN

            //console.log(`    key: ${k}  |  value: ${val}   |  type of value: '${typeof val}'`);

            data_str += k + "=";

            if ((typeof val == "string")  &&  (val != ""))
                data_str += encodeURIComponent(val);    // Safe-encode the value
            else
                data_str += val;                        // Pass thru the value undisturbed

            data_str += "&";
            //console.log(`data_str so far: ${data_str}`);
        }

        if (data_str == "")
            return "";

        return data_str.substring(0, data_str.length - 1);    // Zap the final "&"
    }


    static prepare_GET_options()
    /*  Prepare and return an object to be used as a 2nd ARGUMENT TO A fetch() call, in case there's a GET method involved.
     */
    {
        const fetch_options = {
            method: 'GET',
            cache: 'reload'
        };

        return fetch_options;
    }


    static prepare_POST_options(post_body)
    /*  Prepare and return an object to be used as a 2nd ARGUMENT TO A fetch() call;
        to be used in cases when there's a POST method involved.
        The requested Content-Type will be 'application/x-www-form-urlencoded'.

        post_body:  The string exactly as will be passed to the POST call

        EXAMPLES:
                    post_body = "x=11&y=22";
                    post_body = "id=" + note_id + "&body=" + encodeURIComponent(note_body);

        IMPORTANT: values defined inside the post_body string must be generated with encodeURIComponent(), as needed.
                   (an alternative would be to use Jason or XML Content-Type, and skip using encodeURIComponent)
     */
    {
        const fetch_options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
                // Note: We're using form-urlencoded.
                //       Alternatively, I could encode the data with Jason or XML, and skip encodeURIComponent()
            },
            credentials: 'same-origin',
            body: post_body		// IMPORTANT: the body of the POST data type must match the 'Content-Type' header
        };

        return fetch_options;
    }

    static prepare_POST_options_JSON(post_body)
    /*  Prepare and return an object to be used as a 2nd ARGUMENT TO A fetch() call;
        to be used in cases when there's a POST method involved.

        TODO: merge with prepare_POST_options() by passing an additional argument
     */
    {
        const fetch_options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin',
            body: post_body		// IMPORTANT: the body of the POST data type must match the 'Content-Type' header
        };

        return fetch_options;
    }


    static parse_POST_object(post_obj)
    /*  Turn an object literal into a string, after transforming attribute values with encodeURIComponent();
        suitable for situations when the HTTP request uses
        'Content-Type': 'application/x-www-form-urlencoded'

        Any non-blank string gets passed thru encodeURIComponent.
        [NEW: Any blank strings in the values are left undisturbed]

        The returned result is ready for use as the "post_body" argument
        in contact_server() and contact_server_JSON()
        Note: if post_obj contains no properties, or is null, then an empty string is returned.

        EXAMPLE of usage:
                post_obj = {id: 123,  name: "some name"};
                post_body = ServerCommunication.parse_POST_object(post_obj);

        TODO: phase out in favor of parse_data_object()
     */
    {
        var post_body = "";
        var k, val;

        for (k in post_obj) {   // Loop thru the keys
            val = post_obj[k];      // Get the corresponding value
            //console.log(`    key: ${k}  |  value: ${val} `);

            post_body += k + "=";

            if ((val != "") && (typeof val == "string"))
                post_body += encodeURIComponent(val);
            else
                post_body += val;

            post_body += "&";
            //console.log(`post_body so far: ${post_body}`);
        }

        if (post_body == "")
            return "";

        return post_body.substring(0, post_body.length - 1);    // Zap the final "&"
    }


    static handle_fetch_errors(resp_obj)
    /*  If the given response object - returned by a fetch() calls - indicates success,
            just pass thru the response object:
            it will get caught by the next ".then()" statement of the original fetch() call.
        In case of HTTP error status (such as 404), log the error to the console,
            and raise an exception with error details - meant to be caught by a
            ".catch()" statement in the original fetch() call.

        Example of response object:
            { type: "basic", url: "http://localhost:5000/BA/api/create_new_schema_class", redirected: false,
              status: 200, ok: true, statusText: "OK", headers: Headers, body: ReadableStream, bodyUsed: false }
     */
    {
        if (resp_obj.ok)  {
            // FOR DEBUGGING:
            console.log(`Received response object from server: `, resp_obj);
            console.log('    Content-Type of response: ', resp_obj.headers.get('Content-Type'));
            //console.log('    Date: ', resp_obj.headers.get('Date'));
            // END OF DEBUGGING

            return resp_obj;	// Just pass thru the response object
        }

        // If the above "ok" attribute is false, then there was an HTTP error status - for example a 404 (page not found)
        console.error('Error: HTTP error status received from the server. Response object below:', resp_obj);

        const error_info = "HTTP error status received from the server. Error status: " + resp_obj.status
                                + ". Error details: " + resp_obj.statusText + ". \nURL: " + resp_obj.url;

        throw new Error(error_info);
    }



    static report_fetch_errors(err)
    /*  Invoked in case of ANY failure during a the fetch() call to the specified URL,
        including:
            1) errors in the fetch() call itself
            2) HTTP error
            3) server response messages indicative of error
        Compose an error message, log it to the console, issue an alert about it, and return it as a string.

        ARGUMENTS:
            err : originates from  .catch(err => ...)  OR  from  throw new Error(error_info)
                  object with 2 properties: name and message
                  See https://stackoverflow.com/questions/9156176/what-is-the-difference-between-throw-new-error-and-throw-someobject
      */
    {
        console.error('Error during the fetch() operation');
        console.log(err);   // Note: this may not immediately show up on the console, if there
                            //       is an alert box (which needs to be dismissed first)

        // Old verbose message:  "Failed interaction with the server in the fetch() call. " +
        const fetch_failure_message = err.name + " - " + err.message;
        alert(fetch_failure_message);

        /* TODO: there might be a timing (or caching??) bug in Firefox.  I sporadically get an error with name "TypeError"
           and message: "NetworkError when attempting to fetch resource"
           MAYBE ATTEMPT A 2nd fetch automatically???
           See also: https://stackoverflow.com/questions/67451129/express-and-fetch-typeerror-networkerror-when-attempting-to-fetch-resource
           https://stackoverflow.com/questions/66287934/networkerror-when-attempting-to-fetch-resource-in-firefox-84-85
         */

        return fetch_failure_message;
    }




	/****************************************************************************************************************

                 THE METHODS BELOW ARE RELATED TO JSON-SPECIFIC PARTS OF THE SERVER COMMUNICATION

                 1) JSON RESPONSE is expected to always be present.
                 2) If successful, 2 keys are expected:
                            "status" (containing the value "ok") and "payload" (with the actual data)
                 3) In case of failure, 2 keys are expected:
                            "status" (containing the value "error") and "error_message" (with details)

     ****************************************************************************************************************/


    static  check_for_server_error_JSON(server_response)
	/*  Check the given server response for the presence of errors.
		If an error was detected, return an error message; otherwise, return an empty string.
	 */
	{
	    const SUCCESS_STATUS = "ok";        // This value for the "status" JSON flag is indicative of a successful operation

		var server_error_msg;

		if (server_response == "")  {       // Irregular situation where the server response is blank
			server_error_msg = "Possible Error: the server didn't return any data (try again)"
			return server_error_msg;
		}

	    const server_status = server_response.status;
        //console.log(`In check_for_server_error_JSON(): server response status was '${server_status}'`);

	    if (server_status == SUCCESS_STATUS)
	        return "";	    // No errors found

        // If we get here, an error was detected
        if ('error_message' in server_response)
		    server_error_msg = "The server reported the following problem: " + server_response.error_message;
		else    //  if the server didn't provided the expected error_message field
		    server_error_msg = "The server reported a problem; no further information is available";

        console.log(`In check_for_server_error_JSON(): server response status was '${server_status}'.  ${server_error_msg}`);

		return server_error_msg;

	} // check_for_server_error_JSON()


	static  extract_server_data_JSON(server_response)
	/*  From the given server response, attempt to extract the data payload - which may or may not be present;
	    if absent, return null */
	{
	    //console.log(`In extract_server_data_JSON -  server_response is:`);
	    //console.log(server_response);

	    if ('payload' in server_response)   // If a payload was returned by the server
	        return server_response.payload;
	    else
	        return null;
	}

} // static class "ServerCommunication"