from brainannex.neo_schema.neo_schema import NeoSchema


class Recordsets:
    """
    Plugin-provided custom interface for "recordsets"
    """

    SCHEMA_CLASS_NAME = "Recordset"



    @classmethod
    def initialize_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        assert NeoSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not NeoSchema.class_name_exists("Content Item"):
            NeoSchema.create_class_with_properties(name="Content Item", strict=True,
                                               properties=["uri"])

        db_id, _ = NeoSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=True, code="rs",
                                                          properties=["class", "order_by", "clause", "n_group", "caption"],
                                                          class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

        # Set data types for some Properties
        NeoSchema.set_property_attribute(class_name=cls.SCHEMA_CLASS_NAME, prop_name="n_group",
                                         attribute_name="dtype", attribute_value="int")


        # Set up the auto-increment namespace
        NeoSchema.create_namespace(name="recordset", prefix="rs-", suffix="")
        match_to = NeoSchema.db.match(labels="Schema Autoincrement", key_name="namespace", key_value="recordset")
        NeoSchema.db.add_links(match_from=db_id, match_to=match_to, rel_name="HAS_URI_GENERATOR")
