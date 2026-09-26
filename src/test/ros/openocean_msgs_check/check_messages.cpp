// Compiling this checks that the generated ROS 2 C++ types have the fields and
// constants protoc-gen-ros is meant to produce; running it checks a few values.

#include <iostream>

#include <openocean_msgs/msg/control_setpoint.hpp>
#include <openocean_msgs/msg/navigation.hpp>
#include <openocean_test_msgs/msg/mapping.hpp>

int main()
{
    int errors = 0;
    auto check = [&](bool ok, const char* what) {
        if (!ok)
        {
            std::cerr << "failed: " << what << "\n";
            ++errors;
        }
    };

    openocean_msgs::msg::Navigation nav;
    // uint64 microseconds since 1970 becomes builtin_interfaces/Time
    nav.time.sec = 1;
    nav.time.nanosec = 500;
    // optional presence becomes has_<field>
    check(!nav.has_geodetic, "has_ flags default to false");
    nav.has_geodetic = true;
    nav.geodetic.has_depth = true;
    nav.geodetic.depth = 10.0;
    // repeated becomes a sequence; enums become a message with constants and value
    openocean_msgs::msg::Speed speed;
    speed.has_mode = true;
    speed.mode.value = openocean_msgs::msg::SpeedMode::OVER_GROUND;
    nav.speed.push_back(speed);
    check(nav.speed.at(0).mode.value == 1, "SpeedMode::OVER_GROUND == 1");

    openocean_msgs::msg::ControlSetpoint setpoint;
    openocean_msgs::msg::ControlSetpointCustomSetpoint custom;
    custom.domain = "thruster";
    custom.value = 50;
    custom.units = "percent";
    setpoint.custom.push_back(custom);

    openocean_test_msgs::msg::Mapping mapping;
    // oneof becomes <oneof>_case with constants holding the field numbers
    mapping.choice_case = openocean_test_msgs::msg::Mapping::CHOICE_A;
    check(openocean_test_msgs::msg::Mapping::CHOICE_NOT_SET == 0, "CHOICE_NOT_SET == 0");
    check(openocean_test_msgs::msg::Mapping::CHOICE_B == 13, "CHOICE_B == 13");
    check(openocean_test_msgs::msg::MappingSigned::NEGATIVE == -1, "Signed::NEGATIVE == -1");
    mapping.data.push_back(0xff);
    mapping.stamp_ms.sec = 2;
    mapping.period.sec = 3;
    mapping.table.emplace_back();
    mapping.table.back().key = "k";

    if (errors == 0)
        std::cout << "ROS 2 C++ messages OK\n";
    return errors == 0 ? 0 : 1;
}
