# openocean-messages

This project aims to provide a subset of common messages to improve interoperability between marine robotic systems, *regardless of middleware or programming language.*

In this repo are generic messages (defined in Protobuf) for ocean systems and tools to generate native formats from these messages. 

Messages are automatically converted to the desired output format as a first-class native type, so Protobuf is *not needed at runtime* for non-Protobuf output types (e.g. ROS Msg).

The output formats currently supported by this project are:

- Protobuf
  - C++ (built-in)
  - Python (built-in)
  - Rust (prost)
  - C (nanopb)
* ROS2 Msg
	- Conversion to/from Protobuf optional.
* LCM types
	- Conversion to/from Protobuf optional.

This project is an initiative of Open Ocean Software: https://oceansoft.org.

## Documentation

*This section was written by Claude.*

See the [documentation](src/doc/index.md) for the messages, building, and using the outputs from another project. [openocean-messages-examples](https://github.com/openocean-software/openocean-messages-examples) has a small, independent example project for each output.

## License

*This section was written by Claude.*

Apache-2.0; see [LICENSE](LICENSE).
