"""Backend-neutral view of the protos in a CodeGeneratorRequest.

Nested types are flattened (Navigation.Geodetic -> NavigationGeodetic) since
neither ROS 2 nor LCM can nest type definitions.
"""

import re
from dataclasses import dataclass, field as dc_field
from typing import List, Optional

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

F = descriptor_pb2.FieldDescriptorProto

UNITS_EXTENSION = "openocean.field"

# Seconds per unit for "<unit> since 1970-01-01 00:00:00 UTC"
_EPOCH_UNITS = {
    "seconds": 1, "s": 1,
    "milliseconds": 1e-3, "ms": 1e-3,
    "microseconds": 1e-6, "us": 1e-6,
    "nanoseconds": 1e-9, "ns": 1e-9,
}
_EPOCH = re.compile(r"^(\w+) since 1970-01-01(?:[ T]00:00(?::00)?)?(?: ?(?:UTC|Z))?$")

# SourceCodeInfo path components (field numbers in descriptor.proto)
_FILE_MESSAGE, _FILE_ENUM = 4, 5
_MESSAGE_FIELD, _MESSAGE_NESTED, _MESSAGE_ENUM, _MESSAGE_ONEOF = 2, 3, 4, 8
_ENUM_VALUE = 2


class GeneratorError(Exception):
    pass


@dataclass
class Comments:
    leading: List[str] = dc_field(default_factory=list)
    trailing: List[str] = dc_field(default_factory=list)


@dataclass
class Field:
    name: str
    number: int
    type: int  # FieldDescriptorProto.Type
    type_name: str  # fully qualified, with leading '.', for messages and enums
    repeated: bool
    has_presence: bool
    oneof: Optional[str]
    units: str
    units_field: str
    # Seconds per unit when this is a UNIX-epoch timestamp, else None
    epoch_scale: Optional[float]
    comments: Comments


@dataclass
class Oneof:
    name: str
    fields: List[Field]
    comments: Comments


@dataclass
class EnumValue:
    name: str
    number: int
    comments: Comments


@dataclass
class Enum:
    full_name: str
    flat_name: str
    proto_name: str
    file: str
    values: List[EnumValue]
    comments: Comments


@dataclass
class Message:
    full_name: str
    flat_name: str
    file: str
    fields: List[Field]
    oneofs: List[Oneof]
    comments: Comments


@dataclass
class Model:
    messages: List[Message]
    enums: List[Enum]
    # Every type in the request (including imports), by fully qualified name
    all_types: dict


def _comments(locations, path):
    loc = locations.get(tuple(path))
    if loc is None:
        return Comments()

    def lines(text):
        return [line[1:] if line.startswith(" ") else line
                for line in text.rstrip("\n").split("\n")] if text else []

    return Comments(lines(loc.leading_comments), lines(loc.trailing_comments))


def _field_options_reader(request):
    """Parses FieldOptions with the request's own descriptors, so extensions
    resolve without the options' generated Python code."""
    files = [f.name for f in request.proto_file]
    if "google/protobuf/descriptor.proto" not in files:
        return lambda options: ("", "")
    pool = descriptor_pool.DescriptorPool()
    for f in request.proto_file:
        pool.AddSerializedFile(f.SerializeToString())
    if hasattr(message_factory, "GetMessageClassesForFiles"):
        classes = message_factory.GetMessageClassesForFiles(files, pool)
    else:
        classes = message_factory.MessageFactory(pool).GetMessages(files)
    options_class = classes["google.protobuf.FieldOptions"]
    try:
        extension = pool.FindExtensionByName(UNITS_EXTENSION)
    except KeyError:
        return lambda options: ("", "")

    def read(options):
        parsed = options_class.FromString(options.SerializeToString())
        value = parsed.Extensions[extension]
        return value.units, value.units_field

    return read


def _is_options_file(file):
    return file.extension and all(
        e.extendee.startswith(".google.protobuf.") and e.extendee.endswith("Options")
        for e in file.extension)


def _epoch_scale(units):
    match = _EPOCH.match(units)
    return _EPOCH_UNITS.get(match.group(1)) if match else None


def build(request):
    """Builds the model for request.file_to_generate.

    Files that only extend google.protobuf.*Options (e.g. options.proto) define
    metadata, not data, and are skipped.
    """
    read_options = _field_options_reader(request)
    to_generate = set(request.file_to_generate)

    all_types = {}
    for file in request.proto_file:
        prefix = "." + file.package if file.package else ""

        def index(messages, enums, scope):
            for m in messages:
                all_types[f"{scope}.{m.name}"] = (file, m)
                index(m.nested_type, m.enum_type, f"{scope}.{m.name}")
            for e in enums:
                all_types[f"{scope}.{e.name}"] = (file, e)

        index(file.message_type, file.enum_type, prefix)

    messages, enums = [], []
    for file in request.proto_file:
        if file.name not in to_generate or _is_options_file(file):
            continue
        locations = {tuple(loc.path): loc for loc in file.source_code_info.location}
        proto3 = file.syntax == "proto3"
        prefix = "." + file.package if file.package else ""

        def add_enum(e, scope, flat_scope, path):
            enums.append(Enum(
                full_name=f"{scope}.{e.name}",
                flat_name=flat_scope + e.name,
                proto_name=e.name,
                file=file.name,
                values=[EnumValue(v.name, v.number,
                                  _comments(locations, path + [_ENUM_VALUE, i]))
                        for i, v in enumerate(e.value)],
                comments=_comments(locations, path)))

        def add_message(m, scope, flat_scope, path):
            full_name = f"{scope}.{m.name}"
            flat_name = flat_scope + m.name
            real_oneofs = {}
            fields = []
            for i, f in enumerate(m.field):
                in_real_oneof = f.HasField("oneof_index") and not f.proto3_optional
                repeated = f.label == F.LABEL_REPEATED
                if repeated or in_real_oneof:
                    has_presence = False
                elif f.proto3_optional or f.type == F.TYPE_MESSAGE:
                    has_presence = True
                else:
                    has_presence = not proto3 and f.label == F.LABEL_OPTIONAL
                units, units_field = read_options(f.options)
                fld = Field(
                    name=f.name, number=f.number, type=f.type, type_name=f.type_name,
                    repeated=repeated, has_presence=has_presence,
                    oneof=m.oneof_decl[f.oneof_index].name if in_real_oneof else None,
                    units=units, units_field=units_field,
                    epoch_scale=_epoch_scale(units),
                    comments=_comments(locations, path + [_MESSAGE_FIELD, i]))
                fields.append(fld)
                if in_real_oneof:
                    real_oneofs.setdefault(f.oneof_index, []).append(fld)
            oneofs = [Oneof(m.oneof_decl[i].name, members,
                            _comments(locations, path + [_MESSAGE_ONEOF, i]))
                      for i, members in sorted(real_oneofs.items())]
            messages.append(Message(full_name, flat_name, file.name, fields, oneofs,
                                    _comments(locations, path)))
            for j, nested in enumerate(m.nested_type):
                add_message(nested, full_name, flat_name, path + [_MESSAGE_NESTED, j])
            for j, e in enumerate(m.enum_type):
                add_enum(e, full_name, flat_name, path + [_MESSAGE_ENUM, j])

        for i, m in enumerate(file.message_type):
            add_message(m, prefix, "", [_FILE_MESSAGE, i])
        for i, e in enumerate(file.enum_type):
            add_enum(e, prefix, "", [_FILE_ENUM, i])

    seen = {}
    for t in messages + enums:
        if t.flat_name in seen:
            raise GeneratorError(
                f"{t.full_name} and {seen[t.flat_name]} both flatten to {t.flat_name}")
        seen[t.flat_name] = t.full_name

    return Model(messages, enums, all_types)


def upper_snake(camel):
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", camel)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).upper()


def parse_parameters(parameter):
    params = {}
    for item in filter(None, parameter.split(",")):
        key, sep, value = item.partition("=")
        if not sep:
            raise GeneratorError(f"parameter '{item}' is not key=value")
        params[key.strip()] = value.strip()
    return params
