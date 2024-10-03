from brainannex.media_manager import MediaManager
from brainannex.neo_schema.neo_schema import NeoSchema


class Images:
    """
    Plugin-provided custom interface for "images"
    """

    SCHEMA_CLASS_NAME = "Image"



    @classmethod
    def default_folder(cls):
        """
        Specify the desired name for the default folder to contain image media
        """
        return "images"



    @classmethod
    def initialize_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        assert NeoSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not NeoSchema.class_name_exists("Media"):
            NeoSchema.create_class_with_properties(name="Media", strict=True,
                                               properties=["basename", "suffix"])

        NeoSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=True, code="i",
                                               properties=["width", "height", "caption", "date_created"],
                                               class_to_link_to="Media", link_name="INSTANCE_OF", link_dir="OUT")

        if not NeoSchema.class_name_exists("Directory"):
            NeoSchema.create_class_with_properties(name="Directory", strict=True,
                                                   properties=["name", "description"])
            NeoSchema.create_class_relationship(from_class="Media", to_class="Directory", rel_name="BA_stored_in")
