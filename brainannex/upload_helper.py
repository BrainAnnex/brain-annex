import os
import re               # For REGEX
import unicodedata



class UploadHelper:
    """
    Helper class to manage file uploads with Flask 1.1
    """


    @classmethod
    def store_uploaded_file(cls, files, upload_dir: str, key_name=None) -> (str, str, str, str):
        """
        Meant for SINGLE-file uploads.

        It accepts a flask.request object, and it creates a file from the upload,
        which it stores into the folder specified by upload_dir

        It decides, from the name of the file being uploaded, a meaningful (and safe) name
        for the temporary file to create as part of the upload.

        It returns both the basename and the full filename of the temporary file thus created,
        as well as the original name of the file.

        In case of error, an Exception is raised

        TODO: maybe allow to optionally provide the final location/name for the uploaded file

        :param files:       An ImmutableMultiDict object.
                                EXAMPLE: ImmutableMultiDict([('imported_datafile', <FileStorage: 'my_data.json' ('application/json')>)])
                                    where 'imported_datafile' originates from <input type="file" name="imported_datafile">
                                    and the name after FileStorage is the name of the file being uploaded
        :param upload_dir:  Name of temporary directory to use for the upload.
                                EXAMPLES: "/tmp/" (Linux)  or  "D:/tmp/" (Windows)
        :param key_name:    (OPTIONAL) The value that was used in the HTML form INPUT tag for the "name" attribute:
                                <input type="file" name="some_key_to_refer_to_the_upload">
                                or its counterpart in JS submissions, such as
                                            const post_data = new FormData();
                                            post_data.append('file', this.file_to_import);
                            Basically, a label to tag the file being uploaded.
                            The "Dropzone" front-end module uses "file".
                            If not provided, the first key found in request.files is used.
                            (Note: in the ImmutableMultiDict data structure, multiple values are allowed for the same key;
                                   if more than one value is present, the first is picked)

        :return:            The 4-tuple (filename, full_filename_including_path, original_filename, mimetype)
                            where filename is the basename;
                            filename and original_filename are usually the same, unless there were
                            funky characters in original_filename
                            EXAMPLE: ("my_file_being_uploaded.txt", "D:/tmp/my_file_being_uploaded.txt",
                                      "my_file_being_uploaded.txt", "text/plain")

        """
        # Locate the data about the desired file upload
        if len(files) == 0:
            raise Exception(f"No files found in upload!  (The ImmutableMultiDict object in request.files is empty)")


        if key_name is not None:    # If a specific "name" (tag attached to uploaded file) was requested
            # Example from an invoking form:   <input type="file" name="some_key_to_refer_to_the_upload">
            if key_name not in files:
                raise Exception(f"No file tagged with the label `{key_name}` found in the upload!  "
                                f"Check the `name` attribute in the HTML `input` tag (it should be '{key_name}').")

        else:                       # If no particular "name" (tag) was specified, just pick the first one
            key_name = list(files)[0]
            print(f"store_uploaded_file(): No specific key (tag associated with uploaded file) requested. "
                  f"The first key found in request.files (`{key_name}`) will be used.")


        f = files[key_name]      # f is a Werkzeug FileStorage object
        # Note: if multiple uploads were attached to this key, only the first one is picked

        #print("f: ", f)                    # EXAMPLE: <FileStorage: 'abc.txt' ('text/plain')>
        #print("f.stream: ", f.stream)      # EXAMPLE: <tempfile.SpooledTemporaryFile object at 0x000001604F5E6700>
        #print("f.filename: ", f.filename)  # EXAMPLE: abc.txt
        #print("f.mimetype: ", f.mimetype)  # EXAMPLE: text/plain

        # If the user did not select a file, the browser submits an
        #       empty file without a filename
        if f.filename == '':
            raise Exception("No selected file!  Did you select a file to upload?")


        # Construct, from the name of the file being uploaded, a "safe" name (free of funky characters)
        #   for the temporary file to create as part of the upload
        tmp_filename_for_upload = cls.secure_filename_BA(f.filename)
        #print(f"Name given to temporary file to upload to: `{tmp_filename_for_upload}`")

        #print(f"Attempting to upload to directory `{upload_dir}`")

        full_filename = f"{upload_dir}{tmp_filename_for_upload}"    # EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        f.save(full_filename)                                       # Create the temporary file, which concludes the upload

        return (tmp_filename_for_upload, full_filename, f.filename, f.mimetype)    # Normal termination



    @classmethod
    def secure_filename_BA(cls, filename: str) -> str:
        """
        Return a secure version of a filename.
        This filename can then safely be stored on a regular file system and passed
        to os.path.join.  The filename returned is an ASCII only string
        for maximum portability.

        ADAPTED FOR BRAIN ANNEX FROM werkzeug.utils.secure_filename(), version 0.5;
        blank spaces, commas, ampersand, and round parentheses are now treated as valid.
        However, blank spaces at start/end of names are still dropped.
        See: https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/

        On Windows, the function also makes sure that the file is not
        named after one of the special device files.

        EXAMPLES:   secure_filename_BA("My cool ++ movie.mov")          -> 'My cool  movie.mov'
                    secure_filename_BA("../../../etc/passwd")           -> 'etc_passwd'
                    secure_filename_BA('i contain \xfcml\xe4uts.txt')   -> 'i contain umlauts.txt'
                    secure_filename_BA("    blank-padded string  ")     -> 'blank-padded string'
                    secure_filename_BA("COM1.txt")       [On Windows]   -> '_COM1.txt'

        WARNING: The function might return an empty filename.  It's your responsibility
        to ensure that the filename is unique and that you abort or
        generate a random filename if the function returned an empty one.

        :param filename:    A string with the "cleaned-up" filename to use
        """
        #TODO: pytest
        _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_., &()-]") # List of allowed characters in the name;
                                                                       # BRAIN ANNEX adaptation:
                                                                       # note that the blank space, ampersand and the round parentheses
                                                                       # are included
        _windows_device_files = (
            "CON",
            "AUX",
            "COM1", "COM2", "COM3", "COM4",
            "LPT1", "LPT2", "LPT3",
            "PRN",
            "NUL"
        )

        # Convert non-ASCII characters to closest ASCII equivalent.  EXAMPLE: "Rüdiger" -> "Rudiger"
        filename = unicodedata.normalize("NFKD", filename)  # Normal form "KD" (Compatibility Decomposition)
        filename = filename.encode("ascii", "ignore").decode("ascii")

        # Replace OS file path separators (such as forward and back slashes) with underscores.  EXAMPLE: "bin/src" -> "bin_src"
        for sep in os.path.sep, os.path.altsep:
            if sep:
                filename = filename.replace(sep, "_")

        #filename = "_".join(filename.split()   # Replace all blanks spaces with underscores
        filename = _filename_ascii_strip_re.sub("", filename)   # Zap all characters except the allowed ones
        filename = filename.strip("._ ")         # Zap periods, underscores and blanks at the start or end of the string

        # On nt (such as Windows 7, etc) a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename; if it is, we prepend an underline
        if  (
                os.name == "nt"
                and filename
                and filename.split(".")[0].upper() in _windows_device_files
        ):
            filename = f"_{filename}"

        return filename
