// Serializes and parses a downstream message that holds an openocean message.

#include <iostream>

#include "downstream/report.pb.h"

int main()
{
    downstream::Report report;
    report.mutable_navigation()->mutable_geodetic()->set_latitude(41.5);
    report.set_note("test");

    downstream::Report parsed;
    if (!parsed.ParseFromString(report.SerializeAsString()) ||
        parsed.navigation().geodetic().latitude() != 41.5 || parsed.note() != "test")
    {
        std::cerr << "failed: Report round trip\n";
        return 1;
    }
    return 0;
}
