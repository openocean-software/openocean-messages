// Round-trips Navigation and ControlSetpoint through the nanopb C library, using
// the static fields that nanopb.options gives the repeated and string fields.
//
// If given a path, also writes the encoded Navigation there, so that
// decode_navigation.py can check that Protobuf decodes nanopb's output.

#include <stdio.h>
#include <string.h>

#include <pb_decode.h>
#include <pb_encode.h>

#include "openocean/messages/control.pb.h"
#include "openocean/messages/navigation.pb.h"

static int errors = 0;

static void check(bool ok, const char* what)
{
    if (!ok)
    {
        fprintf(stderr, "failed: %s\n", what);
        ++errors;
    }
}

int main(int argc, char** argv)
{
    openocean_Navigation nav = openocean_Navigation_init_zero;
    nav.time = 1000000;
    nav.has_geodetic = true;
    nav.geodetic.has_latitude = true;
    nav.geodetic.latitude = 41.5;
    nav.geodetic.has_depth = true;
    nav.geodetic.depth = 10.0;
    nav.speed_count = 1;
    nav.speed[0].has_value = true;
    nav.speed[0].value = 1.5;
    nav.speed[0].has_mode = true;
    nav.speed[0].mode = openocean_SpeedMode_SPEED_MODE_OVER_GROUND;
    nav.has_vehicle = true;
    strcpy(nav.vehicle.name, "auv1");

    uint8_t nav_buf[openocean_Navigation_size];
    pb_ostream_t out = pb_ostream_from_buffer(nav_buf, sizeof nav_buf);
    check(pb_encode(&out, openocean_Navigation_fields, &nav), "encode Navigation");
    size_t nav_len = out.bytes_written;

    openocean_Navigation nav_back = openocean_Navigation_init_zero;
    pb_istream_t in = pb_istream_from_buffer(nav_buf, nav_len);
    check(pb_decode(&in, openocean_Navigation_fields, &nav_back), "decode Navigation");
    check(nav_back.has_geodetic && nav_back.geodetic.depth == 10.0, "geodetic.depth");
    check(!nav_back.geodetic.has_longitude, "unset longitude stays unset");
    check(!nav_back.has_enu, "unset enu stays unset");
    check(nav_back.speed_count == 1 && nav_back.speed[0].value == 1.5, "speed");
    check(strcmp(nav_back.vehicle.name, "auv1") == 0, "vehicle.name");

    openocean_ControlSetpoint setpoint = openocean_ControlSetpoint_init_zero;
    setpoint.has_depth = true;
    setpoint.depth = 5.0;
    setpoint.custom_count = 1;
    strcpy(setpoint.custom[0].domain, "thruster");
    setpoint.custom[0].value = 50;
    strcpy(setpoint.custom[0].units, "percent");

    uint8_t setpoint_buf[openocean_ControlSetpoint_size];
    out = pb_ostream_from_buffer(setpoint_buf, sizeof setpoint_buf);
    check(pb_encode(&out, openocean_ControlSetpoint_fields, &setpoint), "encode ControlSetpoint");

    openocean_ControlSetpoint setpoint_back = openocean_ControlSetpoint_init_zero;
    in = pb_istream_from_buffer(setpoint_buf, out.bytes_written);
    check(pb_decode(&in, openocean_ControlSetpoint_fields, &setpoint_back),
          "decode ControlSetpoint");
    check(setpoint_back.custom_count == 1 &&
              strcmp(setpoint_back.custom[0].units, "percent") == 0,
          "custom setpoint");

    if (argc > 1)
    {
        FILE* f = fopen(argv[1], "wb");
        check(f && fwrite(nav_buf, 1, nav_len, f) == nav_len && fclose(f) == 0,
              "write encoded Navigation");
    }

    if (errors == 0)
        printf("nanopb messages OK\n");
    return errors == 0 ? 0 : 1;
}
