from app_libraries.media_manager import MediaManager
from brainannex import GraphSchema


class Images:
    """
    Plugin-provided custom interface for "images"
    """

    SCHEMA_CLASS_NAME = "Image"



    @classmethod
    def default_folder(cls):
        """
        Specify the desired name for the default subfolder (of the media folder) to contain image media
        """
        return "images"



    @classmethod
    def initialize_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        # TODO: rename to add_to_schema()

        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Media"):
            GraphSchema.create_class_with_properties(name="Media", strict=True,
                                                     properties=["basename", "suffix"])

        GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="i",
                                                 properties=["width", "height", "caption", "date_created"],
                                                 class_to_link_to="Media", link_name="INSTANCE_OF", link_dir="OUT")

        if not GraphSchema.class_name_exists("Directory"):
            GraphSchema.create_class_with_properties(name="Directory", strict=True,
                                                     properties=["name", "description"])
            GraphSchema.create_class_relationship(from_class="Media", to_class="Directory", rel_name="BA_stored_in")
