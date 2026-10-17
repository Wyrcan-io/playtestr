# Microsoft Edit development journey

Project four, not admitted. Canonical source is
[microsoft/edit at cb6de0a8966aecd01d19a3541dab1829d0e679ca](https://github.com/microsoft/edit/tree/cb6de0a8966aecd01d19a3541dab1829d0e679ca),
screened as MIT, Rust, custom full-screen text editing. The pinned README and
workspace manifest have now been reviewed directly through the upstream API.

The source supports a normal stable Rust release build and requires Rust 1.93
or later. It also describes optional nightly/bootstrap optimizations and optional
ICU-backed search/replace. Use the ordinary stable build where available. No
installer, global Cargo/Rust update, user configuration or clipboard change is
authorized by this journey. Newly written caches, homes and outputs stay under
the owned active target. Read/execute existing toolchains; review source/build
hooks before execution. Source acquisition itself executes no build hooks.

Initial resource declaration: one active repository, 2 GiB active forecast below
the 4-GiB ceiling; default 8-MiB source archive, 64-MiB expanded, 10,000 entries
and 8-MiB individual source member guards. Build ceiling twenty minutes with
4-MiB output, owned caches/temp and bounded process-tree cleanup. Retention is
64 MiB across hosts; inspect/compact packets before accumulation can repeat
Bundler's recorded storage breach. Native Linux amd64 and Windows amd64 are the
provisional cells. No twenty-case, source-fault or framework coverage is claimed.

Next: inspect actual source/license/hooks and installed toolchain prerequisites,
build locally or on the authorized standard native hosts, then measure the public
documentation-only first-use route before authoring the twenty scenario package.
