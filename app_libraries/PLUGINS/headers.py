from brainannex import GraphSchema, Categories



class Headers:
    """
    Plugin-provided custom interface for "headers"
    """

    SCHEMA_CLASS_NAME = "Header"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin

        :return:    None
        """
        # TODO: test
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Content Item"):
            Categories.add_to_schema()


        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            db_id = GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="h", handler="headers",
                                                                properties=["text"],
                                                                class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

            # Set data types for some Properties
            GraphSchema.set_property_attribute(class_name=cls.SCHEMA_CLASS_NAME, prop_name="text",
                                               attribute_name="dtype", attribute_value="str")


            # Set up the auto-increment namespace
            namespace="header"
            GraphSchema.create_namespace(name=namespace, prefix="header-", suffix="")
            match_to = GraphSchema.db.match(labels="Schema Autoincrement", key_name="namespace", key_value=namespace)
            GraphSchema.db.add_links(match_from=db_id, match_to=match_to, rel_name="HAS_URI_GENERATOR")
