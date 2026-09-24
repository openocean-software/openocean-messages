# openocean-messages
Generic messages for ocean system and tools to generate native formats

Messages are defined in Protobuf. Every numeric field declares its units as a [UDUNITS-2](https://docs.unidata.ucar.edu/udunits/current/) string using the `(openocean.field).units` option.

## Repo Structure

- src: Source code
  - messages: Message definitions (Protobuf, imported as `messages/*.proto`)
    - options.proto: Field options (units)
    - navigation.proto: Navigation (vehicle state)
    - control.proto: ControlSetpoint (heading, speed, depth, etc.)
  - test: Checks that all units parse with UDUNITS-2 and that ControlSetpoint stays aligned with Navigation

## Conventions

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU x, y, z about a datum (z = -depth)
- Body-frame velocities are forward, starboard, down (Fossen / SNAME)
- Heading and course are clockwise from true north
- Unset optional fields are unknown (Navigation) or not controlled (ControlSetpoint)

## Building

Install the dependencies (Ubuntu), then build with CMake and Ninja:

```
./init.sh
./build.sh
ctest --test-dir build
```

`build.sh` passes any arguments on to CMake, and `BUILD_DIR` overrides the build directory (default `build`).
