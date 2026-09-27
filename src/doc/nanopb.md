# nanopb

*This page was written by Claude.*

`src/openocean/messages/nanopb.options` limits each repeated and string field (e.g. at most 2 `Navigation.speed` and 8 `custom` entries, 32-character strings), so every field is a fixed-size struct member rather than a callback. Messages that exceed a limit fail to encode or decode with nanopb.
