"""
2 classes:  MediaManager and ImageProcessing
"""


import os
import brainannex.exceptions as exceptions
from brainannex import GraphSchema
from PIL import Image



class MediaManager:
    """
    Helper library for the management of media files (documents and images)

    Static class that does NOT get instantiated;
    however, it must be initialized with calls to set_media_folder() and set_default_folders()
    """

    MEDIA_FOLDER = None # Location where the media for Content Items is stored, including the final "/"
                        # EXAMPLE on Windows: "D:/media/"
                        #                     (notice the forward slashes, even on Windows)
                        # This class variable gets set by initialize.py

    DEFAULT_FOLDERS = None  # A dict mapping a Class name to its designated default folder (a child of MEDIA_FOLDER)
                            # EXAMPLE: {"Document": "documents", "Image": "images", "Note": "notes"}
                            # This class variable gets set by initialize.py



    @classmethod
    def set_media_folder(cls, path_name: str) -> None:
        """

        :param path_name:   Location where the media for Content Items is stored, including the final "/"
                                EXAMPLE on Windows: "D:/media/"
                                (notice the forward slashes, even on Windows)
        :return:            None
        """
        # TODO: if path_name doesn't end with "/", add it

        cls.MEDIA_FOLDER = path_name



    @classmethod
    def set_default_folders(cls, folder_dict :dict) -> None:
        """

        :param folder_dict:
        :return:
        """
        cls.DEFAULT_FOLDERS = folder_dict



    @classmethod
    def default_file_path(cls, class_name :str, thumb=False) -> str:
        """
        Return the default file path, including the final "/", of the media files associated to the given schema Class

        :param class_name:  The name of the Class of the media item of interest
        :param thumb:       If True, then the "thumbnail" version is returned
                                (only applicable to some media types, such as images)
        :return:            The full file path, including the final "/"
                            EXAMPLES on Windows:
                                "D:/media/documents/"
                                "D:/media/images/resized/"
        """
        folder = cls.MEDIA_FOLDER    # Includes the final "/"
        assert folder is not None, \
            "lookup_file_path(): MEDIA_FOLDER must be set first.  Call MediaManager.set_media_folder()"

        default_folder = cls.DEFAULT_FOLDERS.get(class_name)

        folder += default_folder + "/"

        if thumb:
            folder += "resized/"

        return folder



    @classmethod
    def retrieve_full_path(cls, uri :str, thumb=False) -> str:
        """
        Return the full path for the specified media file or, if requested, for its thumbnail image.
        Includes the final "/"
        EXAMPLE (on Windows):  "D:/BACKUP_media/images/resized/"

        :param uri:         Unique identifier string for the Media Item of Interest
        :param thumb:       If True, return the folder for the thumbnail image instead
        :return:            EXAMPLES on Windows:
                                "D:/media/documents/"
                                "D:/media/images/resized/"
        """
        class_name = GraphSchema.class_of_data_node(node_id=uri, id_key="uri")

        dir_names = GraphSchema.follow_links(class_name=class_name, node_id=uri, id_key="uri",
                                             link_name="BA_stored_in", properties="name")
        #print("dir_names: ", dir_names)

        assert len(dir_names) < 2, \
            f"retrieve_folder_name(): more than 1 directory is associated with file with uri `{uri}`"

        if len(dir_names) == 0:     # No custom directory was specified
            return cls.default_file_path(class_name=class_name, thumb=thumb)    # including the final "/"

        folder_name = dir_names[0]

        if thumb:
            folder_name += "/resized"

        return cls.MEDIA_FOLDER + folder_name + "/"



    @classmethod
    def lookup_media_file(cls, uri :str, class_name, thumb=False) -> (str, str, str):
        """

        :param uri:     Unique identifier for the Media Item of interest
        :param class_name:
        :param thumb:   If True, return the folder for the thumbnail image instead;
                                ignored if the file suffix is "svg" (regardless of case),
                                because SVG files cannot be resized
        :return:        The triplet (filepath, basename, suffix)
                                Notes:  filepath ends with a "/"
                                        the basename is exclusive of path and of suffix
                                        the suffix does NOT include the dot
                                EXAMPLE:
                                    ("D:/media/my_media_folder/images/", "snap1", "jpg")
        """
        #TODO: maybe combine this method and retrieve_full_path()

        content_node = GraphSchema.get_single_data_node(node_id=uri, id_key="uri", class_name=class_name)
        #print("content_node:", content_node)
        if content_node is None:
            raise Exception(f'lookup_media_file(): Metadata not found for the Media file of Class `{class_name}` and uri="{uri}"')

        basename = content_node['basename']
        suffix = content_node['suffix']

        if suffix.lower() == "svg":
            thumb = False   # SVG files cannot be resized


        # Obtain the name of the folder for the content file or, if applicable, for its thumbnail image
        # Includes the final "/"
        folder = cls.retrieve_full_path(uri=uri, thumb=thumb)

        return (folder, basename, suffix)



    @classmethod
    def get_full_filename(cls, uri : str, class_name, thumb=False) -> str:
        """

        :param uri:     Unique identifier for the Media Item of Interest
        :param class_name:
        :param thumb:   If True, return the folder for the thumbnail image instead;
                                ignored if the file suffix is "svg" (regardless of case),
                                because SVG files cannot be resized
        :return:        EXAMPLE: "D:/media/my_media_folder/images/Tahiti vacation/"
        """
        (filepath, basename, suffix) = cls.lookup_media_file(uri=uri, class_name=class_name, thumb=thumb)
        filename = basename + "." + suffix

        full_path = cls.retrieve_full_path(uri=uri, thumb=thumb)
        full_file_name = full_path + filename

        return full_file_name



    @classmethod
    def get_from_text_file(cls, filename: str, path="", encoding="latin-1") -> str:
        """
        Read in and return the contents of the specified TEXT file.

        Note: 'utf8' encoding at times led to problems.
               More info: https://stackoverflow.com/questions/5552555/unicodedecodeerror-invalid-continuation-byte

        :param filename:    FULL filename, INCLUDING path - unless path is passed in the following argument
                                EXAMPLE on Windows:
                                "D:/media/my_file.txt"   (notice the forward slashes, even on Windows)
        :param path:        [OPTIONAL] String to prefix to the filename argument, above
        :param encoding:    A string such as "latin-1" (aka "iso-8859-1") or "utf8"
        :return:            The contents of the text file, using the requested encoding
        """
        full_file_name = path + filename

        with open(full_file_name, 'r', encoding=encoding) as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def get_from_binary_file(cls, path: str, filename: str) -> bytes:
        """
        Read in and return the contents of the specified BINARY file

        :param path:        String that must include a final "/", containing the full path of the file
                                EXAMPLE on Windows: "D:/media/" (notice the forward slashes, even on Windows)
        :param filename:    EXCLUSIVE of path.  EXAMPLE: "my pic.jpg"
        :return:            The contents of the binary file
        """
        full_file_name = path + filename
        with open(full_file_name, 'rb') as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def get_binary_content(cls, uri :str, class_name :str, th) -> (str, bytes):
        """
        Fetch and return the contents of a media item stored in a local file.
        In case of error, raise an Exception

        :param uri:         String identifier for a media item
        :param class_name:
        :param th:          If not None, then the thumbnail version is returned (only
                                applicable to images).
                                If the thumbnail version is not found, but the full-size image
                                is present, create and save a thumbnail file, prior to
                                returning the contents of the newly-created file

        :return:    The pair (filename suffix, binary data in the file)
        """
        # TODO: (at least for large media) read the file in blocks

        #print("In get_binary_content(): uri = ", uri)
        #content_node = GraphSchema.get_data_node(uri = uri)
        #print("content_node:", content_node)
        #if content_node is None:
            #raise Exception("get_binary_content(): Metadata for the Content Datafile not found")

        #basename = content_node['basename']
        #suffix = content_node['suffix']

        #folder = cls.lookup_file_path(schema_code=content_node['schema_code'], thumb=thumb)

        # Obtain the name of the folder for the content file or, if applicable, for its thumbnail image
        # Includes the final "/"
        folder, basename, suffix = cls.lookup_media_file(uri, class_name=class_name, thumb=th)

        filename = f"{basename}.{suffix}"   # Including the suffix.  EXAMPLE: "my_pic.jpg"

        try:
            file_contents = cls.get_from_binary_file(path=folder, filename=filename)
            return (suffix, file_contents)

        except Exception as ex:
            # File I/O failed
            error_msg = f"Reading of data file for Content Item `{uri}` failed: {ex}"
            print(error_msg)
            if not th:
                raise Exception(error_msg)
            else:
                # We looked for a thumbnail version, and didn't find it
                print("    Trying to use the full-size image instead of its thumb version...")

                # Attempt to resize the full-sized version, and save the new thumbnail file
                try:
                    # Get the folder for the full-size images
                    images_folder = cls.retrieve_full_path(uri=uri, thumb=False)
                    source_full_name = images_folder + filename
                    print(f"    Looking up info on the full-sized image in file `{source_full_name}`")

                    # Full-size version was found; obtain its dimensions
                    width, height = ImageProcessing.get_image_size(source_full_name)
                    # Create a thumbnail version
                    thumb_folder = cls.retrieve_full_path(uri=uri, thumb=th)
                    # Carry out the resizing, and save the thumbnail file
                    print("    Attempting to create a thumbnail version of it")
                    #print(f"    src_folder=`{images_folder}` | filename=`{filename}` | save_to_folder=`{thumb_folder}` | "
                    #      f"src_width={width} | src_height={height}")
                    ImageProcessing.save_thumbnail(src_folder=images_folder, filename=filename, save_to_folder=thumb_folder,
                                                   src_width=width, src_height=height)
                    # Get the contents of the newly-created thumbnail file
                    file_contents = cls.get_from_binary_file(path=folder, filename=filename)
                    return (suffix, file_contents)

                except Exception as ex:
                    # Failed to resize the file, or to read in the resized file
                    error_msg = f"    Unable resize the image ({filename}), or to read the resized file. {ex}\n" \
                                f"    Attempting to return the full-sized file instead"
                    print(error_msg)

                    # One last attempt: try to read in and return the full-sized version
                    try:
                        file_contents = cls.get_from_binary_file(path=images_folder, filename=filename)
                        return (suffix, file_contents)
                    except Exception as ex:
                        # File I/O failed
                        error_msg = f"Unable to load the full-size version of image, either. {ex}"
                        print(error_msg)
                        raise Exception(error_msg)



    @classmethod
    def before_update_content(cls, uri :str, set_dict :dict, class_name :str) -> None:
        """
        Invoked before a Media Item of this type gets updated in the database

        :param uri:         Unique identifier for the Media Item of Interest
        :param set_dict:    A dict of field values to eventually set into the database
        :param class_name:
        :return:            None
        """
        #print(f"In before_update_content() - uri: `{uri}` | class_name: `{class_name}` | set_dict: {set_dict}")
        basename = set_dict.get("basename")
        suffix =   set_dict.get("suffix")

        if basename or suffix:
            if basename:
                check = cls.check_file_name(basename)
                assert check == "", \
                    f"before_update_content(): Non-acceptable character found in destination file name: {check}"

            folder, old_basename, old_suffix = cls.lookup_media_file(uri, class_name=class_name)
            #folder = cls.lookup_file_path(class_name=class_name)
            old_full_name = f"{folder}{old_basename}.{old_suffix}"

            new_basename = basename if basename else old_basename
            new_suffix = suffix if suffix else old_suffix
            new_full_name = f"{folder}{new_basename}.{new_suffix}"

            if new_full_name != old_full_name:
                print(f"MediaManager.before_update_content(): attempting to move media file from `{old_full_name}` to `{new_full_name}`")
                cls.move_file(src=old_full_name, dest=new_full_name)



    @classmethod
    def save_into_file(cls, contents: str, filename: str, class_name :str) -> None:
        """
        Save the given data into the specified file in the class-wide media folder.  UTF8 encoding is used.
        In case of error, detailed Exceptions are raised

        :param contents:    String to store into the file
        :param filename:    EXCLUSIVE of file path
        :param class_name:  Needed to determine the default folder location (which is based on class_name)
        :return:            None.  In case of errors, detailed Exceptions are raised
        """

        folder = cls.default_file_path(class_name=class_name)
        full_file_name = folder + filename

        try:
            f = open(full_file_name, "w", encoding='utf8')
        except Exception as ex:
            raise Exception(f"save_into_file(): Unable to open file {full_file_name} for writing. {ex}")

        try:
            f.write(contents)
        except Exception as ex:
            raise Exception(f"save_into_file(): Unable write data to file {full_file_name}. "
                            f"First 20 characters: `{contents[:20]}`. {exceptions.exception_helper(ex)}")

        f.close()



    @classmethod
    def delete_media_file(cls, uri: str, class_name :str, thumb=False) -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param uri:         Unique identifier for the Media Item of Interest
        :param class_name:
        :param thumb:       If True, then the "thumbnail" version is deleted
                                (only applicable to some media types, such as images)
        :return:            True if successful, or False otherwise
        """
        full_file_name = cls.get_full_filename(uri, class_name=class_name, thumb=thumb)

        return cls.delete_file(full_file_name)



    @classmethod
    def delete_file(cls, fullname: str) -> bool:
        """
        Delete the specified file

        :param fullname:    Full name of the file to delete, including its path
        :return:            True if successful, or False if file was not found
        """

        if os.path.exists(fullname):
            os.remove(fullname)
            return True
        else:
            return False    # "The file does not exist"



    @classmethod
    def move_file(cls, src: str, dest: str) -> None:
        """
        Rename (move) the specified file.
        An Exception is raised if the file was not found,
        or if another file with new name already exists

        :param src:    Old full name (incl. path) of the file to rename
        :param dest:   New full name (incl. path) of the file to rename
        :return:       None
        """
        assert src != dest, \
            f"move_file(): The requested source and destination file names are the same! (`{src}`)"

        assert os.path.exists(src), \
            f"move_file(): The requested file `{src}` does not exist"

        assert not os.path.exists(dest), \
            f"move_file(): A file with the requested destination name (`{dest}`) already exists"


        os.rename(src, dest)



    @classmethod
    def check_file_name(cls, filename :str) -> str:
        """
        Check the given filename against a list of acceptable filename characters, based on a slightly-expanded
        (but still conservative) version of the POSIX portable file name character set
        https://www.ibm.com/docs/en/zos/3.1.0?topic=locales-posix-portable-file-name-character-set

        :return:    The first non-allowed character, if applicable;
                        if all characters are good, return ""
        """
        allowed_chars = " .,-_()&@0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for character in filename:
            if character not in allowed_chars:
                return character

        return ""



    @classmethod
    def get_mime_type(cls, suffix :str) -> str:
        """
        Return the appropriate MIME type for file content type assumed from the
        filename extension, assuming normal conventions are being followed

        :param suffix:  A string with a filename's suffix (i.e. the "file extension type".)
                            EXAMPLES: "jpg" or "PDF"
        :return:        A string describing the MIME type for files of that particular type
        """
        mime_mapping = {'jpg': 'image/jpeg',
                        'png': 'image/png',
                        'gif': 'image/gif',
                        'bmp': 'image/bmp',
                        'svg': 'image/svg+xml',

                        'txt': 'text/plain',
                        'pdf': 'application/pdf',
                        'docx': 'application/msword',
                        'doc': 'application/msword',
                        'xlsx': 'application/vnd.ms-excel',
                        'xls': 'application/vnd.ms-excel',

                        'ppt' : 'application/vnd.ms-powerpoint',
                        'pptx' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',

                        'zip': 'application/zip'
                        }   # TODO: add more MIME types, when more plugins are introduced

        default_mime = 'application/save'   # TODO: not sure if this is the best default. Test!

        mime_type = mime_mapping.get(suffix.lower(), default_mime)

        return mime_type



    @classmethod
    def locate_orphan_media_NOT_YET_USED(cls, directory: str, db) -> [str]:    # TODO: finish implementing
        """
        Locate files in a LOCAL directory
        that lack a corresponding database record (for now, just considering Notes)

        :param directory:   EXAMPLE:  "D:/tmp/transfer"  (Use forward slashes even on Windows!)
        :param db:          Object of type "GraphAccess"; TODO: should be able to avoid it
                                                              by using the GraphSchema layer instead
        :return:            A list of names of "orphaned" file s
        """
        file_list = os.listdir(directory)
        print(f"Total number of files: {len(file_list)}")

        # Locate files that lack a database record
        orphans = []
        for filename in file_list:
            #print(filename)
            (basename, suffix) = os.path.splitext(filename)
            q = f"MATCH (n:Note) WHERE n.basename='{basename}' AND n.suffix='htm' RETURN COUNT(n) AS number_nodes"
            n = db.query(q, single_cell="number_nodes")
            if n == 0:
                print(f"Notes record for file `{filename}`  NOT FOUND!")
                orphans.append(filename)

        return orphans





##########################################    IMAGES    ######################################################

class ImageProcessing:
    """
    Utility class for managing images, especially in the context of uploads.

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
            #print("scaling_ratio: ", scaling_ratio)
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
    def process_uploaded_image(cls, media_folder :str, basename :str, suffix :str) -> dict:
        """
        If possible, obtain the size of the image, resize it to a thumbnail,
        save the thumbnail in the "resized/" subfolder of the specified media folder;
        not all images (such as SVG's) can be resized.

        Return a dictionary of additional image-specific properties that will go in the database.

        :param media_folder:Name of the folder (including the final "/") where the media files are located.
                                The resized version will go in a "resized" subfolder of it.
                                EXAMPLE (on Windows):  "D:/Docs/media/
        :param basename:    EXAMPLE: "my image"
        :param suffix:      EXAMPLE: "jpg"  .  It's ok to be an empty string

        :return:            A dictionary of extra properties to store in database, containing some or all of
                                the following keys: "caption", "width", "height"
        """
        filename = basename
        if suffix:
            filename += f".{suffix}"    # EXAMPLE: "my image.jpg"

        fullname = media_folder + filename  # EXAMPLE (on Windows):  "D:/Docs/media/my image.jpg"

        try:
            # Note: image types such as SVG will lead to an Exception
            (width, height) = ImageProcessing.get_image_size(fullname)  # Extract the dimensions of the uploaded image

            # Create and save a thumbnail version
            ImageProcessing.save_thumbnail(src_folder = media_folder,
                                           filename = filename,
                                           save_to_folder = media_folder+"resized/",
                                           src_width=width, src_height=height)

            print(f"process_uploaded_image(): Uploaded image has width {width} , height: {height}.  "
                  f"Thumbnail successfully created and stored")
            properties = {"caption": basename, "width": width, "height": height}
        except Exception as ex:
            print("process_uploaded_image(): Unable to resize image")
            properties = {"caption": basename}


        return properties    # A dictionary of additional image-specific properties that will go in the database



    @classmethod
    def describe_image(cls, source_full_name) -> None:
        """
        Print out some info about the given image:
        the file format, the pixel format, the image size and (if any) the color palette

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
