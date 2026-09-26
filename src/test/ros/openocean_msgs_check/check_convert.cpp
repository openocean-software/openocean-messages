// Checks the openocean Protobuf <-> openocean_msgs converters: Navigation and ControlSetpoint
// round trip, int64 microseconds become builtin_interfaces/Time, presence becomes has_ flags,
// and a time past builtin_interfaces' int32 seconds (2038) throws rather than wraps.

#include <cstdint>
#include <stdexcept>

#include <openocean_msgs_convert/convert.hpp>

#include "check_util.hpp"

int main()
{
    openocean::Navigation nav;
    nav.set_time(1500000);
    nav.mutable_vehicle()->set_name("auv1");
    nav.mutable_geodetic()->set_latitude(41.5);
    nav.mutable_geodetic()->set_depth(10.0);
    nav.mutable_attitude()->set_heading(1.0);
    auto* speed = nav.add_speed();
    speed->set_value(1.5);
    speed->set_mode(openocean::SPEED_MODE_OVER_GROUND);
    nav.set_altitude(20.0);

    auto ros = check::round_trip<openocean_msgs::msg::Navigation>(nav, "Navigation");
    check::expect(ros.time.sec == 1 && ros.time.nanosec == 500000000, "time as builtin_interfaces/Time");
    check::expect(ros.has_geodetic && ros.geodetic.has_depth && !ros.geodetic.has_longitude,
                  "presence flags");
    check::expect(!ros.has_enu, "unset enu has has_enu false");
    check::expect(ros.speed.size() == 1 &&
                      ros.speed[0].mode.value == openocean_msgs::msg::SpeedMode::OVER_GROUND,
                  "repeated speed with its SpeedMode");

    openocean::ControlSetpoint setpoint;
    setpoint.set_time(-1500000);
    setpoint.set_depth(5.0);
    auto* custom = setpoint.add_custom();
    custom->set_domain("thruster");
    custom->set_value(50);
    custom->set_units("percent");
    auto ros_setpoint =
        check::round_trip<openocean_msgs::msg::ControlSetpoint>(setpoint, "ControlSetpoint");
    check::expect(ros_setpoint.time.sec == -2 && ros_setpoint.time.nanosec == 500000000,
                  "a time before 1970 keeps nanosec non-negative");

    openocean::Navigation late;
    late.set_time(int64_t(1) << 52); // about the year 2112
    openocean_msgs::msg::Navigation late_ros;
    check::expect_throws<std::out_of_range>([&] { to_ros(late, &late_ros); },
                                            "time past builtin_interfaces' int32 seconds");

    return check::finish("ROS 2 converters");
}
