/*
    ----------------------------------------------------------------------------------
	MIT License

    Copyright (c) 2021-23 Julian A. West

    This file is part of the "Brain Annex" project (https://BrainAnnex.org)

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
 */


class ServerCommunication
/*  STATIC class to communicate with the server using the fetch() API.

    Some methods are general; others implement one of the protocols detailed further down.

    Guide:  https://brainannex.org/docs/server_communication.htm
 */
{
    static contact_server(url_server,
                                        {
                                            method = "GET",
                                            post_obj = {},
                                            post_body = "",
                                            payload_type = "TEXT",
                                            callback_fn = undefined,
                                            custom_data = undefined
                                        } = {} )
    /*  Send a request to the server at the specified URL
        Using named arguments to make use of contact_server_TEXT() or contact_server_JSON, etc

            method:         Either "GET" or "POST" - optional, by default "GET"
                                (however, ignored if a non-empty string is passed to post_body,
                                                     or a non-empty object is passed to post_obj)

            post_obj:       If a non-empty object is passed, the method is automatically forced to POST
                                (and it will disregard the contents of post_body)
                                EXAMPLE:  {item_id: 123, text: "Some data"}
            post_body:      If a non-empty string is passed, the method is automatically forced to POST;
                                (disregarded if a non-empty post_obj was passed,
                                 i.e. post_obj has higher priority over post_obj)

            payload_type:   Either "TEXT" or "JSON" - optional; by default "TEXT"
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
        //console.log(`contact_server() converted the post object to the following string: "${post_obj_as_string}"`);
        if (post_obj_as_string != "")
            post_body = post_obj_as_string;     // If a post_body was passed, it will be over-ridden,
                                                // because post_obj has higher priority

        /*
        if (post_body == "")
            console.log('contact_server() - No POST data present');
        else
           console.log(`contact_server() - a POST will be used, with the following data: "${post_body}"`);
        */

        if (payload_type == "TEXT")
            return ServerCommunication.contact_server_TEXT(url_server, post_body, callback_fn, custom_data, method);
        else
            return ServerCommunication.contact_server_JSON(url_server, post_body, callback_fn, custom_data, method);
    }


    static contact_server_TEXT(url_server, post_body, callback_fn, custom_data, method)
    /*  Send a request to the server at the specified URL, with a GET or POST method (depending on the presence of post_body)
        Use this function if the payload is general text.

        post_body : if a blank string, a GET is assumed, unless method="POST" is specified
            EXAMPLE of post_body: "item_id=62&schema_code=r"

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
        .then(fetch_resp_obj => fetch_resp_obj.text())  // Transform the response object into a JS promise that will resolve into a string
        .then(server_response => {                      // Manage the server response
            //console.log("server_response: ", server_response);
            // Check if the response indicates failure
            const error_msg = ServerCommunication.check_for_server_error(server_response);
            if (error_msg != "")   // If server reported failure
                throw new Error(error_msg);   // This will take us to the .catch portion, below
            else
            {   // Server reported SUCCESS
                server_payload = ServerCommunication.extract_server_data(server_response);
                //console.log("server reported success");
                //console.log("  ...and returned the following payload: ", server_payload);
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

    }  // contact_server



    static contact_server_JSON(url_server, post_body, callback_fn, custom_data, method)
    /*  Send a request to the server at the specified URL, with a GET or POST method (depending on the presence of post_body)
        Use this function if the payload is JSON text.

        post_body : if a blank string, a GET is assumed, unless method="POST" is specified
            EXAMPLE of post_body: "item_id=62&schema_code=r"

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
                                                        //      TODO: turn into a method that first logs the first part of the response (helpful in case of parsing errors)
        .then(server_response => {                      // Manage the server response
            console.log("server_response received by contact_server_JSON(): ");
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

        TODO: factor out some parts to contact_server()
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
                // Note: I'm using form-urlencoded.
                //       Alternatively, I could encode the data with Jason or XML, and skip encodeURIComponent()
            },
            credentials: 'same-origin',
            body: post_body		// IMPORTANT: the body of the POST data type must match the 'Content-Type' header
        };

        return fetch_options;
    }


    static parse_POST_object(post_obj)
    /*  Turn an object literal into a string, after transforming attribute values with encodeURIComponent();
        suitable for situations when we use 'Content-Type': 'application/x-www-form-urlencoded'

        Any non-blank string gets passed thru encodeURIComponent.
        [NEW: Any blank strings in the values are left undisturbed]

        The returned result is ready for use as the "post_body" argument
        in contact_server(), contact_server_TEXT() and contact_server_JSON()
        Note: if post_obj contains no properties, or is null, then an empty string is returned.

        EXAMPLE of usage:
                post_obj = {id: 123,  name: "some name"};
                post_body = ServerCommunication.parse_POST_object(post_obj);
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
            { type: "basic", url: "http://localhost:5000/BA/api/simple/create_new_schema_class", redirected: false,
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
        console.error('Error during the fetch() operation. Details in the next line: ');
        console.log(err);

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

             METHODS APPLICABLE TO SERVER COMMUNICATION USING THE FOLLOWING "SIMPLE TEXT PROTOCOL"

                IN BRIEF:   a string with the payload or error,
                            prefixed by the single character "+" or "-" respectively in case of success or failure

                PROTOCOL: 	1) a server response is expected; its lack is regarded as an error

                            2) if the response starts with the character "+", it's taken to be an successful operation,
                               and the optional rest of the string is taken to be a data payload

                            3) if the response starts with the character "-", it's taken to be an error status,
                               and the rest of the string is taken to be the error message

                            4) responses that DON'T start with either "+" or "-" are taken to be
                               an unexpected error (not correctly handled), and the entire text is regarded as a presumed error message

     ****************************************************************************************************************/


    static validate_server_response(server_response)
    /*  ONLY APPLICABLE TO SERVER COMMUNICATION USING THE SIMPLE TEXT PROTOCOL FOR THIS CLASS.
        If the given response indicates success, return true;
        otherwise, log it to the console and issue an alert with the error message provided by the server, and return false
     */
    {
        const server_error_msg = ServerCommunication.check_for_server_error(server_response);

        if (server_error_msg)	{	// If the server response indicated an ERROR
            console.error(server_error_msg);
            alert(server_error_msg);
            return false;
        }
        return true;           // No error
    }



	static  check_for_server_error(server_response)
	/*  ONLY APPLICABLE TO SERVER COMMUNICATION USING THE SIMPLE TEXT PROTOCOL FOR THIS CLASS.
	    Check the given server response for the presence of errors.
		If error is detected, return an error message; otherwise, return an empty string.
	 */
	{
	    const SUCCESS_PREFIX = "+";         // The initial "+" character is indicative of a successful operation
	    const ERROR_PREFIX = "-";           // The initial "-" character is indicative of a failure

		var server_error_msg;

		if (server_response == "")  {       // Irregular situation where the server response is blank
			server_error_msg = "Possible Error: the server didn't return any data (try again)"
			return server_error_msg;
		}

	    const server_status = server_response.substring(0, 1);	// The initial character

	    if (server_status == SUCCESS_PREFIX)
	        return "";	// No errors found

	    var parsed_server_response;

	    if (server_status == ERROR_PREFIX)
	        parsed_server_response = ServerCommunication.extract_server_data(server_response);
	    else
	        parsed_server_response = server_response;   // Irregular situation where the status prefix is missing

		server_error_msg = "the server reported the following problem: " + parsed_server_response;
		return server_error_msg;

	} // check_for_server_error()



	static  extract_server_data(server_response)
	/*  ONLY APPLICABLE TO SERVER COMMUNICATION USING THE SIMPLE TEXT PROTOCOL FOR THIS CLASS.
	    From the given server response, extract the data payload (either an error message or a successful result) */
	{
	    if (server_response == "")
	        return "";      // This is an irregular scenario that should be avoided

	    return server_response.substring(1, server_response.length);    // Drop the first character, which is the error status
	}



	/****************************************************************************************************************

                 METHODS APPLICABLE TO SERVER COMMUNICATION USING THE "STANDARD JSON PROTOCOL" FOR THIS CLASS

                 1) JSON RESPONSE is expected to always be present.
                 2) If successful, 2 keys are expected:
                            "status" (containing the value "ok") and "payload" (with the actual data)
                 3) In case of failure, 2 keys are expected:
                            "status" (containing the value "error") and "error_message" (with details)

     ****************************************************************************************************************/


    static  check_for_server_error_JSON(server_response)
	/*  ONLY APPLICABLE TO SERVER COMMUNICATION USING THE "STANDARD JSON PROTOCOL" FOR THIS CLASS.
	    Check the given server response for the presence of errors.
		If error is detected, return an error message; otherwise, return an empty string.
	 */
	{
	    const SUCCESS_STATUS = "ok";        // This value for the "status" JSON flag is indicative of a successful operation

		var server_error_msg;

		if (server_response == "")  {       // Irregular situation where the server response is blank
			server_error_msg = "Possible Error: the server didn't return any data (try again)"
			return server_error_msg;
		}

	    const server_status = server_response.status;
        console.log(`In check_for_server_error_JSON(): server response status = ${server_status}`);

	    if (server_status == SUCCESS_STATUS)
	        return "";	    // No errors found

        // If we get here, an error was detected
        if ('error_message' in server_response)
		    server_error_msg = "The server reported the following problem: " + server_response.error_message;
		else    //  if the server didn't provided the expected error_message field
		    server_error_msg = "The server reported a problem; no further information is available";

		return server_error_msg;

	} // check_for_server_error_JSON()


	static  extract_server_data_JSON(server_response)
	/*  ONLY APPLICABLE TO SERVER COMMUNICATION USING THE "STANDARD JSON PROTOCOL" FOR THIS CLASS.
	    From the given server response, extract the data payload */
	{
	    return server_response.payload;    // TODO: verify that it is actually present
	}

} // static class "ServerCommunication"