"""
2 classes:  MediaManager and ImageProcessing
"""


import os
import shutil
import brainannex.exceptions as exceptions
from brainannex import GraphSchema
from app_libraries.PLUGINS.plugin_manager import PluginManager
from PIL import Image
from pathlib import Path



class MediaManager:
    """
    Helper library for the management of media files (documents and images)

    Static class that does NOT get instantiated;
    however, it must be initialized with calls to set_media_folder() and set_default_folders()

    Two broad categories of operations:
        1) database operations
        2) file-system operations

    Gradually, this library will conform to the following nomenclature;
    given, for example, a file "C:\folder_1\folder_2\my_file.txt" :

    | String                                          | Term               |
    | ----------------------------------------------- | ------------------ |
    | `txt`                                           | extension          |
    | `my_file`                                       | stem               |
    | `my_file.txt`                                   | filename           |
    | `folder_2`                                      | directory name     |
    | `/folder_1/folder_2` or `C:\folder_1\folder_2`  | directory path     |
    | `/folder_1/folder_2/my_file.txt`                | file path          |
    | `C:\folder_1\folder_2\my_file.txt`              | absolute file path |
     """

    MEDIA_FOLDER = None # Location where the media for Content Items is stored, including the final "/"
                        # EXAMPLE on Windows: "D:/media/"
                        #                     (notice the forward slashes, even on Windows)
                        # This class variable gets set by initialize.py

    DEFAULT_FOLDERS = {}    # A dict mapping a Class name to its designated default folder
                            # (a subfolder of cls.MEDIA_FOLDER)
                            # EXAMPLE: {"Document": "documents",
                            #           "Image": "images",
                            #           "Note": "notes"}
                            # This class variable gets set by initialize.py

    RESIZED_FOLDER = "_resized/"    # TODO: this ought to be managed by the Images class



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this module:
        that includes the Classes "Media" and "Directory"

        :return:    None
        """
        if not GraphSchema.class_name_exists("Media"):
            GraphSchema.create_class_with_properties(name="Media", strict=False,
                                                     properties=["basename", "suffix"])
            if GraphSchema.class_name_exists("Content Item"):   # TODO: maybe "Content Item" should be created here, if needed. Currently done by Categories
                GraphSchema.create_class_relationship(from_class="Media", to_class="Content Item", rel_name="INSTANCE OF")

        if not GraphSchema.class_name_exists("Directory"):
            GraphSchema.create_class_with_properties(name="Directory", strict=False,
                                                     properties=["name", "description"])
            GraphSchema.create_class_relationship(from_class="Media", to_class="Directory", rel_name="BA_stored_in")



    @classmethod
    def set_media_folder(cls, path_name :str) -> None:
        """
        Initialize the class variable MEDIA_FOLDER with the given data.
        If path_name doesn't end with "/", add it

        :param path_name:   Location where the media for Content Items is stored, including the final "/"
                                EXAMPLE on Windows: "D:/media/"
                                (notice the forward slashes, even on Windows)
        :return:            None
        """
        # TODO: verify that the given folder actually exists

        assert type(path_name) == str, \
            f"MediaManager.set_media_folder(): the argument `path_name` must be a string.  " \
            f"The passed argument ({path_name}) was of type {type(path_name)}"

        cls.MEDIA_FOLDER = path_name.rstrip("/") + "/"  # Always add a final "/" (after first removing it, if present)



    @classmethod
    def get_media_folder(cls) -> str:
        """
        Location where the media for Content Items is stored, including the final "/"

        :return:    EXAMPLE on Windows: "D:/media/"
                        (notice the forward slashes, even on Windows)
        """
        return cls.MEDIA_FOLDER


    @classmethod
    def set_default_folders(cls, folder_dict :dict) -> None:
        """
        Initialize the class variable DEFAULT_FOLDERS with the given data

        :param folder_dict: A dict mapping a Class name to its designated default folder (a subfolder of cls.MEDIA_FOLDER)
                                EXAMPLE: {"Document": "documents", "Image": "images", "Note": "notes"}
        :return:            None
        """
        cls.DEFAULT_FOLDERS = folder_dict



    @classmethod
    def default_file_path(cls, class_name :str, thumb=False) -> str:
        """
        Return the default file path, including the final "/", of the media files associated to the given schema Class
        Note: some schema Classes are associated to subfolders, as specified by set_default_folders()

        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
                                If no special subfolder was registered for this Class, then the starting point is just
                                the global MEDIA_FOLDER
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

        if default_folder:
            folder += default_folder + "/"

        if thumb:
            folder += cls.RESIZED_FOLDER

        return folder



    @classmethod
    def retrieve_full_path(cls, uri :str, thumb=False) -> str:
        """
        Return the full path for the specified media file or, if requested, for its thumbnail image.
        Includes the final "/"

        :param uri:         Entity ID for the Media Item of Interest        TODO: also needs Class name
        :param thumb:       If True, return the folder for the thumbnail image instead
        :return:            EXAMPLES on Windows:
                                "D:/media/documents/"
                                "D:/media/images/resized/"
        """
        class_name = GraphSchema.class_of_data_node(node_id=uri, id_key="entity_id")

        dir_names = GraphSchema.follow_links(class_name=class_name, node_id=uri, id_key="entity_id",
                                             link_name="BA_stored_in", properties="name")
        #print("dir_names: ", dir_names)

        assert len(dir_names) < 2, \
            f"retrieve_folder_name(): more than 1 directory is associated with file with uri `{uri}`"

        if len(dir_names) == 0:     # No custom directory was specified
            return cls.default_file_path(class_name=class_name, thumb=thumb)    # including the final "/"

        folder_name = dir_names[0]

        if thumb:
            return cls.MEDIA_FOLDER + folder_name + "/" + cls.RESIZED_FOLDER

        return cls.MEDIA_FOLDER + folder_name + "/"



    @classmethod
    def get_media_item_file_by_entity(cls, entity_id :str, class_name :str) -> (str, str, str):
        """
        Retrieve the full file path, basename and suffix of the a media item identified by its Class and Entity ID.

        :param entity_id:   Unique identifier string (within the given Class)
                                for the Media Item of Interest
        :param class_name:  Name of the Schema Class for the desired media Item.
                                EXAMPLE: "Image", "Note", "Document"

        :return:            The triplet (directory path, stem, extension)
                                Notes:  - the directory path ends with a "/" (even on Windows)
                                        - stem is the file basename exclusive of path and of suffix
                                        - extension (the suffix) does NOT include the dot
                                EXAMPLES:
                                    ("D:/media/my_media_folder/images/", "my_pict", "jpg")
                                    ("D:/media/my_media_folder/my_custom_directory/vacation/", "my_pict", "jpg")
        """
        content_node = GraphSchema.get_single_data_node(node_id=entity_id, id_key="entity_id", class_name=class_name)
        #print("content_node:", content_node)
        if content_node is None:
            raise Exception(f'get_media_item_file_by_entity(): '
                            f'Metadata not found for the Media file of Class `{class_name}` and Entity ID "{entity_id}"')

        basename = content_node['basename']
        suffix = content_node['suffix']

        dir_names = GraphSchema.follow_links(class_name=class_name, node_id=entity_id, id_key="entity_id",
                                             link_name="BA_stored_in", properties="name")
        #print("dir_names: ", dir_names)

        assert len(dir_names) < 2, \
            f"get_media_item_file(): more than 1 directory is associated " \
            f"with the media file of Class {class_name} and Entity ID `{entity_id}`"

        if len(dir_names) == 0:     # No custom directory was specified
            path = cls.default_file_path(class_name=class_name)    # including the final "/"
        else:
            folder_name = dir_names[0]
            path = cls.MEDIA_FOLDER + folder_name + "/"


        return (path, basename, suffix)



    @classmethod
    def get_media_item_file(cls, internal_id : int|str) -> (str, str, str):
        """
        Retrieve the directory path, stem and suffix of the a media item identified by its internal database ID

        :param internal_id: Internal database ID to identify the Data Node for the Media Item of interest

        :return:            The triplet (directory path, stem, extension)
                                Notes:  - the directory path ends with a "/" (even on Windows)
                                        - stem is the file basename exclusive of path and of suffix
                                        - extension (the suffix) does NOT include the dot
                                EXAMPLE:
                                    ("D:/media/my_media_folder/images/", "my_pict", "jpg")
        """
        content_node = GraphSchema.get_single_data_node(node_id=internal_id, hide_schema=False)
        #print("content_node:", content_node)
        assert content_node is not None, \
                    f'get_media_item_file_by_id(): Metadata not found for the Media file ' \
                    f'with internal database ID {internal_id}'

        basename = content_node['basename']
        suffix = content_node['suffix']
        class_name = content_node['_CLASS']

        dir_names = GraphSchema.follow_links(class_name=class_name, node_id=internal_id,
                                             link_name="BA_stored_in", properties="name")
        #print("dir_names: ", dir_names)

        assert len(dir_names) < 2, \
            f"get_media_item_file(): more than 1 directory is associated " \
            f"with the media file with internal database ID {internal_id}`"

        if len(dir_names) == 0:     # No custom directory was specified
            path = cls.default_file_path(class_name=class_name)    # including the final "/"
        else:
            folder_name = dir_names[0]
            path = cls.MEDIA_FOLDER + folder_name + "/"


        return (path, basename, suffix)



    @classmethod
    def lookup_media_file(cls, entity_id :str, class_name :str, thumb=False) -> (str, str, str):
        """

        :param entity_id:   Together with the Class name, this string provides
                                a unique identifier for the Media Item of interest
        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
        :param thumb:       If True, return the folder for the thumbnail image instead;
                                ignored if the file suffix is "svg" (regardless of case),
                                because SVG files cannot be resized
        :return:            The triplet (filepath, basename, suffix)
                                Notes:  filepath ends with a "/"
                                        the basename is exclusive of path and of suffix
                                        the suffix does NOT include the dot
                                EXAMPLE:
                                    ("D:/media/my_media_folder/images/", "snap1", "jpg")
        """
        #TODO: phase out in favor of get_media_item_file_by_entity()

        content_node = GraphSchema.get_single_data_node(node_id=entity_id, id_key="entity_id", class_name=class_name)
        #print("content_node:", content_node)
        if content_node is None:
            raise Exception(f'lookup_media_file(): Metadata not found for the Media file of Class `{class_name}` and uri="{entity_id}"')

        basename = content_node['basename']
        suffix = content_node['suffix']

        if suffix.lower() == "svg":
            thumb = False   # SVG files cannot be resized


        # Obtain the name of the folder for the content file or, if applicable, for its thumbnail image
        # Includes the final "/"
        folder = cls.retrieve_full_path(uri=entity_id, thumb=thumb)

        return (folder, basename, suffix)



    @classmethod
    def get_full_filename_thumb(cls, entity_id :str, class_name :str) -> str:
        """
        Get the full filename for the THUMBNAIL-image version

        :param entity_id:   Together with the Class name, this string provides
                                a unique identifier for the Media Item of interest
        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
        :param thumb:       If True, return the folder for the thumbnail image instead;
                                ignored if the file suffix is "svg" (regardless of case),
                                because SVG files cannot be resized
        :return:            EXAMPLE: "D:/media/my_media_folder/images/Tahiti vacation/"
        """
        # TODO: dispatch to appropriate plugin
        (filepath, basename, suffix) = cls.lookup_media_file(entity_id=entity_id, class_name=class_name, thumb=True)
        filename = basename + "." + suffix

        full_path = cls.retrieve_full_path(uri=entity_id, thumb=True)
        full_file_name = full_path + filename

        return full_file_name


    @classmethod
    def get_absolute_file_path(cls, entity_id :str, class_name :str) -> str:
        """
        Get the absolute file path of the media file linked to the given Media Content Item

        :param entity_id:   Unique identifier string (within the given Class)
                                for the Media Item of Interest
        :param class_name:  Name of the Schema Class for the desired media Item.
                                EXAMPLE: "Image", "Note", "Document"

        :return:            EXAMPLE: "D:/media/my_media_folder/images/snap1.jpg"
        """
        (filepath, basename, suffix) = cls.get_media_item_file_by_entity(class_name=class_name, entity_id=entity_id)
        filename = basename + "." + suffix

        full_path = cls.retrieve_full_path(uri=entity_id)
        full_file_name = full_path + filename

        return full_file_name


    @classmethod
    def get_full_filename(cls, entity_id :str, class_name :str, thumb=False) -> str:
        """

        :param entity_id:   Together with the Class name, this string provides
                                a unique identifier for the Media Item of interest
        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
        :param thumb:       If True, return the folder for the thumbnail image instead;
                                ignored if the file suffix is "svg" (regardless of case),
                                because SVG files cannot be resized
        :return:            EXAMPLE: "D:/media/my_media_folder/images/snap1.jpg"
        """
        # Dispatch based on the `thumb` argument
        if thumb:
            return cls.get_full_filename_thumb(entity_id=entity_id, class_name=class_name)
        else:
            return cls.get_absolute_file_path(entity_id=entity_id, class_name=class_name)



    @classmethod
    def get_binary_content(cls, entity_id :str, class_name :str, th) -> (str, bytes):
        """
        Fetch and return the contents of a media item stored in a local file.
        In case of error, raise an Exception

        :param entity_id:   Unique identifier string (within the given Class) for a media Item
        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
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
        folder, basename, suffix = cls.lookup_media_file(entity_id, class_name=class_name, thumb=th)

        filename = f"{basename}.{suffix}"   # Including the suffix.  EXAMPLE: "my_pic.jpg"

        try:
            file_contents = cls.get_from_binary_file(path=folder, filename=filename)
            return (suffix, file_contents)

        except Exception as ex:
            # File I/O failed
            error_msg = f"Reading of data file for Content Item `{entity_id}` failed: {ex}"
            print(error_msg)
            if not th:
                raise Exception(error_msg)
            else:
                # We looked for a thumbnail version, and didn't find it
                print("    Trying to use the full-size image instead of its thumb version...")

                # Attempt to resize the full-sized version, and save the new thumbnail file
                try:
                    # Get the folder for the full-size images
                    images_folder = cls.retrieve_full_path(uri=entity_id, thumb=False)
                    source_full_name = images_folder + filename
                    print(f"    Looking up info on the full-sized image in file `{source_full_name}`")

                    # Full-size version was found; obtain its dimensions
                    width, height = ImageProcessing.get_image_size(source_full_name)
                    # Create a thumbnail version
                    thumb_folder = cls.retrieve_full_path(uri=entity_id, thumb=th)
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
    def rename_media_file(cls, folder :str,
                          old_basename :str, old_suffix :str,
                          new_basename=None, new_suffix=None,
                          ignore_missing=False) -> None:
        """
        An Exception is raised if the file was not found,
        or if another file with new name already exists

        :param folder:          Full name of the folder (directory) where the media file resides,
                                    optionally including the final "/"
                                    EXAMPLE (on Windows):   "D:/media/my_media_folder/"  (FORWARD slashes!)
        :param old_basename:    EXAMPLE: "my pict"
        :param old_suffix:      EXAMPLE: "jpg"
        :param new_basename:    [OPTIONAL]
        :param new_suffix:      [OPTIONAL]
        :param ignore_missing:  [OPTIONAL]  If True, no error is raised if the old file is missing;
                                    default is False
        :return:                None
        """
        if (new_basename is None) and (new_suffix is None):
            return  # Nothing to do

        # Add a final slash, if not already provided
        if folder[-1] != "/":
            folder += "/"

        # If new names aren't available, re-use the old ones
        if new_basename:
            bad_character = MediaManager.check_valid_file_name(new_basename)
            assert bad_character == "", \
                f"MediaManager.rename_media_file(): The intended destination file name ({new_basename}) contains a non-acceptable character: {bad_character}"
        else:
            new_basename = old_basename

        if new_suffix:
            bad_character = MediaManager.check_valid_file_extension(new_suffix)
            assert bad_character == "", \
                f"MediaManager.rename_media_file(): The intended destination file suffix ({new_suffix}) contains a non-acceptable character: {bad_character}"
            assert len(new_suffix) < 5, \
                f"MediaManager.rename_media_file(): The intended destination file suffix ({new_suffix}) is too long ({len(new_suffix)} characters)"

        else:
            new_suffix = old_suffix


        old_full_name = f"{folder}{old_basename}.{old_suffix}"
        new_full_name = f"{folder}{new_basename}.{new_suffix}"

        if new_full_name != old_full_name:
            print(f"MediaManager.rename_media_file(): attempting to move media file from `{old_full_name}` to `{new_full_name}`")
            if not ignore_missing or os.path.exists(old_full_name):
                cls.move_file(src=old_full_name, dest=new_full_name)



    @classmethod
    def delete_media_file(cls, uri: str, class_name :str, thumb=False) -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param uri:         Unique identifier for the Media Item of Interest
        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
        :param thumb:       If True, then the "thumbnail" version is deleted
                                (only applicable to some media types, such as images)
        :return:            True if successful, or False otherwise
        """
        full_file_name = cls.get_full_filename(uri, class_name=class_name, thumb=thumb)

        return cls.delete_file(full_file_name)



    @classmethod
    def assert_valid_file_path(cls, file_path :str) -> None:
        """
        Raise an Exception if the given file path isn't a valid string.

        EXAMPLES:   "a/bad?name" , or "COM" if on Windows, will raise Exceptions
                    "a/good name! (Indeed, just so 123).txt"  will be fine

        :param file_path:   A file part (or absolute file path), such as
                                "folder_1/my_file"  or  "C:\folder_1\my_file.txt"
        :return:            None
        """
        INVALID_CHARS = r'<>:"/\\|?*'

        RESERVED_NAMES = {  # Forbidden on Windows7+ on as any path component
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10)),
        }

        p = Path(file_path)

        for part in p.parts:
            if part in (".", ".."):
                continue

            if part == p.anchor:
                continue            # To accept the the filesystem root, such as "/", "\" or "D:\"

            if any(ch in part for ch in INVALID_CHARS):
                raise ValueError(f"Invalid name of filepath component: {part}")

            if os.name == "nt":     # If on Windows7+ or Windows Server variants
                stem = Path(part).stem.upper()
                if stem in RESERVED_NAMES:
                    raise ValueError(f"Reserved Windows name of filepath component: `{part}`")



    @classmethod
    def check_valid_file_name(cls, filename :str) -> str:
        """
        Check the given filename against a list of acceptable filename characters, based on a slightly-expanded
        (but still conservative) version of the POSIX portable file name character set
        https://www.ibm.com/docs/en/zos/3.1.0?topic=locales-posix-portable-file-name-character-set

        :filename:  A string with the file name (EXCLUSIVE of extension) to examine
        :return:    The first non-allowed character, if applicable;
                        if all characters are good, return ""
        """
        #TODO: if on Window, also reject reserved names; see secure_filename_BA()
        ALLOWED_CHARS = " .,-_()&@0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for character in filename:
            if character not in ALLOWED_CHARS:
                return character

        return ""


    @classmethod
    def check_valid_file_extension(cls, suffix :str) -> str:
        """
        Check the given filename extension (suffix) against a list of acceptable characters,
        based on a very conservative approach.
        No check is done on the length

        :suffix:    A string with the filename extension (EXCLUSIVE of the dot ".") to examine
        :return:    The first non-allowed character, if applicable;
                        if all characters are good, return ""
        """
        ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"   # TODO: consider expanding

        for character in suffix:
            if character not in ALLOWED_CHARS:
                return character

        return ""



    @classmethod
    def split_absolute_file_path(cls, absolute_file_path :str) -> (str, str, str):
        """
        Break up an absolute file path into the triplet (directory, stem, extension)

        :param absolute_file_path:  EXAMPLE: r"C:\folder_1\folder_2\my_file.txt"
        :return:                    The triplet (directory, stem, extension)
                                        EXAMPLE: (r"C:\folder_1\folder_2", "my_file", "txt")
        """
        p = Path(absolute_file_path)

        directory = str(p.parent)           # EXAMPLE: r"C:\folder_1\folder_2"
        stem = p.stem                       # EXAMPLE: "my_file"
        extension = p.suffix.lstrip(".")    # EXAMPLE: "txt"

        '''
        print(directory)
        print(stem)
        print(extension)
        '''
        return (directory, stem, extension)



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
    def create_missing_media_folder(cls, class_name :str) -> None:
        """
        Attempt to create a presumably-missing media folder for the media associated to the given schema Class.
        If the folder already exists, no action taken.

        :param class_name:  Name of the Schema Class for the desired media Item.  EXAMPLE: "Image", "Note", "Document"
        :return:            None
        """
        folder_name = cls.DEFAULT_FOLDERS.get(class_name)   # EXAMPLE: "documents"
        if folder_name:
            dir_to_create = cls.MEDIA_FOLDER + folder_name  # EXAMPLE: "D:/media/documents"
            cls.create_folder(dir_to_create)



    @classmethod
    def locate_orphan_media_NOT_YET_USED(cls, directory: str, db) -> [str]:
        """
        # TODO: finish implementing
        Locate files in a LOCAL directory
        that lack a corresponding database record (for now, just considering Notes)

        :param directory:   EXAMPLE:  "D:/tmp/transfer"  (Use forward slashes even on Windows!)
        :param db:          Object of type "GraphAccess"; TODO: should be able to avoid it
                                                                by using the GraphSchema layer instead
        :return:            A list of names of "orphaned" files
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



    #####################################################################################################

    '''                            ~   DATABASE_OPERATIONS   ~                                '''

    def ________DATABASE_OPERATIONS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################


    @classmethod
    def get_media_directories(cls, limit=100) -> [str]:
        """
        Extract the list of all registered directories (sorted by name, ignoring case).

        :param limit:       [OPTIONAL] Max number of directory names to return

        :return:            The (possibly empty) sorted list of all directory names
                                EXAMPLE:

                                        [
                                            "documents/Ebooks & Articles/SYSTEMS BIO",
                                            "documents/Ebooks & Articles/math"
                                        ]
        """
        result, _ = GraphSchema.get_nodes_by_filter(class_name="Directory",
                                                    order_by="name", sort_ignore_case=["name"],
                                                    limit=limit)
        #print(result)
        #TODO: let get_nodes_by_filter() extract the desired single field
        directory_list = [d.get("name") for d in result]
        #print(directory_list)
        return directory_list



    @classmethod
    def media_directory_stored_in(cls, internal_id :str|int) -> str|None:
        """
        Extract the directory location of the given Content Item

        :param internal_id: To identify the Media Content Item of interest

        :return:            The media-directory path of the specified Content Item,
                                if applicable (or None otherwise)

                                EXAMPLE:    "documents/Ebooks & Articles/SYSTEMS BIO"
        """
        result = GraphSchema.db.follow_links(match=internal_id,
                                     rel_name="BA_stored_in", rel_dir="OUT",
                                     neighbor_labels="Directory")
        assert len(result) <= 1, \
            f"media_directory_stored_in(): found MULTIPLE locations ({len(result)})   " \
            f"for the Content Item with internal_id {internal_id}"

        if len(result) == 1:
            location = result[0].get("name")
        else:
            location = None

        return location



    @classmethod
    def create_media_directory(cls, name :str, entity_id=None) -> int | str:
        """
        Create a new media subdirectory, both in the database and in the file system

        :param name:        No final "/".  Don't include the general media-folder prefix.
                                EXAMPLE:  "images/vacation/Tahiti"
                                If it already exists in the database, an Exception will be raised;
                                no harm if it already exists in the file system
        :param entity_id:   [OPTIONAL] If a string is passed, then a field (node property) called "entity_id"
                                is set to that value
        :return:            The internal database ID of the new data node just created
        """
        # TODO: be lenient of "/" at either end
        # TODO: more pytests about bad names
        dirs_list = MediaManager.get_media_directories()
        #print(dirs_list)

        assert name not in dirs_list, \
            f"create_media_directory(): a directory named `{name}` is already registered in the database"

        directory_path = cls.get_media_folder() + name
        #print("directory_path: ", directory_path)   # EXAMPLE: "D:/media/my_media_folder/my documents/chapter 1"
        cls.create_folder(directory_path)           # No problem if already exists

        # Create a new directory (just its metadata)
        return GraphSchema.create_data_node(class_name="Directory", properties={"name": name},
                                            new_entity_id=entity_id)



    @classmethod
    def move_media_item(cls, internal_id :int|str, media_directory :str) -> None:
        """
        Move the specified media item to the given media directory.
        This operation will affect both the file system and the database.
        TODO: also need to move "covers" or "thumbnails"

        :param internal_id:     To identify the Media Item of interest
        :param media_directory: The desired media directory (which must already exist)
                                    EXAMPLE: "images/family outings"
        :return:                None
        """
        # Verify that the requested media directory is already present in the database
        dirs_list = cls.get_media_directories()
        #print("dirs_list: ", dirs_list)
        assert media_directory in dirs_list, \
            f"move_media_item(): a media directory named `{media_directory}` " \
            f"first needs to be created with create_media_directory()"

        # Find the current directory for the requested Media Content Item
        dir = cls.media_directory_stored_in(internal_id)
        #print("\ndir: ", dir)
        # Make sure that it isn't already equal to the specified new directory path
        assert media_directory != dir, \
            f"move_media_item(): the requested Media Item (internal database ID {internal_id}) " \
            f"is ALREADY located in the specified new destination directory (`{media_directory}`)"

        # Look up in the database the metadata of the requested Media Content Item
        directory_path, stem, extension = MediaManager.get_media_item_file(internal_id=internal_id)
        # EXAMPLE:  ("D:/media/my_media_folder/images/", "my_pict", "jpg")

        src_file_path = f"{directory_path}{stem}.{extension}"   # The current storage location (TODO: turn into function)
        dest_file_path = f"{MediaManager.get_media_folder()}{media_directory}/{stem}.{extension}"   # The desired storage location

        #print("\nsrc_file_path: ", src_file_path)       # EXAMPLE: "test_files/sample_file_1.txt"
        #print("dest_file_path: ", dest_file_path)       # EXAMPLE: "test_files/my documents/chapter 1/sample_file_1.txt"

        # Move the media file
        MediaManager.move_file(src=src_file_path, dest=dest_file_path)
        PluginManager.move_media_item_successful(internal_id=internal_id,
                                                 src=src_file_path, dest=dest_file_path)   # Needed to move "covers" or "thumbnails"

        # Update the databases
        # Locate the node for the new "Directory"
        new_dir_id = GraphSchema.locate_single_data_node(class_name="Directory", key_name="name", key_value=media_directory)
        #print("new_dir_id : ", new_dir_id)

        if dir is None:
            GraphSchema.add_data_relationship(from_id=internal_id, to_id=new_dir_id, rel_name="BA_stored_in")
        else:
            # Change the link in the database
            old_dir_id = GraphSchema.locate_single_data_node(class_name="Directory", key_name="name", key_value=dir)
            #print("old_dir_id : ", old_dir_id)
            GraphSchema.db.reattach_node(node=internal_id,
                                         old_attachment=old_dir_id, new_attachment=new_dir_id,
                                         rel_name="BA_stored_in")






    #####################################################################################################

    '''                            ~   DIRECT FOLDER ACCESS (read/modify)   ~                                '''

    def ________DIRECT_FOLDER_ACCESS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def create_folder(cls, directory_path :str) -> None:
        """
        If the folder already exists, no action is taken

        :param directory_path:  EXAMPLE, on Windows: "D:/media/documents"
                                EXAMPLE of local path:  "test_files/my documents/chapter 1"
        :return:                None
        """
        #print(f"create_folder(): attempting to create a folder named '{directory_path}'")
        os.makedirs(directory_path, exist_ok=True)       # Do not raise an error if the folder already exists



    @classmethod
    def delete_folder(cls, directory_path :str) -> None:
        """
        If the folder doesn't exists or isn't empty, an Exception is raised

        :param directory_path:  EXAMPLE, on Windows: "D:/media/documents"
                                EXAMPLE of local path:  "test_files/my documents/chapter 1"
        :return:                None
        """
        #TODO: pytest
        #print(f"delete_folder(): attempting to delete a folder named '{directory_path}'")
        os.rmdir(directory_path)    # An Exception will be raised if folder isn't empty


    @classmethod
    def folder_exists(cls, name :str) -> bool:
        """

        :param name:    EXAMPLE: "test_files/my documents/chapter 1"
        :return:        True if such folder (directory) exists, or False otherwise
        """
        #TODO: pytest

        # Create a path object (works seamlessly on Windows and Linux)
        folder_path = Path(name)

        # Check if it exists AND is a directory
        return folder_path.is_dir()



    @classmethod
    def move_file(cls, src :str, dest :str) -> None:
        """
        Rename (move) the specified file, possibly across disks.
        An Exception is raised if:
            * the file was not found
            * if source and destination are the same
            * another file with destination file path already exists
            * bad file path for the destination (e.g. forbidden characters)
            * if the directory path to the destination isn't already present

        EXAMPLE:
            move_file(src = "test_files/I_dont_exist.txt",
                      dest = "test_files/sample_file_2.txt")

        :param src:    Current file path of the file to rename
        :param dest:   Desired new file path
        :return:       None
        """
        #print(f"move_file(): src='{src}' | dest: '{dest}'")

        assert src != dest, \
            f"move_file(): The requested source and destination file names are the same! (`{src}`)"

        assert os.path.exists(src), \
            f"move_file(): The requested file `{src}` does not exist"

        assert not os.path.exists(dest), \
            f"move_file(): A file with the requested destination name (`{dest}`) already exists"

        cls.assert_valid_file_path(dest)

        # Move (if on the same disk, it does a rename; if across disks, it copies first, and then deletes the original)
        #os.rename(src, dest)    # TODO: doesn't work if the source and destination are on different disks!
        shutil.move(src, dest)





    #####################################################################################################

    '''                            ~   DIRECT FILE ACCESS (read/modify)   ~                                '''

    def ________DIRECT_FILE_ACCESS________(DIVIDER):
        pass        # Used to get a better structure view in IDEs
    #####################################################################################################

    @classmethod
    def file_exists(cls, name) -> bool:
        """

        :param name:    Use forward slashes
        :return:
        """
        # Use forward slashes; pathlib automatically converts them for Windows
        file_path = Path(name)

        return file_path.is_file()



    @classmethod
    def get_from_text_file(cls, filename :str, path="", encoding="latin-1") -> str:
        """
        Read in and return the contents of the specified TEXT file.

        Note: "utf8" encoding at times led to problems.
              See https://stackoverflow.com/questions/5552555/unicodedecodeerror-invalid-continuation-byte

        :param filename:    FULL filename, INCLUDING path - unless path is passed in the following argument
                                EXAMPLE on Windows:
                                "D:/my_media_folder/documents/my_file.txt"   (notice the forward slashes, even on Windows)
        :param path:        [OPTIONAL] String to prefix to the `filename` argument, above
        :param encoding:    [OPTIONAL] A string such as "latin-1" (aka "iso-8859-1") or "utf8"
        :return:            The contents of the text file, using the requested encoding
        """
        full_file_name = path + filename

        with open(full_file_name, 'r', encoding=encoding) as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def get_from_binary_file(cls, path :str, filename :str) -> bytes:
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
    def save_into_text_file(cls, contents :str, filename :str, class_name :str) -> None:
        """
        Save the given text data into the specified file, stored in the class-wide media folder.
        UTF8 encoding is used.

        :param contents:    String with the text to store into the file
        :param filename:    EXCLUSIVE of file path
        :param class_name:  Needed to determine the default folder location (which is based on class_name);
                                if that folder doesn't exist, it gets created
        :return:            None.  In case of errors, detailed Exceptions are raised
        """
        folder = cls.default_file_path(class_name=class_name)
        full_file_name = folder + filename

        # First, try to open the file...
        try:
            f = open(full_file_name, "w", encoding='utf8')
        except Exception:
            # This failure might be due to the media folder not being present
            print(f"save_into_text_file(): Failed to open file '{full_file_name}' for writing.  "
                  f"Attempting to automatically correct, if that was due to a missing folder for the media of Class '{class_name}'")

            # Attempt to remedy the problem by creating the appropriate media folder - in case it was missing
            cls.create_missing_media_folder(class_name=class_name)

            # Try again after creating the media folder (if that was indeed missing)
            try:
                f = open(full_file_name, "w", encoding='utf8')
            except Exception as ex:
                raise Exception(f"save_into_file(): Unable to open file '{full_file_name}' for writing. {ex}")


         # ...then try to write into it
        try:
            f.write(contents)
        except Exception as ex:
            raise Exception(f"save_into_file(): Unable write data to file '{full_file_name}'. "
                            f"First 20 characters: `{contents[:20]}`. {exceptions.exception_helper(ex)}")

        f.close()



    @classmethod
    def delete_file(cls, fullname :str) -> bool:
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





##########################################    IMAGES    ######################################################

class ImageProcessing:
    """
    Utility class for managing images, especially in the context of uploads.

    SIDE NOTE: The "th" format from previous versions of BrainAnnex, is the only format in current use:
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
    def save_thumbnail(cls, src_folder :str, filename :str, save_to_folder :str,
                       src_width :int, src_height :int) -> None:
        """
        Make a thumbnail of the specified image, and save it in a file.
        The "th" thumbnail format (width=300) is being followed.

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param save_to_folder:  Full path of folder where to save the resized file.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/_resized/"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :return:                None
        """
        #TODO: turn the hardwired 300 into a class variable.  Specific formats ought to go into the Image plugin
        image = cls.scale_down_horiz(src_folder=src_folder, filename=filename,
                                     src_width=src_width, src_height=src_height, target_width=300)

        resized_full_name = save_to_folder + filename

        try:
            image.save(resized_full_name)
        except Exception:
            # This failure might be due to the destination folder for the resized images not being present
            print(f"save_thumbnail(): Failed to save the resized image into the file '{resized_full_name}'.  "
                  f"Attempting to automatically correct, if that was due to a missing destination folder")

            # Attempt to remedy the problem by creating the appropriate folder - in case it was missing
            MediaManager.create_folder(directory_path=save_to_folder)

            # Try again after creating the media folder (if that was indeed missing)
            image.save(resized_full_name)



    @classmethod
    def scale_down_horiz(cls, src_folder: str, filename: str,
                         src_width: int, src_height: int, target_width: int):
        """
        Resize to the target WIDTH the image contained in the specified file,
        and return it as an `Image` object

        :param src_folder:      Full path of folder with the file to resize.  It MUST end with "/"
                                    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/"
        :param filename:        Name of file to resize.  EXAMPLE: "my image.jpg"
        :param src_width:       Pixel width of the original image
        :param src_height:      Pixel height of the original image
        :param target_width:    Desired pixel width of the resized image
        :return:                An `Image` object with the resized image
        """
        image = Image.open(src_folder + filename)

        if target_width >= src_width:   # Don't transform the image; just return it, as it is
            return image
            #image.save(resized_full_name)
        else:
            scaling_ratio = src_width / target_width    # This will be > 1 (indicative of reduction)
            #print("scaling_ratio: ", scaling_ratio)
            target_height = int(src_height / scaling_ratio)
            new_image = image.resize((target_width, target_height))
            return new_image
            #new_image.save(resized_full_name)



    @classmethod
    def get_image_size(cls, source_full_name) -> (int, int):
        """
        Return the size of the given image.

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/Brain Annex/media/my image.jpg"
        :return:                    The pair (width, height) with the image dimensions in pixels.  In case of error, an Exception is raised
        """
        image = Image.open(source_full_name)

        return image.size   # EXAMPLE: (1920, 1280)



    @classmethod
    def process_uploaded_image(cls, media_folder :str, basename :str, suffix :str) -> dict:
        """
        If possible, obtain the size of the image, resize it to a thumbnail,
        save the thumbnail in the "_resized/" subfolder of the specified media folder;
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
                                           save_to_folder = media_folder+cls.RESIZED_FOLDER,
                                           src_width=width, src_height=height)

            print(f"process_uploaded_image(): Uploaded image has width {width} , height: {height}.  "
                  f"Thumbnail successfully created and stored")
            properties = {"caption": basename, "width": width, "height": height}
        except Exception as ex:
            print(f"process_uploaded_image(): Unable to resize image.  {ex}")
            properties = {"caption": basename}


        return properties    # A dictionary of additional image-specific properties that will go in the database



    @classmethod
    def describe_image(cls, source_full_name) -> None:
        """
        Print out some info about the given image:
        the file format, the pixel format, the image size and (if any) the color palette

        :param source_full_name:    EXAMPLE (on Windows): "D:/Docs/media/my image.jpg"
        :return:                    None
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
