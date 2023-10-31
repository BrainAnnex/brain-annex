import os
import BrainAnnex.modules.utilities.exceptions as exceptions


class MediaManager:
    """
    Helper library for the management of media files
    """

    MEDIA_FOLDER = None # Location where the media for Content Items is stored, including the final "/"
                        # Example on Windows: "D:/media/"
                        #                     (notice the forward slashes, even on Windows)
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
    def lookup_file_path(cls, schema_code=None, class_name=None, thumb=False) -> str:
        """
        Return the full file path, including the final "/" of media of
        a particular type, identified by the schema_code argument
        TODO: allow media files to have a variety of locations - not just a standard
              one based on their type

        :param schema_code: String identifier used by the various plugins
        :param class_name:  An alternate way to identify the type of the media file.
                                If both schema_code and class_name are specified,
                                class_name prevails
        :param thumb:       If True, then the "thumbnail" version is returned
                                (only applicable to some media types, such as images)
        :return:            EXAMPLES on Windows:
                                "D:/media/documents/"
                                "D:/media/images/resized/"
        """
        folder = cls.MEDIA_FOLDER    # Includes the final "/"

        if class_name is not None:
            folder += f"{class_name.lower()}/"
        elif schema_code is not None:
            if schema_code == "d":
                folder +=  "documents/"
            elif schema_code == "i":
                folder += "images/"
            elif schema_code == "n":
                folder += "notes/"
        else:
            raise Exception("lookup_file_path(): at least one of two arguments "
                            "`class_name` and `schema_code` must be provided")

        if thumb:
            folder += "resized/"

        return folder



    @classmethod
    def get_from_text_file(cls, path: str, filename: str, encoding="latin-1") -> str:
        """
        Read in and return the contents of the specified TEXT file

        Note: 'utf8' encoding at times led to problems.
               More info: https://stackoverflow.com/questions/5552555/unicodedecodeerror-invalid-continuation-byte

        :param path:        String that must include a final "/", containing the full path of the file
                                EXAMPLE on Windows: "D:/media/" (notice the forward slashes, even on Windows)
        :param filename:    EXCLUSIVE of path
        :param encoding:    A string such as "latin-1" (aka "iso-8859-1") or "utf8"
        :return:            The contents of the text file, using 'latin-1' encoding
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
        :param filename:    EXCLUSIVE of path
        :return:            The contents of the binary file
        """
        full_file_name = path + filename
        with open(full_file_name, 'rb') as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def save_into_file(cls, contents: str, filename: str) -> None:
        """
        Save the given data into the specified file in the class-wide media folder.  UTF8 encoding is used.
        In case of error, detailed Exceptions are raised

        :param contents:    String to store into the file
        :param filename:    EXCLUSIVE of file path
        :return:            None.  In case of errors, detailed Exceptions are raised
        """

        folder = cls.lookup_file_path(schema_code="n")                          # TODO: pass schema_code as an argument, instead of being hardwired
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
    def delete_media_file(cls, basename: str, suffix: str, schema_code, thumbs=False) -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param basename:    File name, exclusive of path and of suffix
        :param suffix:      String such as "htm" (don't include the dot!)
        :param schema_code:
        :param thumbs:
        :return:            True if successful, or False otherwise
        """
        filename = basename + "." + suffix
        print(f"Attempting to delete file `{filename}`")

        folder = cls.lookup_file_path(schema_code=schema_code, thumb=thumbs)
        full_file_name = folder + filename

        #full_file_name = cls.MEDIA_FOLDER + subfolder + filename

        return cls.delete_file(full_file_name)



    @classmethod
    def delete_file(cls, fullname: str) -> bool:
        """
        Delete the specified file

        :param fullname:    Full name of the file to delete, including its path
        :return:            True if successful, or False if not found
        """

        if os.path.exists(fullname):
            os.remove(fullname)
            return True
        else:
            return False    # "The file does not exist"



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
        :param db:          Object of type "NeoAccess"; TODO: should be able to avoid it
                                                              by using the NeoSchema layer instead
        :return:            A list of names of "orphaned" file s
        """
        file_list = os.listdir(directory)
        print(f"Total number of files: {len(file_list)}")

        # Locate files that lack a database record
        orphans = []
        for filename in file_list:
            #print(filename)
            (basename, suffix) = os.path.splitext(filename)
            q = f"MATCH (n:Notes) WHERE n.basename='{basename}' AND n.suffix='htm' RETURN COUNT(n) AS number_nodes"
            n = db.query(q, single_cell="number_nodes")
            if n == 0:
                print(f"Notes record for file `{filename}`  NOT FOUND!")
                orphans.append(filename)

        return orphans
