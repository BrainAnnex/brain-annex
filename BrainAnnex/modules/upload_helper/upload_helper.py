"""
2 classes:  UploadHelper and ImageProcessing    # TODO: maybe move to utilities folder
"""

import os
import re               # For REGEX
import unicodedata
from PIL import Image



class UploadHelper:
    """
    Helper class to manage file uploads with Flask 1.1 (using Werkzeug 2.1)
    """

    @classmethod
    def get_form_data(cls, request_obj, flat=True) -> dict:
        """
        It accepts a flask.request object, and it extracts and returns
        a dictionary with the data passed by the calling form thru inputs, such as:
                <input type="hidden" name="categoryID" value="123">
                <input name="remarks" value="some text">
        or its counterpart in JS submissions, such as
                                            const post_data = new FormData();
                                            post_data.append('categoryID', "123");

        TODO: merge with ApiRouting.extract_post_pars()

        :param request_obj: A flask.request object
        :param flat:        A flag only relevant when there are non-unique keys;
                            if True (default), the values associated to the later keys will be discarded...
                            if False, values are returned as lists
                            EXAMPLE - if the data originates from:
                                <input type="hidden" name="my_data" value="88">
                                <input type="hidden" name="my_data" value="99">
                            then flat=True returns {'my_data': '88'}
                            while flat=False returns {'my_data': ['88', '99']}

        :return:            A dictionary with the POST data
        """
        hidden_data = request_obj.form
        # EXAMPLE: ImmutableMultiDict([('categoryID', '123'), ('pos', 888)])
        #               if the HTML form included <input type="hidden" name="categoryID" value="123">
        #                                     and <input type="hidden" name="pos" value="88">
        #               Note that the keys may not be unique

        data_dict = hidden_data.to_dict(flat=flat)  # WARNING: if multiple identical keys occur,
                                                    #          the values associated to the later keys will be discarded

        return data_dict




    @classmethod
    def store_uploaded_file(cls, request_obj, upload_dir: str, key_name=None, verbose=False) -> (str, str, str, str):
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

        :param request_obj: A flask.request object
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
        :param verbose:     Flag for debugging

        :return:            The 4-tuple (filename, full_filename_including_path, original_filename, mimetype)
                            where filename is the basename;
                            filename and original_filename are usually the same, unless there were
                            funky characters in original_filename
                            EXAMPLE: ("my_file_being_uploaded.txt", "D:/tmp/my_file_being_uploaded.txt",
                                      "my_file_being_uploaded.txt", "text/plain")

        """
        if verbose:
            request_dict = request_obj.__dict__     # A dictionary of all names and attributes of object.
            keys_list = list(request_dict)
            # EXAMPLE: ['method', 'scheme', 'server', 'root_path', 'path', 'query_string', 'headers',
            #           'remote_addr', 'environ', 'shallow', 'cookies', 'url_rule', 'view_args']

            print(f"Upload flask.request object contains {len(request_dict)} items:\n    {keys_list}\n")

            for i, k in enumerate(keys_list):
                print(f"    ({i}) * {k}: {request_dict[k]}")

            # Note: somehow, cannot simply loop over request_dict, or it crashes with error "dictionary changed size during iteration"

            print("\nrequest.files: ", request_obj.files)     # Somehow, that's NOT included in the previous listing!
            # EXAMPLE: ImmutableMultiDict([('imported_datafile', <FileStorage: 'my_data.json' ('application/json')>)])
            #               where 'imported_datafile' originates from <input type="file" name="imported_datafile">
            #               and the name after FileStorage is the name of the file being uploaded

            print("request.args: ", request_obj.args)
            print("request.form: ", request_obj.form)
            # EXAMPLE: ImmutableMultiDict([('categoryID', '123'), ('pos', 888)])
            #               if the HTML form included <input type="hidden" name="categoryID" value="123">
            #                                     and <input type="hidden" name="pos" value="88">

            print("request.values: ", request_obj.values)
            print("request.json: ", request_obj.json)
            print("request.data: ", request_obj.data)
        # END if verbose


        # Locate the data about the desired file upload
        files_multi_dict = request_obj.files    # An ImmutableMultiDict object.  EXAMPLE:
                                                # ImmutableMultiDict([('some_label', <FileStorage: 'my_file.json' ('application/json')>)])
        if len(files_multi_dict) == 0:
            raise Exception(f"No files found in upload!  (The ImmutableMultiDict object in request.files is empty)")


        if key_name is not None:    # If a specific "name" (tag attached to uploaded file) was requested
            # Example from an invoking form:   <input type="file" name="some_key_to_refer_to_the_upload">
            if key_name not in request_obj.files:
                raise Exception(f"No file tagged with the label `{key_name}` found in the upload!  "
                                f"Check the `name` attribute in the HTML `input` tag (it should be '{key_name}').")

        else:                       # If no particular "name" (tag) was specified, just pick the first one
            key_name = list(files_multi_dict)[0]
            print(f"store_uploaded_file(): No specific key (tag associated with uploaded file) requested. "
                  f"The first key found in request.files (`{key_name}`) will be used.")


        f = files_multi_dict[key_name]      # f is a Werkzeug FileStorage object
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
        print(f"Name given to temporary file to upload to: `{tmp_filename_for_upload}`")

        print(f"Attempting to upload to directory `{upload_dir}`")

        full_filename = f"{upload_dir}{tmp_filename_for_upload}"    # EXAMPLE: "D:/tmp/my_file_being_uploaded.txt"
        f.save(full_filename)                                       # Create the temporary file, which concludes the upload

        return (tmp_filename_for_upload, full_filename, f.filename, f.mimetype)    # Normal termination



    @classmethod
    def secure_filename_BA(cls, filename: str) -> str:
        """
        ADAPTED FOR BRAIN ANNEX FROM werkzeug.utils.secure_filename(), version 0.5;
        blank spaces are no longer transformed to underscores,
        and round parentheses are no longer dropped.
        See: https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/

        Return a secure version of a filename.
        This filename can then safely be stored on a regular file system and passed
        to :func:`os.path.join`.  The filename returned is an ASCII only string
        for maximum portability.

        On windows systems the function also makes sure that the file is not
        named after one of the special device files.

        EXAMPLES:   secure_filename_BA("My cool ++ movie.mov")          -> 'My cool  movie.mov'
                    secure_filename_BA("../../../etc/passwd")           -> 'etc_passwd'
                    secure_filename_BA('i contain \xfcml\xe4uts.txt')   -> 'i contain umlauts.txt'
                    secure_filename_BA("    blank-padded string  ")     -> 'blank-padded string'
                    secure_filename_BA("COM1.txt")       [On Windows]   -> '_COM1.txt'

        WARNING: The function might return an empty filename.  It's your responsibility
        to ensure that the filename is unique and that you abort or
        generate a random filename if the function returned an empty one.

        :param filename:    A string with the filename to secure
        """
        _filename_ascii_strip_re = re.compile(r"[^A-Za-z0-9_. ()-]")  # List of allowed characters in the name;
                                                                      # note that the blank space and the round parentheses
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
        filename = filename.strip("._ ")         # Zap periods and underscores at the start or end of the string

        # On nt (such as Windows 7, etc) a couple of special files are present in each folder.  We
        # have to ensure that the target file is not such a filename; if it is, we prepend an underline
        if  (
                os.name == "nt"
                and filename
                and filename.split(".")[0].upper() in _windows_device_files
        ):
            filename = f"_{filename}"

        return filename





##########################################    IMAGES    ######################################################

class ImageProcessing:
    """
    Utility class for managing images, especially in the context of uploads.

    TODO: possibly move to a separate module (perhaps the plugin-specific file)

    SIDE NOTE: The "th" format from the Classic BrainAnnex, is:
    "default (largish) thumbs - 3 fit in a row" : width sized to 300

    formats =
    {
        "th": { "description": "default (largish) thumbs - 3 fit in a row",
                "size": 300,
                "affected": "w"
        }
    }
    """

    @classmethod
    def save_thumbnail(cls, src_folder: str, filename: str, save_to_folder: str,
                       src_width: int, src_height: int) -> None:
        """
        Make a thumbnail of the specified image, and save it in a file.
        The "th" thumbnail format is being followed.

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param save_to_folder:  Full path of folder where to save the resized file.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :return:                None.  In case of error, an Exception is raised
        """
        cls.scale_down_horiz(src_folder, filename, save_to_folder, src_width, src_height, target_width=300)



    @classmethod
    def scale_down_horiz(cls, src_folder: str, filename: str, save_to_folder: str,
                         src_width: int, src_height: int, target_width: int) -> None:
        """
        Resize an image to the target WIDTH, and save it in a file.

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param save_to_folder:  Full path of folder where to save the resized file.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :param target_width:    Desired pixel width of the resized image
        :return:                None.  In case of error, an Exception is raised
        """
        image = Image.open(src_folder + filename)

        resized_full_name = save_to_folder + filename

        if target_width >= src_width:   # Don't transform the image; just save it as it is
            image.save(resized_full_name)
        else:
            scaling_ratio = src_width / target_width    # This will be > 1 (indicative of reduction)
            print("scaling_ratio: ", scaling_ratio)
            target_height = int(src_height / scaling_ratio)
            new_image = image.resize((target_width, target_height))
            new_image.save(resized_full_name)



    @classmethod
    def get_image_size(cls, source_full_name) -> (int, int):
        """
        Return the size of the given image.

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/resized/my image.jpg"
        :return:                    The pair (width, height) with the image dimensions in pixels.  In case of error, an Exception is raised
        """
        image = Image.open(source_full_name)

        return image.size   # EXAMPLE: (1920, 1280)




    @classmethod
    def process_uploaded_image(cls, filename: str, fullname: str, media_folder: str) -> dict:
        """
        Obtain the size of the image, resize it to a thumbnail,
        save the thumbnail in the "resized/" subfolder of the specified media folder,
        and return a dictionary of properties that will go in the database

        :param filename:    EXAMPLE: "my image.jpg"
        :param fullname:    EXAMPLE (on Windows):  "D:/Docs/media/my image.jpg"
        :param media_folder: Name of the folder (including the final "/") where the media files are located.
                             The resized version will go in a "resized" subfolder of it.
                             EXAMPLE (on Windows):  "D:/Docs/media/

        :return:            A dictionary of properties that will go in the database, containing
                                the following keys: "caption", "basename", "suffix", "width", "height"
        """
        (width, height) = ImageProcessing.get_image_size(fullname)  # Extract the dimensions of the uploaded image

        # Create and save a thumbnail version
        ImageProcessing.save_thumbnail(src_folder = media_folder,
                                       filename = filename,
                                       save_to_folder = media_folder+"resized/",
                                       src_width=width, src_height=height)


        (basename, suffix) = os.path.splitext(filename)     # EXAMPLE: "test.jpg" becomes ("test", ".jpg")
        suffix = suffix[1:]     # Drop the first character (the ".")  EXAMPLE: "jpg"

        # Create a dictionary of properties that will go in the database
        properties = {"caption": basename,
                      "basename": basename, "suffix": suffix,
                      "width": width, "height": height}

        print(f"Uploaded image has width : {width} | height: {height}.  Thumbnail successfully created and stored")

        return properties




    @classmethod
    def describe_image(cls, source_full_name) -> None:
        """
        Print out some info about the given image.

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/media/resized/my image.jpg"
        :return:                    None.  In case of error, an Exception is raised
        """
        image = Image.open(source_full_name)

        # The file format
        print(image.format) # EXAMPLE: "JPEG" or "PNG"

        # The pixel format used by the image
        print(image.mode)   # Typical values are "RGB", "RGBA", "1", "L", "CMYK"

        # Image size, in pixels, as a 2-tuple (width, height)
        print(image.size)   # EXAMPLE: (1920, 1280)

        # Color palette table, if any
        print(image.palette) # EXAMPLE: None
