// Checks the converters for the test Mapping message, which covers each mapping rule the
// openocean messages don't: bytes, enums (including negative values), a oneof, maps (sorted by
// key on the ROS side), Timestamp and Duration (builtin_interfaces keeps nanosec non-negative),
// milliseconds since 1970 as Time, uint64 (which ROS 2 holds as is), and fields whose types come
// from openocean (converted by openocean_msgs_convert's functions). check_convert_main.cpp runs it.

#include <cstdint>
#include <limits>
#include <string>

#include <openocean_test_msgs_convert/convert.hpp>

#include "check_util.hpp"

void check_mapping_convert()
{
    openocean::test::Mapping m;
    m.set_implicit_presence(1.5);
    m.set_explicit_presence(2.5f);
    m.add_counts(-3);
    m.add_counts(4);
    m.set_data(std::string("\x00\xff\x7f", 3));
    m.set_color(openocean::test::Mapping::COLOR_GREEN);
    m.set_sign(openocean::test::Mapping::NEGATIVE);
    m.set_stamp_ms(1700000000123);
    m.mutable_stamp()->set_seconds(-2);
    m.mutable_stamp()->set_nanos(500000000);
    m.mutable_period()->set_seconds(-1);
    m.mutable_period()->set_nanos(-250000000);
    m.mutable_inner()->set_name("inner");
    m.add_inners()->set_name("first");
    m.mutable_b()->set_name("chosen");
    (*m.mutable_table())["z"] = 26;
    (*m.mutable_table())["a"] = 1;
    (*m.mutable_by_id())[7].set_name("seven");
    m.set_big(std::numeric_limits<uint64_t>::max());
    m.set_small(std::numeric_limits<uint32_t>::max());
    m.mutable_speed()->set_value(1.5);
    m.mutable_speed()->set_mode(openocean::SPEED_MODE_OVER_GROUND);
    m.set_mode(openocean::SPEED_MODE_ESTIMATE);

    auto ros = check::round_trip<openocean_test_msgs::msg::Mapping>(m, "Mapping");
    check::expect(ros.choice_case == openocean_test_msgs::msg::Mapping::CHOICE_B, "oneof case");
    check::expect(ros.data.size() == 3 && ros.data[1] == 0xff, "bytes");
    check::expect(ros.sign.value == openocean_test_msgs::msg::MappingSigned::NEGATIVE,
                  "negative enum value");
    check::expect(ros.stamp_ms.sec == 1700000000 && ros.stamp_ms.nanosec == 123000000,
                  "milliseconds since 1970 as Time");
    check::expect(ros.period.sec == -2 && ros.period.nanosec == 750000000,
                  "negative Duration with non-negative nanosec");
    check::expect(ros.table.size() == 2 && ros.table[0].key == "a" && ros.table[1].key == "z",
                  "map entries sorted by key");
    check::expect(ros.has_speed && ros.speed.value == 1.5 &&
                      ros.speed.mode.value == openocean_msgs::msg::SpeedMode::OVER_GROUND,
                  "openocean_msgs/Speed field");
    check::expect(ros.mode.value == openocean_msgs::msg::SpeedMode::ESTIMATE,
                  "openocean_msgs/SpeedMode field");

    openocean::test::Mapping empty;
    check::round_trip<openocean_test_msgs::msg::Mapping>(empty, "empty Mapping");
}
