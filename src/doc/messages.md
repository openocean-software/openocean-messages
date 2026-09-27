# Messages

*This page was written by Claude.*

Messages are defined in Protobuf in `src/openocean/messages`, imported as `openocean/messages/*.proto`:

- options.proto: Field options (units)
- common.proto: Types shared between messages (Speed, Euler, CustomValue)
- navigation.proto: Navigation (vehicle state)
- control.proto: ControlSetpoint (heading, speed, depth, etc.)
- nanopb.options: nanopb size limits

Every numeric field declares its units as a [UDUNITS-2](https://docs.unidata.ucar.edu/udunits/current/) string using the `(openocean.field).units` option.

## Conventions

- Geodetic position is latitude, longitude, and depth (positive down)
- Local position is ENU: **e**ast, **n**orth, **u**p about a datum (where up = -depth), relative to some datum (in latitude/longitude).
- Body-frame velocities are forward, starboard, down (Fossen / SNAME)
- Heading and course are clockwise from true north.
- Optional fields indicate no data (Navigation) or not controlled (ControlSetpoint).

## Extending the messages

Projects that need more than openocean's fields should wrap the openocean message in their own (composition):

```protobuf
import "openocean/messages/navigation.proto";

message ContactReport
{
    openocean.Navigation nav = 1;
    string type = 2;
    optional double length = 3;
}
```

Composition works with every output: the ROS 2 and LCM generators refer to openocean's types with `dep=` (see [Using from another project](using.md#using-from-another-project)), so the wrapper is a native, typed message there too. It is a different message from `openocean.Navigation`, though, so subscribers to that type don't see it.

For a few loosely typed values (e.g. one more sensor reading), `Navigation.custom` and `ControlSetpoint.custom` hold a list of `CustomValue` (name, value, and UDUNITS-2 units) instead.

Field numbers 1000 and up are reserved in `Navigation` and `ControlSetpoint`, for messages that repeat their fields and add their own, so Protobuf readers of the openocean message can still read them.

Fields several projects need belong in openocean itself.
