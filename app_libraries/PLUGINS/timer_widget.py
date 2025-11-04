from brainannex import GraphSchema



class TimerWidget:
    """
    Plugin-provided custom interface for "timer widgets"
    """

    SCHEMA_CLASS_NAME = "Timer Widget"



    @classmethod
    def initialize_schema(cls) -> None:
        """
        Initialize the Schema needed by this plugin

        :return:    None
        """
        #TODO: test
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Content Item"):
            GraphSchema.create_class_with_properties(name="Content Item", strict=True,
                                                     properties=["uri"])    # TODO: this ought to be done by plugin_support.py

        db_id, _ = GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=True, code="timer",
                                                            properties=["ringtone"],
                                                            class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

        # Set data types for some Properties
        GraphSchema.set_property_attribute(class_name=cls.SCHEMA_CLASS_NAME, prop_name="ringtone",
                                           attribute_name="dtype", attribute_value="str")


        # Set up the auto-increment namespace
        namespace="timer"
        GraphSchema.create_namespace(name=namespace, prefix="timer-", suffix="")
        match_to = GraphSchema.db.match(labels="Schema Autoincrement", key_name="namespace", key_value=namespace)
        GraphSchema.db.add_links(match_from=db_id, match_to=match_to, rel_name="HAS_URI_GENERATOR")
