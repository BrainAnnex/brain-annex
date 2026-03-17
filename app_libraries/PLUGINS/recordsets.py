from brainannex import GraphSchema, Categories



class Recordsets:
    """
    Plugin-provided custom interface for "recordsets"
    """

    SCHEMA_CLASS_NAME = "Recordset"



    @classmethod
    def add_to_schema(cls) -> None:
        """
        Create, as needed, the database Schema needed by this plugin.
        Any part already present (typically from an earlier install) is left undisturbed.

        :return:    None
        """
        assert GraphSchema.is_valid_class_name(cls.SCHEMA_CLASS_NAME), \
            f"initialize_schema(): attempting to create a Schema Class with an invalid name: '{cls.SCHEMA_CLASS_NAME}'"

        if not GraphSchema.class_name_exists("Content Item"):
            Categories.add_to_schema()


        # Create the Class needed by this plugin, unless already in the database
        if not GraphSchema.class_name_exists(cls.SCHEMA_CLASS_NAME):
            GraphSchema.create_class_with_properties(name=cls.SCHEMA_CLASS_NAME, strict=False, code="rs", handler="recordsets",
                                                     properties=["caption", "filter_label", "order_by", "clause_key", "clause_op", "clause_value",  "n_group", "fields"],
                                                     class_to_link_to="Content Item", link_name="INSTANCE_OF", link_dir="OUT")

            # Set data types for some Properties
            GraphSchema.set_property_attribute(class_name=cls.SCHEMA_CLASS_NAME, prop_name="n_group",
                                               attribute_name="dtype", attribute_value="int")

            # Set up the auto-increment namespace
            namespace="recordset"
            if not GraphSchema.namespace_exists(name=namespace):
                GraphSchema.create_namespace(name=namespace, prefix="rs-", suffix="")

            GraphSchema.assign_namespace_to_class(class_name=cls.SCHEMA_CLASS_NAME, namespace=namespace)
            #GraphSchema.db.add_links(match_from=db_id, match_to=ns_id, rel_name="HAS_URI_GENERATOR")
