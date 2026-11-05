"""Dynamically generated Strawberry GraphQL API for Brain Annex.

Current proof-of-concept scope:
    * Read the semantic definition of the GraphSchema class "Restaurants".
    * Expose only properties whose metadata explicitly says visible is True.
    * Convert supported GraphSchema dtypes into GraphQL scalar types.
    * Fetch Restaurant data nodes when the GraphQL `restaurants` field is queried.

The GraphQL schema is generated when register_graphql_2(app) is called.  The
restaurant data itself is fetched on each query, not cached at startup.
"""

import keyword
import re
from collections.abc import Mapping
from typing import List, Optional, Type

import strawberry
from strawberry.flask.views import GraphQLView

from brainannex import GraphSchema


# ---------------------------------------------------------------------------
# Configuration for this first, deliberately narrow proof of concept
# ---------------------------------------------------------------------------

SEMANTIC_CLASS_NAME = "Restaurants"
GRAPHQL_OBJECT_TYPE_NAME = "Restaurant"
GRAPHQL_ROOT_FIELD_NAME = "restaurants"
GRAPHQL_URL = "/graphql_2"
FLASK_ENDPOINT_NAME = "graphql_view_2"


_GRAPHQL_NAME_PATTERN = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")


# Mapping of GraphSchema dtypes to python data types
_DTYPE_TO_PYTHON_TYPE = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool
}


def _python_type_for_dtype(dtype: str, property_name: str) -> Type:
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
    except KeyError as exc:
        supported = ", ".join(sorted(_DTYPE_TO_PYTHON_TYPE))
        raise ValueError(
            f"Cannot generate GraphQL field {property_name!r}: "
            f"unsupported GraphSchema dtype {dtype!r}. "
            f"Currently supported dtypes: {supported}."
        ) from exc


def _validate_property_name(property_name: str) -> None:
    """Ensure a semantic property name can be used as a GraphQL field name."""
    if (
        not isinstance(property_name, str)
        or not _GRAPHQL_NAME_PATTERN.fullmatch(property_name)
        or keyword.iskeyword(property_name)
        or property_name.startswith("__")
    ):
        raise ValueError(
            f"Cannot expose property {property_name!r} as a GraphQL field. "
            "For this proof of concept, property names must be valid "
            "GraphQL/Python-style identifiers (for example, 'address')."
        )


def _get_visible_restaurant_properties() -> list:
    """Retrieve and validate the visible property definitions for Restaurants.

    A property is exposed only when its metadata contains `visible: True`.
    Missing `visible` flags, and flags set to False, are treated as not visible.
    """
    # TODO: recover gracefully from Exceptions

    property_definitions = GraphSchema.get_class_properties_full_data(
        class_name=SEMANTIC_CLASS_NAME
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

        # Require an explicit True: absent and False flags are not exposed.
        if property_definition.get("visible") is not True:
            continue

        property_name = property_definition.get("name")
        _validate_property_name(property_name)

        if property_name in seen_names:
            raise ValueError(
                f"Duplicate visible property {property_name!r} in "
                f"GraphSchema class {SEMANTIC_CLASS_NAME!r}."
            )
        seen_names.add(property_name)

        dtype = property_definition.get("dtype")
        if dtype is None:
            raise ValueError(
                f"Visible property {property_name!r} has no 'dtype' "
                "in its GraphSchema metadata."
            )

        python_type = _python_type_for_dtype(dtype, property_name)
        visible_properties.append((property_name, python_type))

    if not visible_properties:
        raise ValueError(
            f"GraphSchema class {SEMANTIC_CLASS_NAME!r} has no properties "
            "explicitly marked visible=True; cannot generate the "
            "GraphQL Restaurant type."
        )

    return visible_properties


def _build_restaurant_type(visible_properties: list) -> Type:
    """Create a Strawberry object type from the visible property metadata.

    The fields are nullable because the metadata supplied for this first step
    does not describe whether every data node is required to have every
    property.  A missing value therefore appears as GraphQL null rather than
    violating a non-null GraphQL field declaration.
    """
    annotations = {}
    class_namespace = {
        "__module__": __name__,
        "__annotations__": annotations,
    }

    for property_name, python_type in visible_properties:
        annotations[property_name] = Optional[python_type]
        # A default of None makes the generated constructor tolerant of
        # properties that are absent from an individual data node.
        class_namespace[property_name] = None

    dynamic_python_class = type(
        GRAPHQL_OBJECT_TYPE_NAME,
        (),
        class_namespace,
    )

    return strawberry.type(dynamic_python_class)


def _build_query_type(
    restaurant_type: Type,
    visible_property_names: list,
) -> Type:
    """Create the Strawberry Query type and its restaurants resolver."""

    def resolve_restaurants():
        """Fetch Restaurant data nodes and adapt them to the generated type."""
        records = GraphSchema.get_data_nodes_of_class(
            class_name=SEMANTIC_CLASS_NAME
        )

        if records is None:
            return []

        restaurants = []
        for record in records:
            if not isinstance(record, Mapping):
                raise TypeError(
                    "GraphSchema.get_data_nodes_of_class() was expected "
                    "to return dictionaries for data nodes; got "
                    f"{type(record).__name__}."
                )

            # Include only GraphQL-visible properties. This both adapts the
            # dictionary to the generated object type and prevents hidden
            # properties from leaking into the GraphQL result.
            visible_values = {
                property_name: record.get(property_name)
                for property_name in visible_property_names
            }
            restaurants.append(restaurant_type(**visible_values))

        return restaurants

    # Build a Python class dynamically. The annotation supplies the GraphQL
    # return type; strawberry.field attaches the resolver to that field.
    query_namespace = {
        "__module__": __name__,
        "__annotations__": {
            GRAPHQL_ROOT_FIELD_NAME: List[restaurant_type],
        },
        GRAPHQL_ROOT_FIELD_NAME: strawberry.field(
            resolver=resolve_restaurants
        ),
    }

    dynamic_query_class = type("Query", (), query_namespace)
    return strawberry.type(dynamic_query_class)



def register_graphql_2(app) -> None:
    """Generate and register the /graphql_2 endpoint on an existing Flask app.

    Call this from the Brain Annex application factory after GraphSchema has
    been initialized.  The schema is generated at registration/startup time;
    restaurant records are retrieved each time the `restaurants` field is
    queried.

    :param app: Existing Flask application instance
    :return:    None
    """
    visible_properties = _get_visible_restaurant_properties()
    visible_property_names = [name for name, _ in visible_properties]

    restaurant_type = _build_restaurant_type(visible_properties)
    query_type = _build_query_type(
        restaurant_type,
        visible_property_names,
    )
    generated_schema = strawberry.Schema(query=query_type)

    print(generated_schema.as_str())    # For testing/debugging

    app.add_url_rule(
        GRAPHQL_URL,
        view_func=GraphQLView.as_view(
            FLASK_ENDPOINT_NAME,
            schema=generated_schema,
        ),
    )
