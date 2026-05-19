from brainannex import GraphSchema, Categories



class FlashCard:
    """
    Plugin-provided custom interface for "flash cards"
    """

    SCHEMA_CLASS_NAME = "Flash Card"
    SCHEMA_CODE = "f"                  # TODO: phase out
    NAMESPACE_PREFIX = "fc"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin

        :return:    None
        """
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        # TODO: this ought to be done by plugin_support.py
        if not GraphSchema.class_name_exists("Content Item"):
            Categories.add_to_schema()


        # Create the Class needed by this plugin, unless already in the database
        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False,
                                                     code=cls.SCHEMA_CODE, handler="flash_card",
                                                     properties=["source_label", "sideA_field", "sideB_field", "reverse_odds"],
                                                     class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

            # Set up the auto-increment namespace
            namespace="flash_card"
            if not GraphSchema.namespace_exists(name=namespace):
                GraphSchema.create_namespace(name=namespace, prefix=f"{cls.NAMESPACE_PREFIX}-", suffix="")

            GraphSchema.assign_namespace_to_class(class_name=cls.SCHEMA_CLASS_NAME, namespace=namespace)