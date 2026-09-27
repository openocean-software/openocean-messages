"""Renders a ROS 2 package with the Protobuf C++ library and a header that converts between
it and the ROS 2 C++ types that ros.py describes."""

import re
from xml.sax.saxutils import escape

from .model import F, GeneratorError, dependency
from .ros import _NUMERIC, _PACKAGE_NAME, _SCALARS, _smallest

_WELL_KNOWN = {
    ".google.protobuf.Timestamp": ("time", "google/protobuf/timestamp.pb.h"),
    ".google.protobuf.Duration": ("duration", "google/protobuf/duration.pb.h"),
}
_FLOATS = {F.TYPE_DOUBLE, F.TYPE_FLOAT}
_CPP_INTEGERS = {
    F.TYPE_INT64: "int64_t", F.TYPE_SINT64: "int64_t", F.TYPE_SFIXED64: "int64_t",
    F.TYPE_UINT64: "uint64_t", F.TYPE_FIXED64: "uint64_t",
    F.TYPE_INT32: "int32_t", F.TYPE_SINT32: "int32_t", F.TYPE_SFIXED32: "int32_t",
    F.TYPE_UINT32: "uint32_t", F.TYPE_FIXED32: "uint32_t",
}
_ROS_CPP_SCALARS = {"uint8": "uint8_t", "int32": "int32_t", "uint32": "uint32_t"}


def ros_header_name(message_name):
    """rosidl's convert_camel_case_to_lower_case_underscore."""
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", message_name)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.lower()


class _Kind:
    """How one proto value converts: value kinds with expressions (from_value), and
    message-like kinds (messages and well-known types) into a proto pointer (from_into)."""

    def __init__(self, to_stmt, from_value=None, from_into=None):
        self.to_stmt = to_stmt
        self.from_value = from_value
        self.from_into = from_into


class _Converter:
    def __init__(self, model, params):
        self.name = params["convert_package"]
        if not _PACKAGE_NAME.match(self.name):
            raise GeneratorError(f"'{self.name}' is not a valid ROS 2 package name")
        self.ros_package = params["package"]
        self.params = params
        packages = {t.package for t in model.messages + model.enums}
        if len(packages) != 1:
            raise GeneratorError(f"expected one proto package, found {sorted(packages)}")
        self.package = packages.pop()
        self.types = {t.full_name: t for t in model.messages + model.enums}
        self.imported = model.imported
        self.deps = params["dep"]
        # Protos another converter package provides are linked from it, not compiled again
        provided = {f: dependency(f, self.deps) for f in model.proto_files
                    if f not in model.generated_files}
        self.proto_files = [f for f in model.proto_files if not provided.get(f)]
        self.convert_deps = sorted({f"{package}_convert" for package in provided.values() if package})
        self.includes = set()
        self.ros_includes = set()

    def proto_cpp(self, t):
        relative = t.full_name[len(t.package) + 2:] if t.package else t.full_name[1:]
        return f"::{t.package.replace('.', '::')}::{relative.replace('.', '_')}"

    def ros_cpp(self, t):
        package = self.ros_package if t.full_name in self.types else dependency(t.file, self.deps)
        return f"::{package}::msg::{t.flat_name}"

    def kind(self, owner, f):
        name = f'"{owner}.{f.name}"'
        if f.type in _NUMERIC and f.epoch_scale is not None:
            self.ros_includes.add("builtin_interfaces/msg/time.hpp")
            if f.type in _FLOATS:
                return _Kind(lambda src, dst: f"{dst} = ros_detail::to_time_seconds({src}, {name});",
                             from_value=lambda src: f"ros_detail::from_time_seconds({src})")
            units_per_second = round(1 / f.epoch_scale)
            cpp = _CPP_INTEGERS[f.type]
            return _Kind(
                lambda src, dst: f"{dst} = ros_detail::to_time({src}, {units_per_second}, {name});",
                from_value=lambda src: f"ros_detail::from_time<{cpp}>({src}, {units_per_second}, {name})")
        if f.type in _SCALARS:
            return _Kind(lambda src, dst: f"{dst} = {src};", from_value=lambda src: src)
        if f.type == F.TYPE_BYTES:
            return _Kind(lambda src, dst: f"{dst}.assign({src}.begin(), {src}.end());",
                         from_value=lambda src: f"std::string({src}.begin(), {src}.end())")
        if f.type_name in _WELL_KNOWN:
            which, include = _WELL_KNOWN[f.type_name]
            self.includes.add(include)
            self.ros_includes.add(f"builtin_interfaces/msg/{which}.hpp")
            return _Kind(lambda src, dst: f"{dst} = ros_detail::to_{which}({src}, {name});",
                         from_into=lambda src, ptr: f"ros_detail::from_{which}({src}, {ptr});")
        t = self.types.get(f.type_name) or self.imported.get(f.type_name)
        if t is None or (f.type_name in self.imported and not dependency(t.file, self.deps)):
            raise GeneratorError(
                f"{owner}.{f.name}: type {f.type_name[1:]} is not in the files being generated, "
                "or a dep=<proto path prefix>=<ROS package> parameter")
        if f.type_name in self.imported:
            # Its conversions (and ROS 2 type) come from the dependency's converter package
            self.ros_includes.add(f"{dependency(t.file, self.deps)}_convert/convert.hpp")
        if f.type == F.TYPE_ENUM:
            value = _ROS_CPP_SCALARS[_smallest([v.number for v in t.values], "uint8", "int32")]
            enum = self.proto_cpp(t)
            return _Kind(lambda src, dst: f"{dst}.value = static_cast<{value}>({src});",
                         from_value=lambda src: f"static_cast<{enum}>({src}.value)")
        return _Kind(lambda src, dst: f"to_ros({src}, &{dst});",
                     from_into=lambda src, ptr: f"from_ros({src}, {ptr});")

    def set_singular(self, owner, f):
        kind = self.kind(owner, f)
        src = f"in.{f.name}"
        if kind.from_into:
            return [kind.from_into(src, f"out->mutable_{f.name}()")]
        return [f"out->set_{f.name}({kind.from_value(src)});"]

    def bodies(self, m):
        owner = m.full_name[1:]
        to, frm = [], []
        oneof_starts = {o.fields[0].name: o for o in m.oneofs}
        for f in m.fields:
            if f.name in oneof_starts:
                o = oneof_starts[f.name]
                case_type = _ROS_CPP_SCALARS[_smallest([x.number for x in o.fields], "uint8", "uint32")]
                to.append(f"out->{o.name}_case = static_cast<{case_type}>(in.{o.name}_case());")
                frm += [f"switch (in.{o.name}_case)", "{"]
                for x in o.fields:
                    frm.append(f"    case {x.number}:")
                    frm += ["        " + s for s in self.set_singular(owner, x)]
                    frm.append("        break;")
                frm += ["    default:", "        break;", "}"]

            entry = self.types.get(f.type_name)
            if f.repeated and getattr(entry, "map_entry", False):
                key, value = (self.kind(owner, x) for x in entry.fields)
                to += [f"for (const auto* kv : ros_detail::sorted(in.{f.name}()))",
                       "{",
                       f"    out->{f.name}.emplace_back();",
                       f"    {key.to_stmt('kv->first', f'out->{f.name}.back().key')}",
                       f"    {value.to_stmt('kv->second', f'out->{f.name}.back().value')}",
                       "}"]
                k = key.from_value("e.key")
                if value.from_into:
                    set_value = value.from_into("e.value", f"&(*out->mutable_{f.name}())[{k}]")
                else:
                    set_value = f"(*out->mutable_{f.name}())[{k}] = {value.from_value('e.value')};"
                frm += [f"for (const auto& e : in.{f.name})", f"    {set_value}"]
                continue

            kind = self.kind(owner, f)
            if f.repeated:
                to += [f"for (const auto& e : in.{f.name}())",
                       "{",
                       f"    out->{f.name}.emplace_back();",
                       f"    {kind.to_stmt('e', f'out->{f.name}.back()')}",
                       "}"]
                if kind.from_into:
                    add = kind.from_into("e", f"out->add_{f.name}()")
                else:
                    add = f"out->add_{f.name}({kind.from_value('e')});"
                frm += [f"for (const auto& e : in.{f.name})", f"    {add}"]
                continue

            if f.has_presence:
                to.append(f"out->has_{f.name} = in.has_{f.name}();")
            to.append(kind.to_stmt(f"in.{f.name}()", f"out->{f.name}"))
            if f.oneof is None:
                if f.has_presence:
                    frm.append(f"if (in.has_{f.name})")
                    frm += ["    " + s for s in self.set_singular(owner, f)]
                else:
                    frm += self.set_singular(owner, f)
        return to, frm

    def header(self, messages):
        bodies = {m.full_name: self.bodies(m) for m in messages}
        proto_headers = sorted({m.file[:-len(".proto")] + ".pb.h" for m in messages} |
                               self.includes)
        ros_headers = sorted({f"{self.ros_package}/msg/{ros_header_name(m.flat_name)}.hpp"
                              for m in messages} | self.ros_includes)
        out = [f"// Generated by protoc-gen-ros: converts between the {self.package} Protobuf",
               f"// and {self.ros_package} ROS 2 C++ types.",
               "#pragma once",
               "",
               "#include <algorithm>",
               "#include <cmath>",
               "#include <cstdint>",
               "#include <limits>",
               "#include <stdexcept>",
               "#include <string>",
               "#include <type_traits>",
               "#include <vector>",
               ""]
        out += [f'#include "{h}"' for h in proto_headers]
        out.append("")
        out += [f'#include "{h}"' for h in ros_headers]
        detail = ""
        if any(h.startswith("builtin_interfaces/") for h in self.ros_includes):
            detail += _DETAIL_SECONDS
        if "builtin_interfaces/msg/time.hpp" in self.ros_includes:
            detail += _DETAIL_TIME
        if "builtin_interfaces/msg/duration.hpp" in self.ros_includes:
            detail += _DETAIL_DURATION
        detail += _DETAIL_SORTED
        out += ["", f"namespace {self.package.replace('.', '::')}", "{", "namespace ros_detail", "{",
                detail + "} // namespace ros_detail", ""]
        signatures = [(f"inline void to_ros(const {self.proto_cpp(m)}& in, {self.ros_cpp(m)}* out)",
                       f"inline void from_ros(const {self.ros_cpp(m)}& in, {self.proto_cpp(m)}* out)")
                      for m in messages]
        for to_sig, from_sig in signatures:
            out += [to_sig + ";", from_sig + ";"]
        for m, (to_sig, from_sig) in zip(messages, signatures):
            to, frm = bodies[m.full_name]
            out += ["", to_sig, "{", f"    *out = {self.ros_cpp(m)}();"]
            out += ["    " + s for s in to] if to else ["    (void)in;"]
            out += ["}", "", from_sig, "{", "    out->Clear();"]
            out += ["    " + s for s in frm] if frm else ["    (void)in;"]
            out.append("}")
        out += ["", f"}} // namespace {self.package.replace('.', '::')}", ""]
        return "\n".join(out)

    def package_xml(self):
        p = {k: escape(v) for k, v in self.params.items() if isinstance(v, str)}
        builtin = ("  <depend>builtin_interfaces</depend>\n"
                   if any(h.startswith("builtin_interfaces/") for h in self.ros_includes) else "")
        builtin += "".join(f"  <depend>{d}</depend>\n" for d in self.convert_deps)
        return f"""<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>{p['convert_package']}</name>
  <version>{p.get('version', '0.0.0')}</version>
  <description>Protobuf C++ library, and conversion to and from {p['package']}</description>
  <maintainer email="{p['maintainer_email']}">{p['maintainer']}</maintainer>
  <license>{p['license']}</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <depend>{p['package']}</depend>
{builtin}  <depend>protobuf-dev</depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
"""

    def cmake_lists(self):
        protos = "".join(f"    {f}\n" for f in self.proto_files)
        finds = "".join(f"find_package({d} REQUIRED)\n" for d in self.convert_deps)
        import_dirs = "".join(f" ${{{d}_PROTO_DIR}}" for d in self.convert_deps)
        links = "".join(f" {d}::{d}" for d in self.convert_deps)
        exports = "".join(f" {d}" for d in self.convert_deps)
        return f"""cmake_minimum_required(VERSION 3.10)
project({self.name} VERSION {self.params.get("version", "0.0.0")} LANGUAGES CXX)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package({self.ros_package} REQUIRED)
find_package(Protobuf REQUIRED)
{finds}
set(protos
{protos})

option(BUILD_SHARED_LIBS "Build shared libraries" ON)
add_library(${{PROJECT_NAME}})
set_target_properties(${{PROJECT_NAME}} PROPERTIES
  VERSION ${{PROJECT_VERSION}} SOVERSION {self.params.get("soversion", "0")})
protobuf_generate(
  TARGET ${{PROJECT_NAME}}
  LANGUAGE cpp
  PROTOS ${{protos}}
  IMPORT_DIRS ${{CMAKE_CURRENT_SOURCE_DIR}}{import_dirs}
  PROTOC_OUT_DIR ${{CMAKE_CURRENT_BINARY_DIR}})
target_include_directories(${{PROJECT_NAME}} PUBLIC
  $<BUILD_INTERFACE:${{CMAKE_CURRENT_BINARY_DIR}}>
  $<BUILD_INTERFACE:${{CMAKE_CURRENT_SOURCE_DIR}}/include>
  $<INSTALL_INTERFACE:include/${{PROJECT_NAME}}>)
target_link_libraries(${{PROJECT_NAME}} PUBLIC
  protobuf::libprotobuf ${{{self.ros_package}_TARGETS}}{links})

install(DIRECTORY include/ DESTINATION include/${{PROJECT_NAME}})
install(DIRECTORY ${{CMAKE_CURRENT_BINARY_DIR}}/ DESTINATION include/${{PROJECT_NAME}}
  FILES_MATCHING PATTERN "*.pb.h" PATTERN "CMakeFiles" EXCLUDE)
install(TARGETS ${{PROJECT_NAME}} EXPORT export_${{PROJECT_NAME}}
  ARCHIVE DESTINATION lib LIBRARY DESTINATION lib)
# So converter packages for protos that import these can build against them (<package>_PROTO_DIR)
foreach(proto IN LISTS protos)
  get_filename_component(directory ${{proto}} DIRECTORY)
  install(FILES ${{proto}} DESTINATION share/${{PROJECT_NAME}}/proto/${{directory}})
endforeach()

ament_export_targets(export_${{PROJECT_NAME}} HAS_LIBRARY_TARGET)
ament_export_dependencies({self.ros_package} Protobuf{exports})
ament_package(CONFIG_EXTRAS cmake/${{PROJECT_NAME}}-extras.cmake)
"""

    def cmake_extras(self):
        return f'set({self.name}_PROTO_DIR "${{{self.name}_DIR}}/../proto")\n'


# Helper sections of the ros_detail namespace, emitted only when used so that the header
# includes only the builtin_interfaces types it needs
_DETAIL_SECONDS = """inline int32_t to_ros_seconds(int64_t seconds, const char* field)
{
    if (seconds < std::numeric_limits<int32_t>::min() || seconds > std::numeric_limits<int32_t>::max())
        throw std::out_of_range(std::string(field) + " is outside builtin_interfaces' int32 seconds");
    return static_cast<int32_t>(seconds);
}

"""

_DETAIL_TIME = """// value in units since 1970 (units_per_second of them per second)
template <typename Int>
builtin_interfaces::msg::Time to_time(Int value, int64_t units_per_second, const char* field)
{
    if constexpr (std::is_unsigned_v<Int>)
    {
        if (value > static_cast<uint64_t>(std::numeric_limits<int64_t>::max()))
            throw std::out_of_range(std::string(field) + " does not fit in int64");
    }
    int64_t v = static_cast<int64_t>(value);
    int64_t seconds = v / units_per_second, remainder = v % units_per_second;
    if (remainder < 0)
    {
        remainder += units_per_second;
        --seconds;
    }
    builtin_interfaces::msg::Time t;
    t.sec = to_ros_seconds(seconds, field);
    t.nanosec = static_cast<uint32_t>(remainder * (1000000000 / units_per_second));
    return t;
}

// Truncates to whole units
template <typename Int>
Int from_time(const builtin_interfaces::msg::Time& t, int64_t units_per_second, const char* field)
{
    int64_t v = t.sec * units_per_second + t.nanosec / (1000000000 / units_per_second);
    bool fits;
    if constexpr (std::is_unsigned_v<Int>)
        fits = v >= 0 && static_cast<uint64_t>(v) <= std::numeric_limits<Int>::max();
    else
        fits = v >= std::numeric_limits<Int>::min() && v <= std::numeric_limits<Int>::max();
    if (!fits)
        throw std::out_of_range(std::string(field) + " does not fit its Protobuf type");
    return static_cast<Int>(v);
}

inline builtin_interfaces::msg::Time to_time_seconds(double seconds, const char* field)
{
    double whole = std::floor(seconds);
    builtin_interfaces::msg::Time t;
    t.sec = to_ros_seconds(static_cast<int64_t>(whole), field);
    t.nanosec = static_cast<uint32_t>(std::min((seconds - whole) * 1e9, 999999999.0));
    return t;
}

inline double from_time_seconds(const builtin_interfaces::msg::Time& t)
{
    return t.sec + t.nanosec * 1e-9;
}

template <typename Timestamp>
builtin_interfaces::msg::Time to_time(const Timestamp& timestamp, const char* field)
{
    builtin_interfaces::msg::Time t;
    t.sec = to_ros_seconds(timestamp.seconds(), field);
    t.nanosec = static_cast<uint32_t>(timestamp.nanos());
    return t;
}

template <typename Timestamp> void from_time(const builtin_interfaces::msg::Time& t, Timestamp* timestamp)
{
    timestamp->set_seconds(t.sec);
    timestamp->set_nanos(static_cast<int32_t>(t.nanosec));
}

"""

_DETAIL_DURATION = """// Protobuf Duration nanos have the sign of the seconds; builtin_interfaces nanosec is never negative
template <typename Duration>
builtin_interfaces::msg::Duration to_duration(const Duration& duration, const char* field)
{
    int64_t nanos = static_cast<int64_t>(to_ros_seconds(duration.seconds(), field)) * 1000000000 +
                    duration.nanos();
    int64_t seconds = nanos / 1000000000, remainder = nanos % 1000000000;
    if (remainder < 0)
    {
        remainder += 1000000000;
        --seconds;
    }
    builtin_interfaces::msg::Duration d;
    d.sec = to_ros_seconds(seconds, field);
    d.nanosec = static_cast<uint32_t>(remainder);
    return d;
}

template <typename Duration> void from_duration(const builtin_interfaces::msg::Duration& d, Duration* duration)
{
    int64_t nanos = static_cast<int64_t>(d.sec) * 1000000000 + d.nanosec;
    duration->set_seconds(nanos / 1000000000);
    duration->set_nanos(static_cast<int32_t>(nanos % 1000000000));
}

"""

_DETAIL_SORTED = """// Map iteration order is unspecified, so sort for a deterministic ROS message
template <typename Map> std::vector<const typename Map::value_type*> sorted(const Map& map)
{
    std::vector<const typename Map::value_type*> entries;
    for (const auto& kv : map) entries.push_back(&kv);
    std::sort(entries.begin(), entries.end(),
              [](const auto* a, const auto* b) { return a->first < b->first; });
    return entries;
}
"""


def generate(model, params):
    """Returns {path: content} for the converter package, relative to its directory. The
    protos it builds are copied in alongside by the build (protobuf_generate_ros)."""
    converter = _Converter(model, params)
    # Map entries convert inline, through the Protobuf Map API
    messages = [m for m in model.messages if not m.map_entry]
    return {
        f"include/{converter.name}/convert.hpp": converter.header(messages),
        "package.xml": converter.package_xml(),
        "CMakeLists.txt": converter.cmake_lists(),
        f"cmake/{converter.name}-extras.cmake": converter.cmake_extras(),
    }
