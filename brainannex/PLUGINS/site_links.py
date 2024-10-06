from brainannex.media_manager import MediaManager
from brainannex.neo_schema.neo_schema import NeoSchema


class SiteLinks:
    """
    Plugin-provided custom interface for "site links" (bookmarks to web pages)
    """

    SCHEMA_CLASS_NAME = "Site Link"



    @classmethod
    def initialize_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        assert NeoSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        NeoSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=True, code="sl",
                                               properties=["url", "name", "date", "comments", "rating", "read", "date_created"],
                                               class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

        # Ensure that the URL's will be constrained to be unique
        NeoSchema.db.create_constraint(label="Site Link", key="url", type="UNIQUE", name="unique_bookmarks")

