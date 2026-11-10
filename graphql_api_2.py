""" CLASSES and PROPERTIES, as well as links.

Dynamically generated Strawberry GraphQL API for Brain Annex.

Current scope:
    * Discover semantic classes marked visible=True.
    * Expose only class properties marked visible=True.
    * Use GraphSchema's canonical dtypes: str, int, float, bool.
    * Treat PROPERTY.required as true only when explicitly True.
    * Discover outgoing semantic LINK definitions between visible classes.
    * Represent each relationship as a direct nested GraphQL field pointing
      to the destination class. LINK-node properties are intentionally
      ignored in this iteration.
    * Fetch related data nodes lazily, only when a relationship field is
      requested, using the source data node's Neo4j internal ID.



SERVICE CONTRACTS ---

GraphSchema service contracts introduced for this iteration:

    1) GraphSchema.get_class_links_full_data(class_name=...)

       Returns outgoing semantic LINK definitions for the source class, e.g.:

           [
               {"name": "WORKS_FOR", "target_class": "Employer"},
               {"name": "LIVES_IN", "target_class": "City"},
           ]

       `name` is the LINK node's semantic name. `target_class` is the name of
       the destination CLASS node. The method should return only links outgoing
       from the requested source class. Extra metadata may be included, but is
       ignored here. Relationship properties on LINK nodes are also ignored.

    2) GraphSchema.get_linked_data_nodes(
           source_node_id=..., link_name=..., target_class=...
       )

       Returns the target data-node records reached by following the named
       outgoing data relationship from the source node. The return format is
       the same as get_data_nodes_of_class(): a list of dictionaries containing
       ordinary data properties plus `_internal_id` and `_node_labels`.

       This method is called only when the corresponding GraphQL relationship
       field is selected by a client.

Visibility rule:
    A relationship is exposed when its source and target CLASS nodes are
    both visible. There is no separate LINK visibility flag in this version.

Cardinality:
    Until GraphSchema provides cardinality metadata, every relationship field
    is exposed as a non-null GraphQL list. No matches produce an empty list.

Naming:
    Semantic class names, property names, LINK names, and root query field
    names are preserved exactly. Invalid GraphQL names are rejected instead
    of silently rewritten. Automatic camel-casing is disabled.
"""

import logging
import re
from collections.abc import Mapping
from typing import Annotated, Any, List, Optional, Type
from uuid import uuid4

import strawberry
from strawberry.flask.views import GraphQLView
from strawberry.schema.config import StrawberryConfig

from brainannex import GraphSchema


_LOGGER = logging.getLogger(__name__)

GRAPHQL_URL = "/graphql_2"
FLASK_ENDPOINT_NAME = "graphql_view_2"


# GraphQL names use the ASCII grammar [_A-Za-z][_0-9A-Za-z]*.
_GRAPHQL_NAME_PATTERN = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")


# A semantic class cannot use a built-in scalar name or the root Query name
_RESERVED_GRAPHQL_TYPE_NAMES = {
    "Boolean",
    "Float",
    "ID",
    "Int",
    "Query",
    "String"
}


# GraphSchema's canonical dtype vocabulary. Do not normalize or accept aliases:
# GraphSchema is responsible for enforcing these exact values.
_DTYPE_TO_PYTHON_TYPE = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


# Inheritance is deliberately outside the scope of this iteration.
_EXCLUDED_LINK_NAMES = {"INSTANCE_OF"}

# Private Python attributes are not part of the public GraphQL schema.
_INTERNAL_ID_ATTRIBUTE = "_ba_internal_id"



#######################################################################################

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

    The expected result is a list/sequence of strings. A sequence of
    dictionaries or objects with a `name` or `class_name` member is also
    accepted for convenience. Explicitly invisible entries are ignored.
    """
    if class_results is None:
        return []

    if isinstance(class_results, str):
        entries = [class_results]
    elif isinstance(class_results, Mapping):
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
    seen_names = set()

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

        if class_name in seen_names:
            raise ValueError(
                f"GraphSchema returned duplicate visible class name "
                f"{class_name!r}."
            )
        seen_names.add(class_name)

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
    """
    Read and validate the GraphQL-visible properties of one class.

    A property is exposed only when `visible` is present and is exactly True.
    Its dtype must use one of GraphSchema's four canonical identifiers.

    :param class_name:  The name of the Schema class of interest
    :return:
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
        is_required = property_definition.get("required") is True

        visible_properties.append(
            {
                "name": property_name,
                "python_type": python_type,
                "required": is_required,
                "python_field_name": f"ba_property_{len(visible_properties)}",
            }
        )

    return visible_properties



def _get_outgoing_class_links(class_name: str, visible_class_names: set) -> List[dict]:
    """Return outgoing links whose target CLASS is also GraphQL-visible.

    GraphSchema.get_class_links_full_data() is a proposed GraphSchema API
    introduced for this iteration. See the module docstring for its contract.
    """
    get_links = getattr(GraphSchema, "get_class_links_full_data", None)
    if not callable(get_links):
        raise NotImplementedError(
            "This GraphQL iteration requires "
            "GraphSchema.get_class_links_full_data(class_name=...). "
            "Implement it to return outgoing LINK definitions as dictionaries "
            "with 'name' and 'target_class' keys."
        )

    link_definitions = get_links(class_name=class_name)
    if link_definitions is None:
        link_definitions = []

    visible_links = []
    seen_link_names = set()

    for link_definition in link_definitions:
        if not isinstance(link_definition, Mapping):
            raise TypeError(
                "GraphSchema.get_class_links_full_data() must return "
                "dictionaries describing links; got "
                f"{type(link_definition).__name__}."
            )

        link_name = link_definition.get("name")
        if link_name in _EXCLUDED_LINK_NAMES:
            continue

        target_class = link_definition.get("target_class")

        # A relationship is visible when both endpoint classes are visible.
        # The source class is already known to be visible; filter by target.
        if target_class not in visible_class_names:
            continue

        link_name = _validate_graphql_name(
            link_name,
            description=f"LINK name on class {class_name!r}",
        )
        target_class = _validate_graphql_name(
            target_class,
            description=f"target class of LINK {link_name!r}",
        )

        if link_name in seen_link_names:
            raise ValueError(
                f"Class {class_name!r} has multiple visible outgoing LINK "
                f"definitions named {link_name!r}. GraphQL field names must "
                "be unique within an object type."
            )
        seen_link_names.add(link_name)

        visible_links.append(
            {
                "name": link_name,
                "target_class": target_class,
                "python_field_name": f"ba_link_{len(visible_links)}",
            }
        )

    return visible_links



def _discover_class_definitions() -> dict:
    """Discover visible classes, properties and outgoing semantic links."""
    class_names = _get_visible_class_names()
    if not class_names:
        raise ValueError(
            "GraphSchema returned no classes marked visible=True; cannot "
            "generate a GraphQL Query type with no fields."
        )

    visible_class_names = set(class_names)
    definitions = {}

    for class_name in class_names:
        properties = _get_visible_properties(class_name)
        links = _get_outgoing_class_links(class_name, visible_class_names)

        property_names = {prop["name"] for prop in properties}
        link_names = {link["name"] for link in links}
        collisions = property_names.intersection(link_names)
        if collisions:
            raise ValueError(
                f"Class {class_name!r} has a property and a LINK with the "
                f"same GraphQL field name(s): {sorted(collisions)!r}."
            )

        definitions[class_name] = {
            "properties": properties,
            "links": links,
        }

    # GraphQL object types must have at least one field. A class can now
    # qualify through either visible scalar properties OR relationships.
    # Repeated pruning removes links to classes that themselves have no
    # selectable fields, while retaining relationship-only cycles such as
    # A -> B -> A (both object types have a field).
    active_classes = set(class_names)
    while True:
        remove_classes = set()
        for class_name in active_classes:
            properties = definitions[class_name]["properties"]
            links_to_active_classes = any(
                link["target_class"] in active_classes
                for link in definitions[class_name]["links"]
            )
            if not properties and not links_to_active_classes:
                remove_classes.add(class_name)

        if not remove_classes:
            break

        for class_name in sorted(remove_classes):
            _LOGGER.warning(
                "Not exposing visible GraphSchema class %r: it has no "
                "visible scalar properties and no outgoing relationship to "
                "another exposable class.",
                class_name,
            )
        active_classes.difference_update(remove_classes)

    if not active_classes:
        raise ValueError(
            "No visible GraphSchema classes have any visible scalar "
            "properties or relationships to other exposable classes."
        )

    # Remove links whose target classes were pruned.
    for class_name in active_classes:
        definitions[class_name]["links"] = [
            link
            for link in definitions[class_name]["links"]
            if link["target_class"] in active_classes
        ]

    # Re-number internal field names after pruning for readability/debugging.
    for class_name in active_classes:
        for index, prop in enumerate(definitions[class_name]["properties"]):
            prop["python_field_name"] = f"ba_property_{index}"
        for index, link in enumerate(definitions[class_name]["links"]):
            link["python_field_name"] = f"ba_link_{index}"

    # Preserve the ordering supplied by GraphSchema.
    ordered_definitions = {
        class_name: definitions[class_name]
        for class_name in class_names
        if class_name in active_classes
    }
    return ordered_definitions



def _adapt_data_records(
    class_name: str,
    records: Any,
    definitions: dict,
    strawberry_types: dict,
) -> List[Any]:
    """Convert GraphSchema data-node dictionaries to generated Strawberry objects."""
    if records is None:
        return []

    result_objects = []
    class_definition = definitions[class_name]
    has_outgoing_links = bool(class_definition["links"])
    strawberry_object_type = strawberry_types[class_name]

    for record_index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError(
                "GraphSchema data-node retrieval was expected to return "
                f"dictionaries for class {class_name!r}; got "
                f"{type(record).__name__}."
            )

        internal_id = record.get("_internal_id")
        if has_outgoing_links and internal_id is None:
            raise ValueError(
                f"Data node #{record_index} of class {class_name!r} has "
                "outgoing GraphQL relationships but its record does not "
                "contain a non-null '_internal_id'."
            )

        constructor_values = {_INTERNAL_ID_ATTRIBUTE: internal_id}

        for property_info in class_definition["properties"]:
            property_name = property_info["name"]
            value = record.get(property_name)

            if property_info["required"] and value is None:
                raise ValueError(
                    f"Data node #{record_index} of class {class_name!r} "
                    f"does not provide a non-null value for required "
                    f"property {property_name!r}."
                )

            constructor_values[property_info["python_field_name"]] = value

        result_objects.append(strawberry_object_type(**constructor_values))

    return result_objects



def _make_root_resolver(class_name: str, definitions: dict, strawberry_types: dict):
    """Create the root resolver for one visible semantic class."""
    def resolve_class_records() -> List[Any]:
        records = GraphSchema.get_data_nodes_of_class(class_name=class_name)
        return _adapt_data_records(
            class_name,
            records,
            definitions,
            strawberry_types,
        )

    return resolve_class_records



def _make_link_resolver(
    source_class: str,
    link_definition: dict,
    definitions: dict,
    strawberry_types: dict):
    """
    Create a resolver that follows one data relationship on demand

    :param source_class:
    :param link_definition:
    :param definitions:
    :param strawberry_types:
    :return:
    """
    link_name = link_definition["name"]
    target_class = link_definition["target_class"]
    target_type_symbol = link_definition["target_type_symbol"]

    def resolve_link(parent):
        source_node_id = getattr(parent, _INTERNAL_ID_ATTRIBUTE, None)
        if source_node_id is None:
            raise ValueError(
                f"Cannot resolve LINK {link_name!r} from class "
                f"{source_class!r}: the source object has no internal node ID."
            )

        get_linked_nodes = getattr(GraphSchema, "get_linked_data_nodes", None)
        if not callable(get_linked_nodes):
            raise NotImplementedError(
                "This GraphQL relationship query requires "
                "GraphSchema.get_linked_data_nodes(source_node_id=..., "
                "link_name=..., target_class=...). Implement it to return "
                "the connected target data-node records."
            )

        linked_records = get_linked_nodes(
            source_node_id=source_node_id,
            link_name=link_name,
            target_class=target_class,
        )

        return _adapt_data_records(
            target_class,
            linked_records,
            definitions,
            strawberry_types,
        )

    # Strawberry recognizes Parent[T] as the parent object supplied to a
    # field resolver. The target return annotation mirrors the field
    # annotation (a list of the lazily referenced generated object type).
    resolve_link.__annotations__ = {
        "parent": strawberry.Parent[Any],
        "return": List[
            Annotated[target_type_symbol, strawberry.lazy(__name__)]
        ],
    }
    resolve_link.__name__ = f"resolve_{source_class}_{link_name}"
    return resolve_link



def build_graphql_schema():
    """Build and return a Strawberry schema from visible GraphSchema metadata.

    The function is separate from Flask registration so it can be called
    independently to inspect the generated SDL:

        generated_schema = build_graphql_schema()
        print(generated_schema.as_str())
    """
    definitions = _discover_class_definitions()

    # Give each build a fresh set of internal Python type symbols. Strawberry's
    # lazy references resolve these names through this module's namespace,
    # allowing mutually-referencing semantic classes to be generated.
    generation_token = uuid4().hex
    type_symbols = {
        class_name: f"_BA_GRAPHQL_TYPE_{generation_token}_{index}"
        for index, class_name in enumerate(definitions)
    }

    # First create every raw Python class and publish it in module globals.
    # The relationship annotations below refer to these symbols lazily, so
    # self-references and mutual relationships are supported.
    raw_python_types = {}
    strawberry_types = {}  # Shared registry populated after decorating all types.

    for class_name, class_definition in definitions.items():
        annotations = {}
        class_namespace = {
            "__module__": __name__,
            "__annotations__": annotations,
        }

        # Retain each data node's internal Neo4j ID privately. It is not a
        # GraphQL field, but nested relationship resolvers need it.
        annotations[_INTERNAL_ID_ATTRIBUTE] = strawberry.Private[Any]
        class_namespace[_INTERNAL_ID_ATTRIBUTE] = None

        for property_info in class_definition["properties"]:
            python_field_name = property_info["python_field_name"]
            property_name = property_info["name"]
            python_type = property_info["python_type"]
            is_required = property_info["required"]

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

        for link_definition in class_definition["links"]:
            python_field_name = link_definition["python_field_name"]
            link_name = link_definition["name"]
            target_class = link_definition["target_class"]
            target_symbol = type_symbols[target_class]
            link_definition["target_type_symbol"] = target_symbol

            # The annotation resolves to list[TargetType], but the target
            # Strawberry class may be declared later (or be this same class).
            target_annotation = Annotated[
                target_symbol,
                strawberry.lazy(__name__),
            ]
            annotations[python_field_name] = List[target_annotation]

            class_namespace[python_field_name] = strawberry.field(
                name=link_name,
                resolver=_make_link_resolver(
                    class_name,
                    link_definition,
                    definitions,
                    # This shared dictionary is populated after all types
                    # are decorated; the resolver closes over it by reference.
                    strawberry_types,
                ),
            )

        raw_type = type(type_symbols[class_name], (), class_namespace)
        globals()[type_symbols[class_name]] = raw_type
        raw_python_types[class_name] = raw_type

    # Decorate all raw classes as Strawberry types. The explicit `name`
    # preserves the exact semantic class name in the GraphQL schema.
    for class_name, raw_type in raw_python_types.items():
        strawberry_types[class_name] = strawberry.type(
            raw_type,
            name=class_name,
        )
        # Make sure strawberry.lazy() finds the decorated class object.
        globals()[type_symbols[class_name]] = strawberry_types[class_name]

    # Create the root Query type. Root resolvers use the fully populated type
    # registry when adapting data-node records.
    query_annotations = {}
    query_namespace = {
        "__module__": __name__,
        "__annotations__": query_annotations,
    }

    for index, class_name in enumerate(definitions):
        internal_query_field_name = f"ba_query_field_{index}"
        object_type = strawberry_types[class_name]
        query_annotations[internal_query_field_name] = List[object_type]
        query_namespace[internal_query_field_name] = strawberry.field(
            name=class_name,
            resolver=_make_root_resolver(
                class_name,
                definitions,
                strawberry_types,
            ),
        )

    dynamic_query_class = type("_BA_GraphQL_Query", (), query_namespace)
    strawberry_query_type = strawberry.type(dynamic_query_class, name="Query")

    return strawberry.Schema(
        query=strawberry_query_type,
        config=StrawberryConfig(auto_camel_case=False),
    )



def register_graphql_2(app) -> None:
    """Generate and register /graphql_2 on an existing Flask application.

    Call this from the Brain Annex application factory after GraphSchema has
    been initialized. The GraphQL schema is generated at registration/startup
    time; data records are fetched when their root or relationship fields are
    queried.

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
