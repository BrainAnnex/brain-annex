import os
import BrainAnnex.modules.utilities.exceptions as exceptions


class MediaManager:
    """
    Helper library for the management of media files
    """

    MEDIA_FOLDER = None # Location where the media for Content Items is stored, including the final "/"
                        # Example on Windows: "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"
                        #                     (notice the forward slashes, even on Windows)
                        # This class variable gets set by initialize.py


    @classmethod
    def set_media_folder(cls, path_name: str) -> None:
        """

        :param path_name:
        :return:            None
        """
        # TODO: if path_name doesn't end with "/", add it

        cls.MEDIA_FOLDER = path_name



    @classmethod
    def get_from_file(cls, filename: str) -> str:
        """
        Read in and return the contents of the specified text file

        :param filename:    EXCLUSIVE of path (stored in the class variable MEDIA_FOLDER)
        :return:            The contents of the file
        """
        full_file_name = cls.MEDIA_FOLDER + filename
        with open(full_file_name, 'r', encoding='utf8') as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def get_from_binary_file(cls, path: str, filename: str) -> bytes:
        """
        Read in and return the contents of the specified binary file

        :param path:
        :param filename:    EXCLUSIVE of path
        :return:            The contents of the binary file
        """
        #full_file_name = cls.MEDIA_FOLDER + filename
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
        :param filename:    EXCLUSIVE of MEDIA_FOLDER part (stored as class variable)
        :return:            None.  In case of errors, detailed Exceptions are raised
        """

        full_file_name = cls.MEDIA_FOLDER + filename

        try:
            f = open(full_file_name, "w", encoding='utf8')
        except Exception as ex:
            raise Exception(f"Unable to open file {full_file_name} for writing. {ex}")

        try:
            f.write(contents)
        except Exception as ex:
            raise Exception(f"Unable write data to file {full_file_name}. "
                            f"First 20 characters: `{contents[:20]}`. {exceptions.exception_helper(ex)}")

        f.close()



    @classmethod
    def delete_media_file(cls, basename: str, suffix: str, subfolder = "") -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param basename:    File name, exclusive of path and of suffix
        :param suffix:      String such as "htm" (don't include the dot!)
        :param subfolder:   It must end with "/"  .  EXAMPLE:  "resized/"
        :return:            True if successful, or False otherwise
        """
        filename = basename + "." + suffix
        print(f"Attempting to delete file `{filename}`")

        full_file_name = cls.MEDIA_FOLDER + subfolder + filename

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
