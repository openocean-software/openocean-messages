# Compatibility checks

*This page was written by Claude.*

CI checks each pull request against its base branch, and the scripts run locally too (`.github/ci/check-abi.sh origin/main`):

| Check | Fails when | Unless |
|---|---|---|
| ABI (`check-abi.sh`, `abidiff`) | a shared library changes other than by additions (adding a field changes a generated class's size, so it counts) | `OPENOCEAN_SOVERSION` is bumped |
| Protobuf (`check-buf.sh`, `buf breaking` with the `FILE` rules in `buf.yaml`) | a proto changes incompatibly, including renames | the version's compatibility component is bumped: the major version, or in `0.y.z` the minor |
