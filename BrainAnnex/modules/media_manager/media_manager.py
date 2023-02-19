import os


class MediaManager:
    """
    Helper library for the management of media files
    """

    MEDIA_FOLDER = None # Location where the media for Content Items is stored
                        # Example on Windows: "D:/Docs/- MY CODE/Brain Annex/BA-Win7/BrainAnnex/pages/static/media/"
                        # This is set by initialize.py


    @classmethod
    def get_from_file(cls, filename: str) -> str:
        """

        :param filename:    EXCLUSIVE of MEDIA_FOLDER part (stored as class variable)
        :return:            The contents of the file
        """
        full_file_name = cls.MEDIA_FOLDER + filename
        with open(full_file_name, 'r', encoding='utf8') as fh:
            file_contents = fh.read()
            return file_contents



    @classmethod
    def get_from_binary_file(cls, path: str, filename: str) -> bytes:
        """

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
            raise Exception(f"Unable write data to file {full_file_name}. First 20 characters: `{contents[:20]}`. {cls.exception_helper(ex)}")

        f.close()



    @classmethod
    def delete_media_file(cls, basename: str, suffix: str, subfolder = "") -> bool:
        """
        Delete the specified media file, assumed in a standard location

        :param basename:
        :param suffix:
        :param subfolder:   It must end with "/"  .  EXAMPLE:  "resized/"
        :return:
        """
        filename = basename + "." + suffix
        print(f"Attempting to delete file `{filename}`")

        full_file_name = cls.MEDIA_FOLDER + subfolder + filename

        return cls.delete_file(full_file_name)



    @classmethod
    def delete_file(cls, fullname: str) -> bool:
        """
        Delete the specified file, assumed in a standard location

        :param fullname:
        :return:            True if successful, or False otherwise
        """

        if os.path.exists(fullname):
            os.remove(fullname)
            return True
        else:
            return False    # "The file does not exist"
