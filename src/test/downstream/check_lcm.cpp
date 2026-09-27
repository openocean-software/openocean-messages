// Checks the downstream LCM type, which refers to openocean's LCM types, and with the C++ output,
// that its converter (which uses openocean's) round-trips a Report.

#include <iostream>
#include <vector>

#include "downstream/report_t.hpp"
#ifdef WITH_CPP
#include "downstream/lcm_convert.h"
#endif

int main()
{
    downstream::report_t report{};
    report.has_navigation = true;
    report.navigation.time = 1000000;
    report.note = "test";

    std::vector<uint8_t> buffer(report.getEncodedSize());
    downstream::report_t decoded;
    if (report.encode(buffer.data(), 0, static_cast<int>(buffer.size())) < 0 ||
        decoded.decode(buffer.data(), 0, static_cast<int>(buffer.size())) < 0 ||
        decoded.navigation.time != report.navigation.time || decoded.note != report.note)
    {
        std::cerr << "failed: LCM round trip\n";
        return 1;
    }

#ifdef WITH_CPP
    downstream::Report proto;
    downstream::from_lcm(decoded, &proto);
    downstream::report_t back;
    downstream::to_lcm(proto, &back);
    if (proto.navigation().time() != 1000000 || proto.note() != "test" ||
        back.navigation.time != report.navigation.time)
    {
        std::cerr << "failed: Protobuf conversion\n";
        return 1;
    }
#endif
    return 0;
}
