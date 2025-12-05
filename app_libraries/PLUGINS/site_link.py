from brainannex import GraphSchema, Categories



class SiteLink:
    """
    Plugin-provided custom interface for "site links" (bookmarks to web pages)
    """

    SCHEMA_CLASS_NAME = "Site Link"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin

        :return:    None
        """
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Content Item"):
            Categories.add_to_schema()


        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="sl", handler="site_link",
                                                     properties=["url", "name", "date", "comments", "rating", "read", "date_created"],
                                                     class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

            # Ensure that the URL's will be constrained to be unique
            GraphSchema.db.create_constraint(label="Site Link", key="url", name="unique_bookmarks")

