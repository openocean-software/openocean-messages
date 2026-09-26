"""Renders a Model as a ROS 2 interface package (msg/*.msg, package.xml, CMakeLists.txt)."""

import keyword
import re
from xml.sax.saxutils import escape

from .model import F, GeneratorError, upper_snake

_SCALARS = {
    F.TYPE_DOUBLE: "float64",
    F.TYPE_FLOAT: "float32",
    F.TYPE_INT64: "int64",
    F.TYPE_SINT64: "int64",
    F.TYPE_SFIXED64: "int64",
    F.TYPE_UINT64: "uint64",
    F.TYPE_FIXED64: "uint64",
    F.TYPE_INT32: "int32",
    F.TYPE_SINT32: "int32",
    F.TYPE_SFIXED32: "int32",
    F.TYPE_UINT32: "uint32",
    F.TYPE_FIXED32: "uint32",
    F.TYPE_BOOL: "bool",
    F.TYPE_STRING: "string",
}
_NUMERIC = set(_SCALARS) - {F.TYPE_BOOL, F.TYPE_STRING}

_WELL_KNOWN = {
    ".google.protobuf.Timestamp": "builtin_interfaces/Time",
    ".google.protobuf.Duration": "builtin_interfaces/Duration",
}
_TIME = "builtin_interfaces/Time"

# From rosidl_adapter.parser
_PACKAGE_NAME = re.compile(r"^(?!.*__)(?!.*_$)[a-z][a-z0-9_]*$")
_FIELD_NAME = _PACKAGE_NAME
_MESSAGE_NAME = re.compile(r"^[A-Z][A-Za-z0-9]*$")
_CONSTANT_NAME = re.compile(r"^[A-Z]([A-Z0-9_]?[A-Z0-9]+)*$")

_CPP_KEYWORDS = set("""
alignas alignof and and_eq asm auto bitand bitor bool break case catch char char8_t char16_t
char32_t class compl concept const consteval constexpr constinit const_cast continue co_await
co_return co_yield decltype default delete do double dynamic_cast else enum explicit export
extern false float for friend goto if inline int long mutable namespace new noexcept not not_eq
nullptr operator or or_eq private protected public register reinterpret_cast requires return
short signed sizeof static static_assert static_cast struct switch template this thread_local
throw true try typedef typeid typename union unsigned using virtual void volatile wchar_t while
xor xor_eq
""".split())


def _comment_lines(lines):
    return [f"# {line}" if line else "#" for line in lines]


def _check_field_name(owner, name):
    if not _FIELD_NAME.match(name):
        raise GeneratorError(f"{owner}.{name}: not a valid ROS 2 field name")
    if keyword.iskeyword(name) or name in _CPP_KEYWORDS:
        raise GeneratorError(
            f"{owner}.{name}: is a Python or C++ keyword, which ROS 2 can't generate")


def _check_constant_name(owner, name):
    if not _CONSTANT_NAME.match(name):
        raise GeneratorError(f"{owner}.{name}: not a valid ROS 2 constant name")


def _smallest(values, unsigned_type, signed_type):
    return unsigned_type if all(0 <= v <= 255 for v in values) else signed_type


class _Package:
    def __init__(self, model, params):
        self.model = model
        self.name = params["package"]
        if not _PACKAGE_NAME.match(self.name):
            raise GeneratorError(f"'{self.name}' is not a valid ROS 2 package name")
        self.params = params
        self.local = {t.full_name: t.flat_name for t in model.messages + model.enums}
        self.dependencies = set()

    def type_of(self, owner, f):
        if f.type in _NUMERIC and f.epoch_scale is not None:
            base = _TIME
        elif f.type in _SCALARS:
            base = _SCALARS[f.type]
        elif f.type == F.TYPE_BYTES:
            if f.repeated:
                raise GeneratorError(f"{owner}.{f.name}: repeated bytes has no ROS 2 equivalent")
            return "uint8[]"
        elif f.type_name in self.local:
            base = self.local[f.type_name]
        elif f.type_name in _WELL_KNOWN:
            base = _WELL_KNOWN[f.type_name]
        else:
            raise GeneratorError(
                f"{owner}.{f.name}: type {f.type_name[1:]} is not in the files being generated")
        if "/" in base:
            self.dependencies.add(base.split("/")[0])
        return base + "[]" if f.repeated else base

    def trailing(self, f):
        parts = []
        if f.epoch_scale is None:
            if f.units:
                parts.append(f"[{f.units}]")
            elif f.units_field:
                parts.append(f"[units given by '{f.units_field}']")
        parts += f.comments.trailing
        return "  # " + " ".join(parts) if parts else ""

    def header(self, t, comments):
        lines = [f"# Generated from {t.full_name[1:]} ({t.file})"]
        if comments.leading:
            lines += ["#"] + _comment_lines(comments.leading)
        return lines + [""]

    def render_message(self, m):
        if not _MESSAGE_NAME.match(m.flat_name):
            raise GeneratorError(f"{m.full_name}: {m.flat_name} is not a valid ROS 2 message name")
        owner = m.full_name[1:]
        out = self.header(m, m.comments)
        names = set()

        def declare(name):
            _check_field_name(owner, name)
            if name in names:
                raise GeneratorError(f"{owner}: more than one ROS 2 field named {name}")
            names.add(name)

        def gap():
            if out[-1] != "":
                out.append("")

        oneof_starts = {o.fields[0].name: o for o in m.oneofs}
        for f in m.fields:
            if f.name in oneof_starts:
                o = oneof_starts[f.name]
                case = f"{o.name}_case"
                declare(case)
                gap()
                out += _comment_lines(o.comments.leading)
                prefix = o.name.upper()
                ctype = _smallest([x.number for x in o.fields], "uint8", "uint32")
                constants = [(f"{prefix}_NOT_SET", 0)] + [
                    (f"{prefix}_{x.name.upper()}", x.number) for x in o.fields]
                for cname, number in constants:
                    _check_constant_name(owner, cname)
                    out.append(f"{ctype} {cname}={number}")
                out.append(f"{ctype} {case}")
            if f.comments.leading:
                gap()
                out += _comment_lines(f.comments.leading)
            if f.has_presence:
                declare(f"has_{f.name}")
                out.append(f"bool has_{f.name}")
            declare(f.name)
            out.append(f"{self.type_of(owner, f)} {f.name}{self.trailing(f)}")
        return "\n".join(out) + "\n"

    def render_enum(self, e):
        if not _MESSAGE_NAME.match(e.flat_name):
            raise GeneratorError(f"{e.full_name}: {e.flat_name} is not a valid ROS 2 message name")
        owner = e.full_name[1:]
        out = self.header(e, e.comments)
        prefix = upper_snake(e.proto_name) + "_"
        stripped = [v.name[len(prefix):] for v in e.values if v.name.startswith(prefix)]
        strip = len(stripped) == len(e.values) and all(_CONSTANT_NAME.match(s) for s in stripped)
        vtype = _smallest([v.number for v in e.values], "uint8", "int32")
        for v in e.values:
            name = v.name[len(prefix):] if strip else v.name
            _check_constant_name(owner, name)
            if v.comments.leading:
                out += _comment_lines(v.comments.leading)
            trailing = "  # " + " ".join(v.comments.trailing) if v.comments.trailing else ""
            out.append(f"{vtype} {name}={v.number}{trailing}")
        out += ["", f"{vtype} value"]
        return "\n".join(out) + "\n"

    def package_xml(self):
        p = {k: escape(v) for k, v in self.params.items()}
        depends = "".join(f"  <depend>{d}</depend>\n" for d in sorted(self.dependencies))
        if depends:
            depends += "\n"
        return f"""<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>{p['package']}</name>
  <version>{p.get('version', '0.0.0')}</version>
  <description>{p.get('description', 'Messages generated from Protobuf by protoc-gen-ros')}</description>
  <maintainer email="{p['maintainer_email']}">{p['maintainer']}</maintainer>
  <license>{p['license']}</license>

  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>

{depends}  <exec_depend>rosidl_default_runtime</exec_depend>

  <member_of_group>rosidl_interface_packages</member_of_group>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
"""

    def cmake_lists(self, msg_files):
        finds = "".join(f"find_package({d} REQUIRED)\n" for d in sorted(self.dependencies))
        files = "".join(f'  "{f}"\n' for f in msg_files)
        deps = (f"  DEPENDENCIES {' '.join(sorted(self.dependencies))}\n"
                if self.dependencies else "")
        return f"""cmake_minimum_required(VERSION 3.8)
project({self.name})

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
{finds}
rosidl_generate_interfaces(${{PROJECT_NAME}}
{files}{deps})

ament_export_dependencies(rosidl_default_runtime)
ament_package()
"""


def generate(model, params):
    """Returns {path: content} for the ROS 2 package."""
    for required in ("package", "maintainer", "maintainer_email", "license"):
        if required not in params:
            raise GeneratorError(f"missing plugin parameter '{required}'")
    package = _Package(model, params)
    files = {}
    for m in model.messages:
        files[f"msg/{m.flat_name}.msg"] = package.render_message(m)
    for e in model.enums:
        files[f"msg/{e.flat_name}.msg"] = package.render_enum(e)
    if not files:
        raise GeneratorError("no messages or enums to generate")
    msg_files = sorted(files)
    files["package.xml"] = package.package_xml()
    files["CMakeLists.txt"] = package.cmake_lists(msg_files)
    return files
