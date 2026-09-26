// Helpers shared by the converter checks: count failures, and round-trip a Protobuf message
// through its ROS 2 type with to_ros() and from_ros() (found by argument-dependent lookup).
#pragma once

#include <iostream>
#include <string>

#include <google/protobuf/util/message_differencer.h>

namespace check
{
inline int errors = 0;

inline void expect(bool ok, const std::string& what)
{
    if (!ok)
    {
        std::cerr << "failed: " << what << "\n";
        ++errors;
    }
}

// Converts proto to ROS and back, checks nothing changed, and returns the ROS message
template <typename Ros, typename Proto> Ros round_trip(const Proto& proto, const std::string& name)
{
    Ros ros;
    to_ros(proto, &ros);
    Proto back;
    from_ros(ros, &back);
    std::string diff;
    bool equal;
    {
        // The reporter only writes the differences out when the differencer is destroyed
        google::protobuf::util::MessageDifferencer differencer;
        differencer.ReportDifferencesToString(&diff);
        equal = differencer.Compare(proto, back);
    }
    expect(equal, name + " round trip: " + diff);
    return ros;
}

template <typename Exception, typename F> void expect_throws(F f, const std::string& what)
{
    try
    {
        f();
        expect(false, what + " did not throw");
    }
    catch (const Exception&)
    {
    }
}

inline int finish(const std::string& what)
{
    if (errors == 0)
        std::cout << what << " OK\n";
    return errors == 0 ? 0 : 1;
}
} // namespace check
