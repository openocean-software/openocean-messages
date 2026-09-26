# Generated from openocean.test.Mapping (mapping.proto)
#
# Covers each protoc-gen-ros mapping rule that openocean's own messages don't

float64 implicit_presence  # [m]
bool has_explicit_presence
float32 explicit_presence  # [s]
int32[] counts  # [1]
uint8[] data
MappingColor color
bool has_sign
MappingSigned sign
builtin_interfaces/Time stamp_ms
bool has_stamp
builtin_interfaces/Time stamp
bool has_period
builtin_interfaces/Duration period
bool has_inner
MappingInner inner
MappingInner[] inners

# one of a or b
uint8 CHOICE_NOT_SET=0
uint8 CHOICE_A=12
uint8 CHOICE_B=13
uint8 choice_case
float64 a  # [m]
MappingInner b
MappingTableEntry[] table  # [1]
