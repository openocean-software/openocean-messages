// Checks the generated LCM types on their own (no Protobuf): that they have the fields and
// constants protoc-gen-lcm is meant to produce, and that a filled-in message survives the
// LCM encoding. The converters are checked separately, in check_convert.cpp.
//
// Prints one line per problem and exits non-zero if there were any.

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#include "openocean/navigation_t.hpp"
#include "openocean/test/mapping_t.hpp"

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
} // namespace

int main()
{
    openocean::navigation_t nav{};
    nav.time = 1000000;
    nav.has_geodetic = true;
    nav.geodetic.has_depth = true;
    nav.geodetic.depth = 10.0;
    nav.num_speed = 1;
    nav.speed.resize(1);
    nav.speed[0].has_mode = true;
    nav.speed[0].mode.value = openocean::speed_mode_t::OVER_GROUND;

    auto decoded = lcm_round_trip(nav);
    check(decoded.time == 1000000, "time");
    check(decoded.has_geodetic && decoded.geodetic.depth == 10.0, "geodetic.depth");
    check(!decoded.has_enu, "has_enu stays false");
    check(decoded.num_speed == 1 && decoded.speed.size() == 1, "num_speed");
    check(decoded.speed[0].mode.value == 1, "speed_mode_t::OVER_GROUND == 1");

    // Constants from the test Mapping: oneof cases hold field numbers, and enum values
    // keep their sign
    check(openocean::test::mapping_t::CHOICE_NOT_SET == 0, "CHOICE_NOT_SET == 0");
    check(openocean::test::mapping_t::CHOICE_B == 13, "CHOICE_B == 13");
    check(openocean::test::mapping_signed_t::NEGATIVE == -1, "mapping_signed_t::NEGATIVE == -1");
    check(openocean::test::mapping_color_t::GREEN == 1, "mapping_color_t::GREEN == 1");

    if (errors == 0)
        std::cout << "LCM types OK\n";
    return errors == 0 ? 0 : 1;
}
