"""Dynamically generated Strawberry GraphQL API for Brain Annex.

Current scope:
    * Discover all semantic-layer classes marked visible via
      GraphSchema.get_all_classes(only_visible=True).
    * For each class, expose only properties explicitly marked
      visible=True.
    * Convert canonical GraphSchema dtypes into GraphQL scalar types.
    * Honor the optional PROPERTY.required flag:
          required set and True     -> GraphQL non-null field
          otherwise                 -> nullable GraphQL field
    * Fetch data nodes for a class when its GraphQL root field is queried.

The schema is generated when register_graphql_2(app) is called. Data records
are fetched each time the corresponding root field is queried.

Naming:
    * GraphQL object type names exactly match semantic class names.
    * GraphQL root field names exactly match semantic class names.
    * GraphQL property field names exactly match semantic property names.
    * Names must be valid GraphQL names. Invalid names are rejected rather
      than silently rewritten.
"""

import logging
import re
from collections.abc import Mapping
from typing import Any, List, Optional, Type

import strawberry
from strawberry.flask.views import GraphQLView
from strawberry.schema.config import StrawberryConfig

from brainannex import GraphSchema


_LOGGER = logging.getLogger(__name__)

GRAPHQL_URL = "/graphql_2"
FLASK_ENDPOINT_NAME = "graphql_view_2"


# GraphQL names use the ASCII grammar [_A-Za-z][_0-9A-Za-z]*.
_GRAPHQL_NAME_PATTERN = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")


# These names are already occupied in every GraphQL schema, or are used by
# this module for the root query type.
_RESERVED_GRAPHQL_TYPE_NAMES = {
    "Boolean",
    "Float",
    "ID",
    "Int",
    "Query",
    "String",
}



# GraphSchema's canonical dtype vocabulary. Do not normalize or accept aliases:
# GraphSchema is responsible for enforcing these exact values.
_DTYPE_TO_PYTHON_TYPE = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


def _python_type_for_dtype(dtype: Any, property_name: str) -> Type:
    """
    Translate a canonical GraphSchema dtype into a Python/GraphQL scalar type.
    Raise an exception if encountering an unsupported type

    :param dtype:           A string with a dtype value from the database
    :param property_name:   The name of the property with that dtype
                                (only used for error reporting)
    :return:                A python data type
    """
    try:
        return _DTYPE_TO_PYTHON_TYPE[dtype]
    except (KeyError, TypeError) as exc:
        supported = ", ".join(_DTYPE_TO_PYTHON_TYPE)
        raise ValueError(
            f"Cannot generate GraphQL field for property {property_name!r}: "
            f"unsupported GraphSchema dtype {dtype!r}. Expected exactly one "
            f"of: {supported}."
        ) from exc


def _validate_graphql_name(name: Any, *, description: str) -> str:
    """Validate and return a name that will be exposed in GraphQL."""
    if (
        not isinstance(name, str)
        or not _GRAPHQL_NAME_PATTERN.fullmatch(name)
        or name.startswith("__")
    ):
        raise ValueError(
            f"Cannot expose {description} {name!r} in GraphQL. Names must "
            "match [_A-Za-z][_0-9A-Za-z]* and must not begin with '__'. "
            "No automatic renaming is performed."
        )
    return name


def _normalise_class_name_results(class_results: Any) -> List[str]:
    """Extract class names from get_all_classes(only_visible=True).

    The usual expected result is a list of strings. For convenience, this
    also accepts a sequence of dictionaries/objects with a `name` or
    `class_name` member. If a returned dictionary explicitly contains
    `visible: False`, that entry is ignored as a defensive check.
    """
    if class_results is None:
        return []

    if isinstance(class_results, str):
        entries = [class_results]
    elif isinstance(class_results, Mapping):
        # Accommodate either a single class-description dictionary or a
        # mapping keyed by class name.
        if "name" in class_results or "class_name" in class_results:
            entries = [class_results]
        else:
            entries = list(class_results.keys())
    else:
        try:
            entries = list(class_results)
        except TypeError as exc:
            raise TypeError(
                "GraphSchema.get_all_classes(only_visible=True) must return "
                "an iterable of class names (or class-description records)."
            ) from exc

    class_names = []
    for entry in entries:
        if isinstance(entry, str):
            class_name = entry
        elif isinstance(entry, Mapping):
            if entry.get("visible") is False:
                continue
            class_name = entry.get("name", entry.get("class_name"))
        else:
            if getattr(entry, "visible", None) is False:
                continue
            class_name = getattr(
                entry, "name", getattr(entry, "class_name", None)
            )

        class_name = _validate_graphql_name(
            class_name, description="semantic class name"
        )

        if class_name in class_names:
            raise ValueError(
                f"GraphSchema returned duplicate visible class name "
                f"{class_name!r}."
            )
        if class_name in _RESERVED_GRAPHQL_TYPE_NAMES:
            raise ValueError(
                f"Semantic class name {class_name!r} conflicts with a "
                "built-in GraphQL scalar or the root Query type."
            )

        class_names.append(class_name)

    return class_names



def _get_visible_class_names() -> List[str]:
    """
    Return the semantic classes selected for GraphQL exposure

    :return:
    """
    class_results = GraphSchema.get_all_classes(only_visible=True)
    return _normalise_class_name_results(class_results)



def _get_visible_properties(class_name: str) -> List[dict]:
    """Read and validate the GraphQL-visible properties of one class.

    A property is exposed only when `visible` is present and is exactly True.
    Its dtype must use one of GraphSchema's four canonical identifiers.
    """
    property_definitions = GraphSchema.get_class_properties_full_data(
        class_name=class_name
    )

    if property_definitions is None:
        property_definitions = []

    visible_properties = []
    seen_names = set()

    for property_definition in property_definitions:
        if not isinstance(property_definition, Mapping):
            raise TypeError(
                "GraphSchema.get_class_properties_full_data() was expected "
                "to return dictionaries describing properties; got "
                f"{type(property_definition).__name__}."
            )

        if property_definition.get("visible") is not True:
            continue

        property_name = _validate_graphql_name(
            property_definition.get("name"),
            description=f"property name on class {class_name!r}",
        )

        if property_name in seen_names:
            raise ValueError(
                f"Duplicate visible property {property_name!r} in "
                f"GraphSchema class {class_name!r}."
            )
        seen_names.add(property_name)

        dtype = property_definition.get("dtype")
        python_type = _python_type_for_dtype(dtype, property_name)

        # The optional `required` metadata is interpreted conservatively:
        # only an explicit True makes the GraphQL field non-null.
        is_required = property_definition.get("required") is True

        visible_properties.append(
            {
                "name": property_name,
                "python_type": python_type,
                "required": is_required,
            }
        )

    return visible_properties



def _build_object_type(class_name: str, visible_properties: List[dict]):
    """Dynamically construct a Strawberry object type for one semantic class.

    Internal Python attribute names (`ba_field_0`, etc.) are used so that
    GraphQL-valid names that happen to be Python keywords can still be
    represented. The `strawberry.field(name=...)` alias preserves the exact
    semantic property name in the GraphQL schema.
    """
    annotations = {}
    class_namespace = {
        "__module__": __name__,
        "__annotations__": annotations,
    }
    python_field_names = {}

    for index, property_info in enumerate(visible_properties):
        property_name = property_info["name"]
        python_type = property_info["python_type"]
        is_required = property_info["required"]
        python_field_name = f"ba_field_{index}"

        annotations[python_field_name] = (
            python_type if is_required else Optional[python_type]
        )

        if is_required:
            class_namespace[python_field_name] = strawberry.field(
                name=property_name
            )
        else:
            class_namespace[python_field_name] = strawberry.field(
                name=property_name,
                default=None,
            )

        python_field_names[property_name] = python_field_name

    dynamic_python_class = type(class_name, (), class_namespace)
    strawberry_object_type = strawberry.type(dynamic_python_class)

    return strawberry_object_type, python_field_names


def _build_resolver(
    class_name: str,
    strawberry_object_type: Type,
    visible_properties: List[dict],
    python_field_names: dict):
    """
    :param class_name:
    :param strawberry_object_type:
    :param visible_properties:
    :param python_field_names:
    :return:
    """

    """Create a resolver that fetches and adapts data nodes for one class."""

    def resolve_class_records():
        records = GraphSchema.get_data_nodes_of_class(class_name=class_name)

        if records is None:
            return []

        result_objects = []
        for record_index, record in enumerate(records):
            if not isinstance(record, Mapping):
                raise TypeError(
                    "GraphSchema.get_data_nodes_of_class() was expected to "
                    "return dictionaries for data nodes; got "
                    f"{type(record).__name__} for class {class_name!r}."
                )

            constructor_values = {}
            for property_info in visible_properties:
                property_name = property_info["name"]
                value = record.get(property_name)

                if property_info["required"] and value is None:
                    raise ValueError(
                        f"Data node #{record_index} of class {class_name!r} "
                        f"does not provide a non-null value for required "
                        f"property {property_name!r}."
                    )

                internal_field_name = python_field_names[property_name]
                constructor_values[internal_field_name] = value

            result_objects.append(
                strawberry_object_type(**constructor_values)
            )

        return result_objects

    return resolve_class_records



def build_graphql_schema():
    """Build and return a Strawberry schema from visible GraphSchema classes.

    This separate function is useful for inspecting/testing the generated SDL
    without registering a Flask route.
    """
    class_names = _get_visible_class_names()
    if not class_names:
        raise ValueError(
            "GraphSchema returned no classes marked visible=True; cannot "
            "generate a GraphQL Query type with no fields."
        )

    query_annotations = {}
    query_namespace = {
        "__module__": __name__,
        "__annotations__": query_annotations,
    }

    exposed_class_count = 0

    for class_index, class_name in enumerate(class_names):
        visible_properties = _get_visible_properties(class_name)

        # An object type with no fields is not valid GraphQL. For this
        # scalar-properties-only milestone, skip visible classes that have
        # no visible properties. They can be exposed later when relationship
        # fields are supported by the generator.
        if not visible_properties:
            _LOGGER.warning(
                "Skipping visible GraphSchema class %r: it has no properties "
                "marked visible=True. A GraphQL object type must have at "
                "least one field.",
                class_name,
            )
            continue

        object_type, python_field_names = _build_object_type(
            class_name,
            visible_properties,
        )
        resolver = _build_resolver(
            class_name,
            object_type,
            visible_properties,
            python_field_names,
        )

        # Use a safe internal Python attribute, while explicitly preserving
        # the semantic class name as the GraphQL root field name.
        internal_query_field_name = f"ba_query_field_{class_index}"
        query_annotations[internal_query_field_name] = List[object_type]
        query_namespace[internal_query_field_name] = strawberry.field(
            name=class_name,
            resolver=resolver,
        )

        exposed_class_count += 1

    if exposed_class_count == 0:
        raise ValueError(
            "No visible GraphSchema classes have any properties marked "
            "visible=True. Cannot generate a usable GraphQL schema."
        )

    dynamic_query_class = type("Query", (), query_namespace)
    strawberry_query_type = strawberry.type(dynamic_query_class)

    # Disabling auto-camel-case ensures that metadata names are represented
    # exactly as stored, including root fields and property fields.
    return strawberry.Schema(
        query=strawberry_query_type,
        config=StrawberryConfig(auto_camel_case=False),
    )



def register_graphql_2(app) -> None:
    """Generate and register the /graphql_2 endpoint on an existing Flask app.

    Call this from the Brain Annex application factory after GraphSchema has
    been initialized. The GraphQL schema is generated at registration/startup
    time; data nodes are retrieved whenever their root field is queried.

    :param app: Existing Flask application instance.
    :return:    None
    """
    generated_schema = build_graphql_schema()

    app.add_url_rule(
        GRAPHQL_URL,
        view_func=GraphQLView.as_view(
            FLASK_ENDPOINT_NAME,
            schema=generated_schema,
        ),
    )
