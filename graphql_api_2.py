"""Dynamically generated Strawberry GraphQL API for Brain Annex.

This module builds an executable GraphQL schema from Brain Annex's semantic
metadata ("GraphSchema").

It does NOT contain handwritten Strawberry object
classes for each domain class. Instead, it reads the metadata at application
startup and creates the corresponding Python/Strawberry types programmatically.



USAGE EXAMPLE
------------------------

A simple query might look like this:

    {
        Entrees {
            name
            eval

            BA_served_at {
                name
                address
                city
                notes
            }
        }
    }

The names above are *illustrative*; actual class, property, and LINK names come
from the semantic database and are preserved exactly when valid in GraphQL.



HOW THE DYNAMIC GENERATION WORKS
--------------------------------

In an ordinary Strawberry application, a developer writes Python classes
manually, for example::

    @strawberry.type
    class Restaurant:
        name: str
        address: str

Strawberry examines the class's annotations and turns it into a GraphQL object
type. This module performs the equivalent operation at runtime:

* It reads class and property definitions from ``GraphSchema``.
* It builds a Python class namespace containing ``__annotations__`` and field
definitions derived from those metadata records.
* Python's built-in ``type(name, bases, namespace)`` creates the class.
* ``strawberry.type(...)`` decorates that class, registering it as a Strawberry
  object type.

Consequently, the schema remains code-first from Strawberry's perspective,
but the Python class definitions are generated rather than handwritten. The
semantic database is the source of truth; this module translates its metadata
into Strawberry's runtime type system.

The generated Python attribute names (for example, ``ba_property_0``) are
internal implementation details. ``strawberry.field(name=...)`` gives each
field its public GraphQL name from the semantic metadata. This separation
avoids Python attribute-name collisions while preserving the desired GraphQL
names exactly.



CURRENT SCOPE
-------------

* Discover semantic classes marked ``visible=True``.
* Expose only class properties marked ``visible=True``.
* Use GraphSchema's canonical dtypes: ``str``, ``int``, ``float``, ``bool``.
* Treat PROPERTY ``required`` as true only when explicitly ``True``.
* Discover outgoing semantic LINK definitions between visible classes.
* Represent each relationship as a direct nested GraphQL field pointing to
the destination class. LINK-node properties are intentionally ignored.
* Fetch related data nodes lazily, only when a relationship field is requested,
using the source data node's Neo4j internal ID.
* Exclude ``INSTANCE_OF``; inheritance is a separate future iteration.



GRAPHSCHEMA SERVICE CONTRACTS
-----------------------------

Two GraphSchema methods are used for relationship traversal:

1. ``GraphSchema.get_class_links_full_data(class_name=...)``

   Returns outgoing semantic LINK definitions for the source class, e.g.::

       [
           {"name": "WORKS_FOR", "target_class": "Employer"},
           {"name": "LIVES_IN", "target_class": "City"},
       ]

   ``name`` is the LINK node's semantic name. ``target_class`` is the name of
the destination CLASS node. The method should return only links outgoing from
the requested source class. Extra metadata may be included, but is ignored
here. Properties attached to LINK nodes are also ignored in this iteration.

2. ``GraphSchema.get_linked_data_nodes(source_node_id=..., link_name=...,
   target_class=...)``

   Returns the target data-node records reached by following the named outgoing
data relationship from the source node. The return format is the same as
``get_data_nodes_of_class()``: a list of dictionaries containing ordinary data
properties plus ``_internal_id`` and ``_node_labels``.

   This method is called only when the corresponding GraphQL relationship
field is selected by a client. The source node's ``_internal_id`` is retained
inside a Strawberry object as a private Python attribute; it is not exposed as
a GraphQL field.



VISIBILITY AND CARDINALITY
--------------------------

A class is considered for exposure when its CLASS metadata is visible. A
relationship is exposed when both its source and target CLASS nodes are
visible; there is no separate LINK visibility flag in this version. A class
with no visible scalar properties can still be exposed if it has a usable
relationship field. Classes that have neither a visible property nor a
relationship leading to another exposable class are omitted, because GraphQL
object types must have at least one field.

Until GraphSchema provides cardinality metadata, every relationship field is
represented as a non-null list of non-null destination objects. No matches
produce an empty list, not ``null``.



NAMING
------

Semantic class names, property names, LINK names, and root query field names
are preserved exactly. Invalid GraphQL names are rejected instead of silently
rewritten. Automatic camel-casing is disabled so that, for example, a semantic
name ``served_at`` is not silently changed to ``servedAt``.
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


# GraphQL names use the ASCII grammar [_A-Za-z][_0-9A-Za-z]*. The validation
# helper below also rejects names beginning with double underscore because
# GraphQL reserves that prefix for introspection-related names.
_GRAPHQL_NAME_PATTERN = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")


# These names are already occupied by GraphQL built-in scalar types or by the
# dynamically generated root query type. A semantic CLASS cannot reuse them.
_RESERVED_GRAPHQL_TYPE_NAMES = {
    "Boolean",
    "Float",
    "ID",
    "Int",
    "Query",
    "String"
}


# GraphSchema's canonical dtype vocabulary. Do not normalize or accept aliases:
# GraphSchema is responsible for enforcing these exact values. The Python types
# on the right become GraphQL scalars when Strawberry processes the annotations
# (str -> String, int -> Int, float -> Float, bool -> Boolean).
_DTYPE_TO_PYTHON_TYPE = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
}


# Inheritance is deliberately outside the scope of this iteration.
_EXCLUDED_LINK_NAMES = {"INSTANCE_OF"}

# Private Python attributes are not part of the public GraphQL schema.
# Each generated data object carries its source node's Neo4j internal ID here.
# A nested relationship resolver needs that ID to find the related data nodes;
# clients cannot select this attribute because Strawberry treats it as Private.
_INTERNAL_ID_ATTRIBUTE = "_ba_internal_id"




#######################################################################################

def _python_type_for_dtype(dtype: Any, property_name: str) -> Type:
    """Translate one canonical GraphSchema dtype into its Python type.

    Strawberry uses Python annotations to infer GraphQL scalar types. This
    helper therefore converts the semantic vocabulary into Python's built-in
types before the dynamic Strawberry class is decorated.

    No case folding, aliases, or coercion is attempted. A value such as
    ``"string"`` is an error: GraphSchema is responsible for storing only the
    canonical identifiers ``str``, ``int``, ``float``, and ``bool``.

    :param dtype:           The exact dtype identifier read from a PROPERTY definition.
    :param property_name:   Property name, included to make an error actionable.
    :return:                The corresponding Python type object (``str``, ``int``,
                                ``float``, or ``bool``).
    :raises ValueError:     If ``dtype`` is not one of the four canonical values.
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
    """
    Validate a semantic name against GraphQL's name rules.

    GraphQL names must begin with an ASCII
    letter or underscore, and the remaining characters may additionally
    include digits.
    Names beginning with ``__`` are reserved by GraphQL.

    We preserve valid names exactly rather than trying to pluralize, change
    capitalization, or convert snake_case to camelCase.
    This is important because the semantic layer is the source of truth for public names.

    :param name:        Candidate class, property, or LINK name from GraphSchema
    :param description: Human-readable description used in error messages
    :return:            The original name, unchanged, after successful validation
    :raises ValueError: If the value is not a valid public GraphQL name
    """
    if type(name) is not str:
        raise ValueError(
            f"Cannot expose {description} {name!r} in GraphQL. Names must be strings; "
            f"the passed argument is of type {type(name)}"
        )

    if (
        not _GRAPHQL_NAME_PATTERN.fullmatch(name)
        or name.startswith("__")
    ):
        raise ValueError(
            f"Cannot expose {description} {name!r} in GraphQL. Names must be strings"
            "matching [_A-Za-z][_0-9A-Za-z]* and must not begin with '__'. "
            "No automatic renaming is performed."
        )
    return name



def _normalise_class_name_results(class_results: Any) -> List[str]:
    """Normalize the result returned by ``get_all_classes`` into class names.

    The normal expected result is an iterable of strings. For convenience,
    this helper also accepts a single string, a mapping describing one class,
    a mapping keyed by class name, or an iterable of dictionaries/objects with
    a ``name`` or ``class_name`` member. This tolerance is confined to the
    shape of the returned records; it does not normalize the names themselves.

    ``get_all_classes(only_visible=True)`` should already filter invisible
    classes. If the result records include a ``visible`` member, an explicit
    ``False`` is filtered out defensively. Plain string entries are accepted
    because the visibility decision has already been made by GraphSchema.

    Duplicate names and names invalid for GraphQL are rejected rather than
    silently discarded or rewritten.

    :param class_results:   Result of ``GraphSchema.get_all_classes``.
    :return:                Class names in the order supplied by GraphSchema.
    :raises TypeError:      If the result cannot be interpreted as an iterable of
                                class names or class-description records.
    :raises ValueError:     If a name is invalid, duplicated, or reserved by
                                GraphQL.
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
    """Return the class names that GraphSchema has selected for exposure.

    The semantic library performs the visibility filter through
    ``only_visible=True``. The normalizer then validates the returned names
    and makes their representation predictable for the rest of this module.

    :return:            Visible semantic class names, preserving GraphSchema's order.
    :raises ValueError: If GraphSchema returns duplicate, reserved, or
                            GraphQL-invalid class names.
    """
    class_results = GraphSchema.get_all_classes(only_visible=True)
    return _normalise_class_name_results(class_results)



def _get_visible_properties(class_name: str) -> List[dict]:
    """Read and prepare the visible scalar properties of one semantic class.

    Every PROPERTY definition is inspected, but only a record whose
    ``visible`` value is exactly ``True`` becomes a GraphQL field. A missing
    flag, ``False``, or another value does not qualify. Its ``dtype`` must be
    exactly one of GraphSchema's four canonical identifiers.

    The returned dictionaries contain both the public semantic field name and
    an internal Python field name such as ``ba_property_0``. This distinction
    matters for dynamic class construction: the internal name is guaranteed
    to be a safe, unique Python attribute, while ``strawberry.field(name=...)``
    publishes the original semantic name in GraphQL.

    ``required`` is interpreted conservatively: it is true only when the
    metadata value is exactly ``True``. Otherwise the generated field is
    nullable (and its Python annotation will be Optional).

    :param class_name:  Exact name of the semantic CLASS whose properties are
                            being retrieved.
    :return:    Ordered property descriptors. Each contains ``name`` (the public
                    GraphQL name), ``python_type`` (the Python scalar type), ``required``
                    (a Boolean), and ``python_field_name`` (the generated Python attribute).
    :raises TypeError:  If GraphSchema returns a property record that is not a
                            mapping/dictionary.
    :raises ValueError: If a visible property has an invalid/duplicate name or
                            an unsupported dtype.
    """
    property_definitions = GraphSchema.get_class_properties_full_data(
        class_name=class_name
    )
    # Example property metadata (only name, dtype, visible, and required are
    # needed here; other semantic metadata remains available to other consumers):
    #     {
    #         "name": "address",
    #         "dtype": "str",       # canonical GraphSchema dtype
    #         "visible": True,
    #         "required": False,
    #         "description": "Street address of the restaurant"
    #     }

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
    """Find the source class's outgoing LINKs that may appear in GraphQL.

    ``GraphSchema.get_class_links_full_data`` describes semantic relationships
    originating at ``class_name``. The source class is already known to be
    visible; this function applies the other half of the agreed visibility
    rule by retaining only links whose destination CLASS is also visible.

    A LINK is represented here as a *direct nested GraphQL field* returning a
    list of destination objects. The LINK node itself does not become a
    GraphQL type in this iteration, and properties attached to LINK nodes are
    deliberately ignored. ``INSTANCE_OF`` is also excluded because inheritance
    is outside the current scope.

    As with properties, the public GraphQL field name is kept separately from
    an internal synthetic Python attribute name (``ba_link_0``, etc.).

    :param class_name:          Visible source CLASS name whose outgoing links are read.
    :param visible_class_names: Set of all class names selected for GraphQL;
        a link is retained only if its ``target_class`` belongs to this set.
    :return:    Ordered link descriptors containing ``name``, ``target_class``,
        and ``python_field_name``.
    :raises NotImplementedError: If the required GraphSchema link-discovery
        method has not yet been implemented.
    :raises TypeError:          If the method returns a link record that is not a mapping.
    :raises ValueError:         If a visible link name or target class is invalid, or
        if the source class has duplicate outgoing GraphQL field names.
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
    """Build the complete, mutually consistent set of exposed class metadata.

    This is the metadata-discovery phase of schema generation. It does not yet
    create Python classes or execute data queries. For each visible CLASS, it
    collects its visible scalar properties and its outgoing links to other
    visible classes.

    A property and a relationship field share the same GraphQL object-type
    namespace, so a class cannot expose both under the same name.

    GraphQL object types must contain at least one field. Therefore, a class
    qualifies if it has at least one visible scalar property or at least one
    relationship to another qualifying class. The repeated pruning loop finds
    this set as a fixed point: a class that points only to an unusable class
    becomes unusable itself. Conversely, a relationship-only cycle such as
    ``A -> B -> A`` remains valid because both types have fields.

    :return:            An insertion-ordered dictionary keyed by exposed semantic class
                            name. Each value contains ``properties`` and ``links`` descriptors.
    :raises ValueError: If no usable classes remain, or if metadata contains
                            duplicate/conflicting GraphQL field names.
    :raises TypeError:  If the GraphSchema metadata records have invalid shapes.
    """
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
    """Adapt data-layer records into instances of a generated Strawberry type.

    GraphSchema returns dictionaries representing individual Neo4j data nodes.
    Strawberry, however, resolves a generated object's fields as Python
    attributes. This adapter bridges the two representations: it copies only
    the properties selected for GraphQL into the corresponding generated
    object's constructor arguments.

    The record's ``_internal_id`` is copied to a ``strawberry.Private``
    attribute. It is deliberately absent from the public GraphQL schema, but
    nested relationship resolvers need it to identify the exact source node.
    It is required here only when this class has outgoing exposed links.

    The function also enforces ``required=True`` at data-fetch time. GraphQL
    non-null annotations describe the API contract; checking the actual record
    here turns a mismatch between metadata and stored data into a clear error.

    Hidden properties are never copied into the generated object, even if they
    happen to be present in the Neo4j record. This prevents them from leaking
    through the GraphQL API.

    :param class_name:  Semantic class whose records are being adapted.
    :param records:     Iterable of dictionaries returned by
        ``GraphSchema.get_data_nodes_of_class`` or
        ``GraphSchema.get_linked_data_nodes``. ``None`` is treated as no records.
    :param definitions: Complete metadata dictionary returned by
        ``_discover_class_definitions``.
    :param strawberry_types: Registry mapping semantic class names to the
        corresponding dynamically generated Strawberry type objects.
    :return:            A list of instances of the generated Strawberry object type.
    :raises TypeError:  If any data record is not a mapping/dictionary.
    :raises ValueError: If a required property is null/missing, or if a node
        needs an outgoing relationship resolver but has no ``_internal_id``.
    """
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
    """Create the resolver used by one root query field.

    A root query field corresponds to one visible semantic class. For example,
    the generated root field ``Restaurants`` calls a resolver created here
    with ``class_name="Restaurants"``.

    This is a *resolver factory*: it closes over the class name and the two
    schema-generation registries, then returns a small resolver function for
    Strawberry to call when a client selects that root field. The database is
    not queried while the schema is being built; the query runs only when the
    corresponding GraphQL field is requested.

    :param class_name:  Semantic class represented by this root query field.
    :param definitions: Complete class/property/LINK metadata for this schema.
    :param strawberry_types: Registry of generated Strawberry object types,
        used by the record adapter to construct the right object instances.
    :return:    A zero-argument resolver callable returning a list of generated
        Strawberry objects.
    """
    def resolve_class_records() -> List[Any]:
        """Fetch and adapt all data nodes belonging to the captured class.

        :return: Data-node objects ready for Strawberry field resolution.
        """
        records = GraphSchema.get_data_nodes_of_class(class_name=class_name)
        # GraphSchema returns a list of dictionaries. Each dictionary contains
        # ordinary node properties plus internal metadata such as _internal_id
        # and _node_labels. _adapt_data_records copies only the selected public
        # properties into a Strawberry object and stores the ID privately.

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
    """Create a resolver factory for one outgoing semantic relationship.

    The returned resolver is attached to a generated Strawberry field. It is
    invoked only if a client selects that field in a GraphQL query. This is the
    important lazy-traversal behavior: requesting ``Person { name }`` does not
    fetch employers, while requesting ``Person { WORKS_FOR { name } }`` does.

    Strawberry supplies the parent object (the source data node represented by
    the current GraphQL object). Its private internal ID identifies the exact
    Neo4j node from which traversal should begin. The resolver passes that ID,
    the semantic LINK name, and the destination class to GraphSchema's data
    service, then adapts the returned dictionaries into destination objects.

    :param source_class:    Semantic class at the source end of the relationship;
        used in diagnostics and for naming the resolver.
    :param link_definition: Descriptor for this relationship, including its
        semantic ``name``, ``target_class``, and generated target-type symbol.
    :param definitions: Complete metadata for every exposed class, used when
        adapting the related records.
    :param strawberry_types: Shared registry of generated Strawberry types.
        It is populated after all types have been decorated; this resolver
        closes over the dictionary itself, not a snapshot of its contents.

    :return:            A Strawberry-compatible field resolver with a parent argument and
        a list-of-target-objects return annotation.
    :raises ValueError: At query execution time, if the parent object has no
        internal node ID.
    :raises NotImplementedError: At query execution time, if the required
        ``GraphSchema.get_linked_data_nodes`` service has not been implemented.
    """
    link_name = link_definition["name"]
    target_class = link_definition["target_class"]
    target_type_symbol = link_definition["target_type_symbol"]

    def resolve_link(parent):
        """Resolve this relationship for one source object supplied by Strawberry.

        ``parent`` is the Python object corresponding to the source GraphQL
        object. The internal ID is intentionally obtained from that object,
        not from a user-supplied GraphQL argument: the traversal follows the
        particular source record currently being resolved.

        :param parent:  Generated Strawberry instance at the source end of the
            LINK. Strawberry provides it through the resolver's Parent type.
        :return:        A list of generated objects representing all connected target
            data nodes; an empty list means that no matching connection exists.
        """
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

    # Strawberry's Parent[T] annotation marks the first resolver parameter as
    # the object on which this field is being resolved. It is not a GraphQL
    # argument and does not appear in the public schema.
    #
    # We assign __annotations__ explicitly because this resolver is a nested
    # function created at runtime. Its return annotation must describe the same
    # list-of-target-type shape as the field annotation created below. The
    # target type is referenced lazily because it may be generated later, or it
    # may be the source type itself (a self-relationship).
    resolve_link.__annotations__ = {
        "parent": strawberry.Parent[Any],
        "return": List[
            Annotated[target_type_symbol, strawberry.lazy(__name__)]
        ],
    }
    resolve_link.__name__ = f"resolve_{source_class}_{link_name}"
    return resolve_link



def build_graphql_schema():
    """Generate and return an executable Strawberry schema from GraphSchema.

    This function is intentionally independent of Flask. It can be called on
    its own to inspect or test the generated schema definition language (SDL)::

        generated_schema = build_graphql_schema()
        print(generated_schema.as_str())

    STRAWBERRY'S CODE-FIRST MODEL, GENERATED AT RUNTIME
    ---------------------------------------------------

    A normal code-first Strawberry application declares each type in source
    code with ``@strawberry.type`` and Python annotations. Here, the semantic
    metadata supplies the information that a developer would otherwise write
    by hand. The function creates equivalent Python classes dynamically and
    passes them through Strawberry's decorator/schema machinery.

    The generation proceeds in phases:

    1. Discover visible class, property, and relationship definitions.
    2. Allocate a unique internal Python symbol for every semantic class.
       These symbols are not the public GraphQL type names; they are safe names
       that can be placed in this module's namespace for lazy resolution.
    3. Create the raw Python classes. Their ``__annotations__`` dictionaries
       describe scalar fields and relationship fields, just as annotations in
       a handwritten class would. ``strawberry.field(name=...)`` maps each
       internal Python attribute to the exact semantic GraphQL field name.
    4. Decorate every raw class with ``strawberry.type``. The explicit
       ``name=class_name`` sets the public GraphQL object type name.
    5. Build and decorate a separate root ``Query`` class. Each of its fields
       corresponds to one visible semantic class and has a resolver that fetches
       records of that class.
    6. Assemble the executable ``strawberry.Schema`` and disable automatic
       camel-casing so GraphQL names match the semantic metadata exactly.

    WHY TWO PASSES FOR THE OBJECT TYPES?
    -----------------------------------

    A relationship may point to a type that has not yet been created. It may
    also point back to the source type, creating a cycle. We therefore create
    all raw classes and publish their temporary symbols in this module's
    globals first. Relationship annotations use ``strawberry.lazy`` to defer
    resolving those symbols until Strawberry processes the schema. We then
    decorate all raw classes and replace the temporary global entries with the
    corresponding Strawberry-decorated classes.

    The unique generation token prevents a second schema build in the same
    process from reusing the temporary type names from an earlier build.

    :return: A fully executable ``strawberry.Schema`` whose types and fields
        reflect the visible GraphSchema metadata discovered at call time.
    :raises ValueError: If the metadata cannot be represented by valid GraphQL
        names/types, if there are conflicting fields, or if no exposable class
        remains.
    :raises TypeError: If GraphSchema returns malformed class/property/LINK
        metadata.
    :raises NotImplementedError: If the LINK-discovery service required for
        relationship generation is unavailable.
    """
    definitions = _discover_class_definitions()

    # Give each build a fresh set of internal Python type symbols. These are
    # implementation names only; the public GraphQL names remain the semantic
    # class names. Strawberry's lazy references look up these symbols through
    # this module's namespace, allowing mutually-referencing classes to work.
    generation_token = uuid4().hex
    type_symbols = {
        class_name: f"_BA_GRAPHQL_TYPE_{generation_token}_{index}"
        for index, class_name in enumerate(definitions)
    }

    # First create every raw Python class and publish it in module globals.
    # This first pass is necessary because a class may refer to a destination
    # type that has not been built yet. The lazy relationship annotations below
    # defer looking up that destination until Strawberry assembles the schema.
    raw_python_types = {}
    # Resolvers close over this shared dictionary. It is populated in the next
    # pass, after all raw classes have been decorated as Strawberry types.
    strawberry_types = {}

    for class_name, class_definition in definitions.items():
        annotations = {}
        class_namespace = {
            "__module__": __name__,
            "__annotations__": annotations,
        }

        # Retain each data node's internal Neo4j ID privately. Strawberry's
        # Private marker tells Strawberry not to include this attribute in the
        # GraphQL schema. The runtime value is attached when records are adapted
        # and is later used as the source-node identifier for relationship
        # traversal. It is not a public field and clients cannot query it.
        annotations[_INTERNAL_ID_ATTRIBUTE] = strawberry.Private[Any]
        class_namespace[_INTERNAL_ID_ATTRIBUTE] = None

        # Add the class's visible scalar properties. The annotation determines
        # the GraphQL scalar type; Optional[...] means that the field is nullable.
        # The generated Python name is deliberately separate from the public
        # GraphQL name stored in property_info["name"].
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

        # Add outgoing semantic relationships as nested object fields. Unlike
        # scalar properties, these fields return a list of another generated
        # object type. Their resolver performs the actual graph traversal only
        # if the client selects the relationship in a query.
        for link_definition in class_definition["links"]:
            python_field_name = link_definition["python_field_name"]
            link_name = link_definition["name"]
            target_class = link_definition["target_class"]
            target_symbol = type_symbols[target_class]
            link_definition["target_type_symbol"] = target_symbol

            # The annotation describes list[TargetType]. The target Strawberry
            # class may be declared later in this loop, or may be this same
            # class in a self-relationship, so use a lazy reference by symbol.
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

    # Second pass: decorate each dynamically created Python class. This is the
    # runtime equivalent of writing @strawberry.type above a handwritten class.
    # The explicit name=... preserves the exact semantic CLASS name in GraphQL,
    # even though the actual Python class has a generated internal name.
    for class_name, raw_type in raw_python_types.items():
        strawberry_types[class_name] = strawberry.type(
            raw_type,
            name=class_name,
        )
        # Make sure strawberry.lazy() finds the decorated class object.
        globals()[type_symbols[class_name]] = strawberry_types[class_name]

    # Build the root Query object type. In GraphQL, Query is the entry point for
    # ordinary read operations: each field below is one semantic class that a
    # client can request (for example, { Restaurants { name } }). The synthetic
    # Python attribute names avoid collisions; field(name=class_name) supplies
    # the exact public GraphQL field name.

    # By now strawberry_types is fully populated, so each root resolver can
    # adapt its returned data dictionaries into the correct generated type.
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
    """Generate the dynamic schema and register its HTTP endpoint with Flask.

    Call this function from Brain Annex's application factory after the
    ``GraphSchema`` semantic database and its access services are initialized.
    It builds the Strawberry schema immediately, then attaches Strawberry's
    Flask ``GraphQLView`` to the existing Flask application.

    Schema generation happens at application startup, so changes to semantic
    visibility, property definitions, dtypes, or LINK definitions require the
    application to rebuild/restart before they appear in the GraphQL schema.
    Actual application data is different: records are fetched by resolvers
    when a client executes a query, and relationship data is fetched only when
    the client selects the corresponding nested field.

    :param app: The existing Flask application object created by Brain Annex's
        application factory. This function registers a route on that object;
        it does not create a second Flask application.
    :return:    None. The Flask application is modified in place by registering
        ``GRAPHQL_URL`` with the unique Flask endpoint name
        ``FLASK_ENDPOINT_NAME``.
    :raises ValueError: If GraphSchema metadata cannot be represented as a
        valid GraphQL schema.
    :raises NotImplementedError: If required GraphSchema relationship metadata
        services are unavailable.
    """
    generated_schema = build_graphql_schema()

    app.add_url_rule(
        GRAPHQL_URL,
        view_func=GraphQLView.as_view(
            FLASK_ENDPOINT_NAME,
            schema=generated_schema,
        ),
    )
