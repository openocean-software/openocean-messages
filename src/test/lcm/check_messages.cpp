// Checks the generated LCM types and the Protobuf <-> LCM converters:
//
//  1. Navigation, ControlSetpoint, and the test Mapping message (which covers every
//     mapping rule: presence, repeated, bytes, enums, oneof, maps, well-known types,
//     unsigned integers) survive Protobuf -> LCM -> LCM bytes -> LCM -> Protobuf.
//  2. The LCM side has the expected shape (has_ flags, num_ counts, enum constants,
//     oneof case, maps sorted by key).
//  3. Values LCM can't hold, or inconsistent LCM input, throw rather than wrap.
//
// Prints one line per problem and exits non-zero if there were any.

#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

#include <google/protobuf/util/message_differencer.h>

#include "openocean/lcm_convert.h"
#include "openocean/test/lcm_convert.h"

namespace
{
int errors = 0;

void check(bool ok, const std::string& what)
{
    if (!ok)
    {
        std::cerr << "failed: " << what << "\n";
        ++errors;
    }
}

// Encodes and decodes an LCM message, as sending it over LCM would
template <typename T> T lcm_round_trip(const T& msg)
{
    std::vector<uint8_t> buffer(msg.getEncodedSize());
    if (msg.encode(buffer.data(), 0, static_cast<int>(buffer.size())) < 0)
        throw std::runtime_error("LCM encode failed");
    T decoded;
    if (decoded.decode(buffer.data(), 0, static_cast<int>(buffer.size())) < 0)
        throw std::runtime_error("LCM decode failed");
    return decoded;
}

// Converts proto to LCM and back through the LCM encoding, and checks nothing changed
template <typename Proto, typename Lcm> Lcm check_round_trip(const Proto& proto, const std::string& name)
{
    Lcm lcm;
    to_lcm(proto, &lcm);
    Lcm decoded = lcm_round_trip(lcm);
    Proto back;
    from_lcm(decoded, &back);
    std::string diff;
    bool equal;
    {
        // The reporter only writes the differences out when the differencer is destroyed
        google::protobuf::util::MessageDifferencer differencer;
        differencer.ReportDifferencesToString(&diff);
        equal = differencer.Compare(proto, back);
    }
    check(equal, name + " round trip: " + diff);
    return decoded;
}

void check_navigation()
{
    openocean::Navigation nav;
    nav.set_time(1000000);
    nav.mutable_vehicle()->set_name("auv1");
    nav.mutable_geodetic()->set_latitude(41.5);
    nav.mutable_geodetic()->set_depth(10.0);
    nav.mutable_attitude()->set_heading(1.0);
    auto* speed = nav.add_speed();
    speed->set_value(1.5);
    speed->set_mode(openocean::SPEED_MODE_OVER_GROUND);
    nav.add_speed()->set_value(1.4);
    nav.set_altitude(20.0);

    auto lcm = check_round_trip<openocean::Navigation, openocean::navigation_t>(nav, "Navigation");
    check(lcm.has_geodetic && lcm.geodetic.has_depth && !lcm.geodetic.has_longitude,
          "Navigation presence flags");
    check(!lcm.has_enu, "unset Navigation.enu has has_enu false");
    check(lcm.num_speed == 2 && lcm.speed.size() == 2, "num_speed counts the speeds");
    check(lcm.speed[0].has_mode && lcm.speed[0].mode.value == openocean::speed_mode_t::OVER_GROUND,
          "SpeedMode constant");
}

void check_control_setpoint()
{
    openocean::ControlSetpoint setpoint;
    setpoint.set_time(2000000);
    setpoint.set_depth(5.0);
    auto* custom = setpoint.add_custom();
    custom->set_domain("thruster");
    custom->set_value(50);
    custom->set_units("percent");
    check_round_trip<openocean::ControlSetpoint, openocean::control_setpoint_t>(setpoint,
                                                                                 "ControlSetpoint");
}

openocean::test::Mapping full_mapping()
{
    openocean::test::Mapping m;
    m.set_implicit_presence(1.5);
    m.set_explicit_presence(2.5f);
    m.add_counts(-3);
    m.add_counts(4);
    m.set_data(std::string("\x00\xff\x7f", 3));
    m.set_color(openocean::test::Mapping::COLOR_GREEN);
    m.set_sign(openocean::test::Mapping::NEGATIVE);
    m.set_stamp_ms(1700000000000);
    // Before 1970, so microseconds are negative but Timestamp nanos stay positive
    m.mutable_stamp()->set_seconds(-2);
    m.mutable_stamp()->set_nanos(500000000);
    // Durations keep nanos the same sign as seconds
    m.mutable_period()->set_seconds(-1);
    m.mutable_period()->set_nanos(-250000000);
    m.mutable_inner()->set_name("inner");
    m.add_inners()->set_name("first");
    m.add_inners()->set_name("second");
    m.mutable_b()->set_name("chosen");
    (*m.mutable_table())["z"] = 26;
    (*m.mutable_table())["a"] = 1;
    (*m.mutable_by_id())[7].set_name("seven");
    m.set_big(uint64_t(1) << 62);
    m.set_small(std::numeric_limits<uint32_t>::max());
    return m;
}

void check_mapping()
{
    auto lcm = check_round_trip<openocean::test::Mapping, openocean::test::mapping_t>(
        full_mapping(), "Mapping");
    check(lcm.choice_case == openocean::test::mapping_t::CHOICE_B, "oneof case constant");
    check(lcm.num_data == 3 && lcm.data[1] == 0xff, "bytes");
    check(lcm.sign.value == openocean::test::mapping_signed_t::NEGATIVE, "negative enum value");
    check(lcm.stamp == -1500000, "Timestamp as microseconds since 1970");
    check(lcm.period == -1250000, "Duration as microseconds");
    check(lcm.num_table == 2 && lcm.table[0].key == "a" && lcm.table[1].key == "z",
          "map entries sorted by key");

    // An unset oneof round trips as unset
    openocean::test::Mapping unset;
    check_round_trip<openocean::test::Mapping, openocean::test::mapping_t>(unset, "empty Mapping");
}

template <typename Exception, typename F> void check_throws(F f, const std::string& what)
{
    try
    {
        f();
        check(false, what + " did not throw");
    }
    catch (const Exception&)
    {
    }
}

void check_errors()
{
    // uint64 values above INT64_MAX don't fit LCM's int64_t
    auto too_big = full_mapping();
    too_big.set_big(uint64_t(1) << 63);
    openocean::test::mapping_t lcm;
    check_throws<std::out_of_range>([&] { to_lcm(too_big, &lcm); }, "uint64 above INT64_MAX");

    // A negative LCM value can't become a fixed32
    to_lcm(full_mapping(), &lcm);
    auto negative = lcm;
    negative.small = -1;
    openocean::test::Mapping back;
    check_throws<std::out_of_range>([&] { from_lcm(negative, &back); }, "negative fixed32");

    // A count that disagrees with its array is rejected
    auto inconsistent = lcm;
    inconsistent.num_counts = 5;
    check_throws<std::invalid_argument>([&] { from_lcm(inconsistent, &back); },
                                        "num_counts not matching counts");

    // Timestamps below a microsecond are truncated, which is expected, not an error
    openocean::test::Mapping fine;
    fine.mutable_stamp()->set_nanos(1500);
    to_lcm(fine, &lcm);
    from_lcm(lcm, &back);
    check(back.stamp().nanos() == 1000, "Timestamp truncates to microseconds");
}
} // namespace

int main()
{
    check_navigation();
    check_control_setpoint();
    check_mapping();
    check_errors();
    if (errors == 0)
        std::cout << "LCM messages and converters OK\n";
    return errors == 0 ? 0 : 1;
}
