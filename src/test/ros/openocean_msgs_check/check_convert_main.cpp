// Runs both converter checks in one process. That process loads both converter packages'
// shared libraries, so it also checks that openocean_test_msgs_convert links openocean's protos
// from openocean_msgs_convert rather than compiling them again: Protobuf aborts on a second
// registration of the same file.

#include "check_util.hpp"

void check_openocean_convert();
void check_mapping_convert();

int main()
{
    check_openocean_convert();
    check_mapping_convert();
    return check::finish("ROS 2 converters");
}
