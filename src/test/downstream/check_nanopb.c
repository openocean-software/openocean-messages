// Encodes and decodes a Navigation with the installed nanopb library.

#include <stdio.h>

#include <pb_decode.h>
#include <pb_encode.h>

#include "openocean/messages/navigation.pb.h"

int main(void)
{
    openocean_Navigation nav = openocean_Navigation_init_zero;
    nav.time = 1000000;
    nav.has_geodetic = true;
    nav.geodetic.has_latitude = true;
    nav.geodetic.latitude = 41.5;

    uint8_t buffer[openocean_Navigation_size];
    pb_ostream_t out = pb_ostream_from_buffer(buffer, sizeof(buffer));
    openocean_Navigation decoded = openocean_Navigation_init_zero;
    if (!pb_encode(&out, openocean_Navigation_fields, &nav))
    {
        fprintf(stderr, "failed: encode\n");
        return 1;
    }
    pb_istream_t in = pb_istream_from_buffer(buffer, out.bytes_written);
    if (!pb_decode(&in, openocean_Navigation_fields, &decoded) || decoded.time != nav.time ||
        decoded.geodetic.latitude != nav.geodetic.latitude)
    {
        fprintf(stderr, "failed: decode\n");
        return 1;
    }
    return 0;
}
