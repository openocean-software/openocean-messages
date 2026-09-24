# openocean-messages
Generic messages for ocean system and tools to generate native formats

Messages are defined in Protobuf. Every numeric field declares its units as a [UDUNITS-2](https://docs.unidata.ucar.edu/udunits/current/) string using the `(openocean.field).units` option.

## Repo Structure

- src: Source code
  - messages: Message definitions (Protobuf, imported as `messages/*.proto`)
    - options.proto: Field options (units)
    - common.proto: Types shared between messages (Speed, Euler)
    - navigation.proto: Navigation (vehicle state)
    - control.proto: ControlSetpoint (heading, speed, depth, etc.)
  - test: Checks that all units parse with UDUNITS-2 and that fields ControlSetpoint shares with Navigation have the same type and units

## Conventions

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU e, n, u about a datum (u = -depth)
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
