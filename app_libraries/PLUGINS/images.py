from app_libraries.media_manager import MediaManager
from brainannex import GraphSchema


class Images:
    """
    Plugin-provided custom interface for "images"
    """

    SCHEMA_CLASS_NAME = "Image"
    RESIZED_FOLDER = "_resized/"    # The subfolder where the thumbnails are kept
                                    # For now, it must be kept synchronized with value in media_manager.py



    @classmethod
    def default_folder(cls):
        """
        Specify the desired name for the default subfolder (of the media folder) to contain image media
        """
        return "images"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin

        :return:    None
        """
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Media") or not GraphSchema.class_name_exists("Directory"):
            MediaManager.add_to_schema()


        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="i", handler="images",
                                                 properties=["width", "height", "caption", "date_created"],
                                                 class_to_link_to="Media", link_name="INSTANCE_OF", link_dir="OUT")



    @classmethod
    def before_update_content(cls, entity_id :str, item_data :dict) -> dict:
        """
        Invoked before an Image's metadata gets updated in the database

        :param entity_id:   String with a unique identifier (within the given Class) for the Content Item to update
        :param item_data:   A dict with various fields for this Document
        :return:            Just pass thru the `item_data` dictionary
        """
        print(f"In Images.before_update_content() - entity_id: `{entity_id}` | item_data: {item_data}")
        new_basename = item_data.get("basename")
        new_suffix =   item_data.get("suffix")

        folder, old_basename, old_suffix = \
                MediaManager.get_media_item_file(class_name=cls.SCHEMA_CLASS_NAME, entity_id=entity_id)

        print(f"folder: {folder}, old_basename: {old_basename}, old_suffix: {old_suffix}")

        MediaManager.rename_media_file(folder=folder,
                                       old_basename=old_basename, old_suffix=old_suffix,
                                       new_basename=new_basename, new_suffix=new_suffix)

        # Also rename the resized (thumbnail) image, if present
        # TODO: in case of failure, catch error and restore old name of main file,
        #       prior to throwing an Exception
        MediaManager.rename_media_file(folder=folder+cls.RESIZED_FOLDER,
                                       old_basename=old_basename, old_suffix=old_suffix,
                                       new_basename=new_basename,
                                       ignore_missing=True)

        return item_data
