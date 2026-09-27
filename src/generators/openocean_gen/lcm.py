"""Renders a Model as LCM types (*.lcm) and, optionally, a C++ header that converts between
them and the Protobuf C++ types."""

import keyword
import re

from .model import CPP_KEYWORDS, F, GeneratorError, dependency, enum_value_names, upper_snake

# LCM has no unsigned types (other than byte), so these widen or range-check
_SCALARS = {
    F.TYPE_DOUBLE: "double",
    F.TYPE_FLOAT: "float",
    F.TYPE_INT64: "int64_t",
    F.TYPE_SINT64: "int64_t",
    F.TYPE_SFIXED64: "int64_t",
    F.TYPE_UINT64: "int64_t",
    F.TYPE_FIXED64: "int64_t",
    F.TYPE_INT32: "int32_t",
    F.TYPE_SINT32: "int32_t",
    F.TYPE_SFIXED32: "int32_t",
    F.TYPE_UINT32: "int64_t",
    F.TYPE_FIXED32: "int64_t",
    F.TYPE_BOOL: "boolean",
    F.TYPE_STRING: "string",
}
_UINT32 = {F.TYPE_UINT32, F.TYPE_FIXED32}
_UINT64 = {F.TYPE_UINT64, F.TYPE_FIXED64}

# LCM's convention for time is int64_t microseconds
_WELL_KNOWN = {
    ".google.protobuf.Timestamp": ("microseconds since 1970-01-01 00:00:00 UTC",
                                   "google/protobuf/timestamp.pb.h", "from_micros_timestamp"),
    ".google.protobuf.Duration": ("microseconds", "google/protobuf/duration.pb.h",
                                  "from_micros_duration"),
}

_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_LCM_RESERVED = set("""
package struct const enum boolean byte int8_t int16_t int32_t int64_t float double string
encode decode getEncodedSize getHash getTypeName
""".split())


def lcm_name(flat_name):
    return upper_snake(flat_name).lower() + "_t"


def _check_name(owner, name, what):
    if not _IDENTIFIER.match(name):
        raise GeneratorError(f"{owner}.{name}: not a valid LCM {what} name")
    if keyword.iskeyword(name) or name in CPP_KEYWORDS or name in _LCM_RESERVED:
        raise GeneratorError(
            f"{owner}.{name}: is reserved in LCM or its Python or C++ output")


def _comment_lines(lines, indent=""):
    return [f"{indent}// {line}" if line else f"{indent}//" for line in lines]


def _namespace(package):
    return "::" + package.replace(".", "::") if package else ""


class _Kind:
    """How one proto value (a field, repeated element, or map key/value) converts.

    Value kinds convert with expressions (to_value, from_value); message-like kinds
    (messages and well-known types) convert into a proto pointer (from_into)."""

    def __init__(self, lcm_type, to_stmt, from_value=None, from_into=None, units=None,
                 includes=()):
        self.lcm_type = lcm_type
        self.to_stmt = to_stmt
        self.from_value = from_value
        self.from_into = from_into
        self.units = units
        self.includes = includes

    @property
    def message_like(self):
        return self.from_into is not None


class _Package:
    def __init__(self, model, params):
        packages = {t.package for t in model.messages + model.enums}
        if len(packages) != 1:
            raise GeneratorError(f"expected one proto package, found {sorted(packages)}")
        self.package = packages.pop()
        self.namespace = _namespace(self.package)
        self.types = {t.full_name: t for t in model.messages + model.enums}
        self.imported = model.imported
        self.deps = params["dep"]
        self.includes = set()
        self.dep_headers = set()

    def proto_cpp(self, t):
        relative = t.full_name[len(t.package) + 2:] if t.package else t.full_name[1:]
        return f"{_namespace(t.package)}::{relative.replace('.', '_')}"

    def lcm_cpp(self, t):
        return f"{_namespace(t.package)}::{lcm_name(t.flat_name)}"

    def lcm_type(self, t):
        """How a field names type t: bare in this package, qualified from another."""
        name = lcm_name(t.flat_name)
        return name if t.package == self.package else f"{t.package}.{name}"

    def kind(self, owner, f):
        name = f'"{owner}.{f.name}"'
        if f.type in _SCALARS:
            to_value, from_value = "{}", "{}"
            if f.type in _UINT32:
                from_value = f"lcm_detail::to_uint32({{}}, {name})"
            elif f.type in _UINT64:
                to_value = f"lcm_detail::to_int64({{}}, {name})"
                from_value = f"lcm_detail::to_uint64({{}}, {name})"
            elif f.type == F.TYPE_BOOL:
                from_value = "({} != 0)"
            return _Kind(_SCALARS[f.type],
                         lambda src, dst: f"{dst} = {to_value.format(src)};",
                         from_value=from_value.format)
        if f.type_name in _WELL_KNOWN:
            units, include, from_micros = _WELL_KNOWN[f.type_name]
            return _Kind("int64_t",
                         lambda src, dst: f"{dst} = lcm_detail::to_micros({src});",
                         from_into=lambda src, ptr: f"lcm_detail::{from_micros}({src}, {ptr});",
                         units=units, includes=(include,))
        t = self.types.get(f.type_name) or self.imported.get(f.type_name)
        if t is None or (f.type_name in self.imported and not dependency(t.file, self.deps)):
            raise GeneratorError(
                f"{owner}.{f.name}: type {f.type_name[1:]} is not in the files being generated, "
                "or a dep=<proto path prefix>=<converter header> parameter")
        if f.type_name in self.imported:
            # Its conversions come from the dependency's converter header
            self.dep_headers.add(dependency(t.file, self.deps))
        if f.type == F.TYPE_ENUM:
            enum = self.proto_cpp(t)
            return _Kind(self.lcm_type(t),
                         lambda src, dst: f"{dst}.value = static_cast<int32_t>({src});",
                         from_value=lambda src: f"static_cast<{enum}>({src}.value)")
        return _Kind(self.lcm_type(t),
                     lambda src, dst: f"to_lcm({src}, &{dst});",
                     from_into=lambda src, ptr: f"from_lcm({src}, {ptr});")

    def field_units(self, f, kind):
        if kind is not None and kind.units:
            return kind.units
        if f.units:
            return f.units
        if f.units_field:
            return f"units given by '{f.units_field}'"
        return None

    def render(self, m):
        """Returns the .lcm text, and the to_lcm and from_lcm bodies, for message m."""
        owner = m.full_name[1:]
        lcm = [f"// Generated from {owner} ({m.file})"]
        if m.comments.leading:
            lcm += ["//"] + _comment_lines(m.comments.leading)
        lcm += ["", f"package {self.package};", "", f"struct {lcm_name(m.flat_name)}", "{"]
        to, frm = [], []
        names = set()

        def declare(name):
            _check_name(owner, name, "field")
            if name in names:
                raise GeneratorError(f"{owner}: more than one LCM field named {name}")
            names.add(name)

        def gap():
            if lcm[-1] not in ("{", ""):
                lcm.append("")

        oneof_starts = {o.fields[0].name: o for o in m.oneofs}
        for f in m.fields:
            if f.name in oneof_starts:
                o = oneof_starts[f.name]
                case = f"{o.name}_case"
                declare(case)
                gap()
                lcm += _comment_lines(o.comments.leading, "    ")
                prefix = o.name.upper()
                for cname, number in [(f"{prefix}_NOT_SET", 0)] + [
                        (f"{prefix}_{x.name.upper()}", x.number) for x in o.fields]:
                    _check_name(owner, cname, "constant")
                    lcm.append(f"    const int32_t {cname} = {number};")
                lcm.append(f"    int32_t {case};")
                to.append(f"out->{case} = static_cast<int32_t>(in.{o.name}_case());")
                frm.append(f"switch (in.{case})")
                frm.append("{")
                for x in o.fields:
                    frm.append(f"    case {x.number}:")
                    frm += ["        " + s for s in self.set_singular(owner, x)]
                    frm.append("        break;")
                frm += ["    default:", "        break;", "}"]

            if f.comments.leading:
                gap()
                lcm += _comment_lines(f.comments.leading, "    ")
            if f.has_presence:
                declare(f"has_{f.name}")
                lcm.append(f"    boolean has_{f.name};")
                to.append(f"out->has_{f.name} = in.has_{f.name}();")
            lcm_lines, to_lines, from_lines = self.render_field(owner, f, declare)
            lcm += lcm_lines
            to += to_lines
            if f.oneof is None:
                if f.has_presence:
                    frm.append(f"if (in.has_{f.name})")
                    frm += ["    " + s for s in from_lines]
                else:
                    frm += from_lines
        lcm.append("}")
        return "\n".join(lcm) + "\n", to, frm

    def trailing(self, f, kind):
        parts = []
        units = self.field_units(f, kind)
        if units:
            parts.append(f"[{units}]")
        parts += f.comments.trailing
        return "  // " + " ".join(parts) if parts else ""

    def render_field(self, owner, f, declare):
        """Returns (lcm lines, to_lcm statements, from_lcm statements) for field f."""
        name = f'"{owner}.{f.name}"'
        count = f"num_{f.name}"
        if f.type == F.TYPE_BYTES:
            if f.repeated:
                raise GeneratorError(f"{owner}.{f.name}: repeated bytes has no LCM equivalent")
            declare(count)
            declare(f.name)
            return ([f"    int32_t {count};", f"    byte {f.name}[{count}];{self.trailing(f, None)}"],
                    [f"out->{f.name}.assign(in.{f.name}().begin(), in.{f.name}().end());",
                     f"out->{count} = lcm_detail::to_count(out->{f.name}.size(), {name});"],
                    self.set_singular(owner, f))

        entry = self.types.get(f.type_name)
        if f.repeated and getattr(entry, "map_entry", False):
            key, value = entry.fields
            key_kind, value_kind = self.kind(owner, key), self.kind(owner, value)
            self.includes.update(key_kind.includes + value_kind.includes)
            declare(count)
            declare(f.name)
            entry_type = lcm_name(entry.flat_name)
            to = [f"for (const auto* kv : lcm_detail::sorted(in.{f.name}()))",
                  "{",
                  f"    out->{f.name}.emplace_back();",
                  f"    {key_kind.to_stmt('kv->first', f'out->{f.name}.back().key')}",
                  f"    {value_kind.to_stmt('kv->second', f'out->{f.name}.back().value')}",
                  "}",
                  f"out->{count} = lcm_detail::to_count(out->{f.name}.size(), {name});"]
            k = key_kind.from_value("e.key")
            if value_kind.message_like:
                set_value = value_kind.from_into("e.value", f"&(*out->mutable_{f.name}())[{k}]")
            else:
                set_value = f"(*out->mutable_{f.name}())[{k}] = {value_kind.from_value('e.value')};"
            frm = [f"lcm_detail::check_count(in.{count}, in.{f.name}.size(), {name});",
                   f"for (const auto& e : in.{f.name})",
                   f"    {set_value}"]
            return ([f"    int32_t {count};",
                     f"    {entry_type} {f.name}[{count}];{self.trailing(f, None)}"], to, frm)

        kind = self.kind(owner, f)
        self.includes.update(kind.includes)
        if f.repeated:
            declare(count)
            declare(f.name)
            to = [f"for (const auto& e : in.{f.name}())",
                  "{",
                  f"    out->{f.name}.emplace_back();",
                  f"    {kind.to_stmt('e', f'out->{f.name}.back()')}",
                  "}",
                  f"out->{count} = lcm_detail::to_count(out->{f.name}.size(), {name});"]
            if kind.message_like:
                add = kind.from_into("e", f"out->add_{f.name}()")
            else:
                add = f"out->add_{f.name}({kind.from_value('e')});"
            frm = [f"lcm_detail::check_count(in.{count}, in.{f.name}.size(), {name});",
                   f"for (const auto& e : in.{f.name})",
                   f"    {add}"]
            return ([f"    int32_t {count};",
                     f"    {kind.lcm_type} {f.name}[{count}];{self.trailing(f, kind)}"], to, frm)

        declare(f.name)
        return ([f"    {kind.lcm_type} {f.name};{self.trailing(f, kind)}"],
                [kind.to_stmt(f"in.{f.name}()", f"out->{f.name}")],
                self.set_singular(owner, f))

    def set_singular(self, owner, f):
        """from_lcm statements that set singular field f from in.<f>."""
        src = f"in.{f.name}"
        if f.type == F.TYPE_BYTES:
            return [f'lcm_detail::check_count(in.num_{f.name}, {src}.size(), "{owner}.{f.name}");',
                    f"out->set_{f.name}(std::string({src}.begin(), {src}.end()));"]
        kind = self.kind(owner, f)
        if kind.message_like:
            return [kind.from_into(src, f"out->mutable_{f.name}()")]
        return [f"out->set_{f.name}({kind.from_value(src)});"]

    def render_enum(self, e):
        owner = e.full_name[1:]
        lcm = [f"// Generated from {owner} ({e.file})"]
        if e.comments.leading:
            lcm += ["//"] + _comment_lines(e.comments.leading)
        lcm += ["", f"package {self.package};", "", f"struct {lcm_name(e.flat_name)}", "{"]
        for v, name in zip(e.values, enum_value_names(e, _IDENTIFIER)):
            _check_name(owner, name, "constant")
            lcm += _comment_lines(v.comments.leading, "    ")
            trailing = "  // " + " ".join(v.comments.trailing) if v.comments.trailing else ""
            lcm.append(f"    const int32_t {name} = {v.number};{trailing}")
        lcm += ["", "    int32_t value;", "}"]
        return "\n".join(lcm) + "\n"

    def converter(self, messages, bodies):
        lcm_headers = [f"{self.package.replace('.', '/')}/{lcm_name(m.flat_name)}.hpp"
                       for m in messages]
        proto_headers = sorted({m.file[:-len(".proto")] + ".pb.h" for m in messages} |
                               self.includes)
        out = [f"// Generated by protoc-gen-lcm: converts between the {self.package} Protobuf",
               "// and LCM C++ types.",
               "#pragma once",
               "",
               "#include <algorithm>",
               "#include <cstddef>",
               "#include <cstdint>",
               "#include <limits>",
               "#include <stdexcept>",
               "#include <string>",
               "#include <vector>",
               ""]
        out += [f'#include "{h}"' for h in proto_headers]
        out.append("")
        out += [f'#include "{h}"' for h in sorted(lcm_headers)]
        if self.dep_headers:
            out.append("")
            out += [f'#include "{h}"' for h in sorted(self.dep_headers)]
        out += ["", f"namespace {self.package.replace('.', '::')}", "{", _DETAIL, ""]
        signatures = []
        for m in messages:
            proto, lcm = self.proto_cpp(m), self.lcm_cpp(m)
            signatures.append((f"inline void to_lcm(const {proto}& in, {lcm}* out)",
                               f"inline void from_lcm(const {lcm}& in, {proto}* out)"))
        for to_sig, from_sig in signatures:
            out += [to_sig + ";", from_sig + ";"]
        for m, (to_sig, from_sig) in zip(messages, signatures):
            to, frm = bodies[m.full_name]
            out += ["", to_sig, "{", f"    *out = {self.lcm_cpp(m)}();"]
            out += ["    " + s for s in to] if to else ["    (void)in;"]
            out += ["}", "", from_sig, "{", "    out->Clear();"]
            out += ["    " + s for s in frm] if frm else ["    (void)in;"]
            out.append("}")
        out += ["", f"}} // namespace {self.package.replace('.', '::')}", ""]
        return "\n".join(out)


_DETAIL = """namespace lcm_detail
{
inline int64_t to_int64(uint64_t value, const char* field)
{
    if (value > static_cast<uint64_t>(std::numeric_limits<int64_t>::max()))
        throw std::out_of_range(std::string(field) + " does not fit in an LCM int64_t");
    return static_cast<int64_t>(value);
}

inline uint64_t to_uint64(int64_t value, const char* field)
{
    if (value < 0)
        throw std::out_of_range(std::string(field) + " is negative");
    return static_cast<uint64_t>(value);
}

inline uint32_t to_uint32(int64_t value, const char* field)
{
    if (value < 0 || value > std::numeric_limits<uint32_t>::max())
        throw std::out_of_range(std::string(field) + " does not fit in a uint32");
    return static_cast<uint32_t>(value);
}

inline int32_t to_count(std::size_t size, const char* field)
{
    if (size > static_cast<std::size_t>(std::numeric_limits<int32_t>::max()))
        throw std::out_of_range(std::string(field) + " has too many elements for LCM");
    return static_cast<int32_t>(size);
}

inline void check_count(int32_t count, std::size_t size, const char* field)
{
    if (count < 0 || static_cast<std::size_t>(count) != size)
        throw std::invalid_argument(std::string(field) + " count does not match its size");
}

// Truncates to whole microseconds
template <typename T> int64_t to_micros(const T& t)
{
    return t.seconds() * 1000000 + t.nanos() / 1000;
}

// Timestamp nanos are always non-negative
template <typename T> void from_micros_timestamp(int64_t micros, T* t)
{
    int64_t seconds = micros / 1000000, remainder = micros % 1000000;
    if (remainder < 0)
    {
        remainder += 1000000;
        --seconds;
    }
    t->set_seconds(seconds);
    t->set_nanos(static_cast<int32_t>(remainder * 1000));
}

// Duration nanos have the sign of the seconds
template <typename T> void from_micros_duration(int64_t micros, T* t)
{
    t->set_seconds(micros / 1000000);
    t->set_nanos(static_cast<int32_t>(micros % 1000000 * 1000));
}

// Map iteration order is unspecified, so sort for a deterministic LCM encoding
template <typename Map> std::vector<const typename Map::value_type*> sorted(const Map& map)
{
    std::vector<const typename Map::value_type*> entries;
    for (const auto& kv : map) entries.push_back(&kv);
    std::sort(entries.begin(), entries.end(),
              [](const auto* a, const auto* b) { return a->first < b->first; });
    return entries;
}
} // namespace lcm_detail"""


def generate(model, params):
    """Returns {path: content}: one .lcm file per type, and with the header parameter, the
    converter header at that path."""
    package = _Package(model, params)
    files, bodies = {}, {}
    for m in model.messages:
        if not _IDENTIFIER.match(lcm_name(m.flat_name)):
            raise GeneratorError(f"{m.full_name}: {lcm_name(m.flat_name)} is not a valid LCM name")
        text, to, frm = package.render(m)
        files[f"{lcm_name(m.flat_name)}.lcm"] = text
        bodies[m.full_name] = (to, frm)
    for e in model.enums:
        if not _IDENTIFIER.match(lcm_name(e.flat_name)):
            raise GeneratorError(f"{e.full_name}: {lcm_name(e.flat_name)} is not a valid LCM name")
        files[f"{lcm_name(e.flat_name)}.lcm"] = package.render_enum(e)
    if not files:
        raise GeneratorError("no messages or enums to generate")
    if "header" in params:
        # Map entries convert inline, through the Protobuf Map API
        converted = [m for m in model.messages if not m.map_entry]
        files[params["header"]] = package.converter(converted, bodies)
    return files
