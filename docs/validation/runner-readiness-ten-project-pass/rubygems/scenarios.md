# Declared RubyGems/Bundler scenarios

Declared before authoring tests. Canonical project `ruby/rubygems`, pin
`f033df93676007227d1ae0bd7326008e6396b3e9`, Bundler `4.1.0.beta2`.
Reviewed MIT option in `LICENSE.txt`/`MIT.txt`, actual executable entry points,
Thor gem-generation/configuration/init code and Ruby >=3.2 requirement.
The owned Windows Ruby 4.0.7 portable runtime is SHA-verified; no installer,
gem installation, development kit, upstream test suite or build hook runs.
Proposed cells: Linux amd64 and Windows amd64; neither is currently qualified.

Common bounds: fresh managed fixture/home/temp, 100x28 viewport unless varied,
10-second steps, 120-second scenario, 2 MiB terminal output, 1 MiB/64-file fixture.
Use actual source entry points via `ruby -EUTF-8 -S bundle` / `gem`, source/exe
before runtime/bin on PATH, and explicitly inherited owned RUBYLIB. Disable
generated-project Git/bundle-install/editor activity. Use synthetic metadata and
an explicit relative user-config file inside the fixture. No package-index
request, publishing, credentials or user Git/config state. Source URLs in
manifests are literal configuration; they do not authorize network operations.

After specific interaction/completion evidence and exact exit, public state
assertions inspect this execution before cleanup. Expected template bytes are
reviewed independently; binary gem archives require independent bounded payload
and metadata review. Capture/repetition/fault counts never fill scenario quota.

| ID | User task / risk | Positive checkpoint and saved outcome |
| --- | --- | --- |
| N01 | Choose RSpec in real gem authoring | Specific test-framework question, choose rspec, created-gem completion; exact relevant scaffold/config bytes and entry sets |
| N02 | Scaffold a C-extension gem | Explicit extension choice, successful creation; exact native extension source/config and module/version paths; no compilation claim |
| N03 | Build a complete reviewed local gem | Successfully-built/name/version/file result; exact reviewed reproducible package and unchanged source |
| N04 | Set project-local dependency install path | Exact exit 0, local YAML config with selected value; Gemfile unchanged |
| N05 | Unset obsolete local path while retaining another setting | Exact exit 0; only the selected policy disappears, other config bytes preserved |
| N06 | Create an offline lockfile for an empty dependency set | Specific lock completion, exact native-platform/version lock and unchanged Gemfile |
| N07 | Reopen and check a reviewed dependency-free lock | Dependencies-satisfied result, exit 0; existing manifest/lock unchanged |
| N08 | Initialize a dependency manifest in an existing project | Writing-new-Gemfile result; exact shipped manifest template, sentinel unchanged |
| E01 | Invalid Ruby constant/name | Specific invalid-name rejection and nonzero exit; no scaffold/preferences or unrelated changes |
| E02 | Decline overwrite of a dirty pre-existing Gemfile | Specific collision/skip and final creation; original Gemfile retained, other intended scaffold files exact |
| E03 | Ctrl-C at the framework question | Declared upstream interrupt exit 1; no generated project or preferences; existing sentinel unchanged |
| E04 | Destination ancestor is a regular file | Accurate native filesystem error/nonzero exit; original file unchanged, no descendant output |
| E05 | Repeated narrow/wide resize during a real overwrite diff | Invoke the documented collision diff on a reviewed 48 KiB dirty Gemfile using installed Git; observe diff output, resize 40x12 then 100x28, return, decline and prove exact original preservation/remaining generation. Quiet no-reflow resize is separately excluded |
| E06 | Nested Unicode/spaced parent plus namespaced gem | Specific namespace completion; exact portable paths/module/version and unchanged unrelated work |
| E07 | Missing local dependency during check | Specific missing-gem diagnostic, nonzero exit; no silent network/install or fabricated lock |
| E08 | Malformed manifest with an existing reviewed lock | Specific parse error/nonzero exit; original invalid input and old lock unchanged |
| E09 | Re-initialize over an existing dependency manifest | Specific already-exists refusal; exact original manifest and root entry set preserved |
| E10 | Conflicting dependency-group policies on a dirty config | Visible validation error/nonzero exit; complete reviewed config preserved |
| E11 | Print a lock without saving over an existing artifact | Specific printed lock/completion; manifest, existing lock and unrelated artifact unchanged |
| E12 | Build from a missing gem specification | Specific missing-spec error/exact nonzero exit; no package or partial output, existing source unchanged |

Combined cases: E02 dirty-file overwrite refusal; E05 repeated resize plus
collision decision and preservation; E06 namespace generation plus Unicode path;
E08 parse error plus old-lock preservation; E11 output-only operation plus dirty
artifact preservation. All involve the actual CLI, not fake screen emitters.

No support claim covers native extension compilation, external editors, Git
publishing, package downloads or network isolation. This pinned beta is the
qualified target if successful; results do not cover every Bundler/Ruby version.
Three real faults and a post-contract held-out selection remain pending.

Pre-authoring source review correction: boolean strings are accepted/coerced by
this upstream. E10 instead sets `with=development` against reviewed
`without=development`, exercising its real mutually-exclusive-group validator.
No boolean test was executed or counted. N06 uses explicit `--add-platform ruby`
and removes the native platform for a portable, independently reviewed lock.

E05 revision declared before its next execution: the original quiet collision
prompt failed its second Windows resize acknowledgment and remains a retained
unsupported boundary. The revised workflow actually requests Thor's supported
diff action, using `THOR_DIFF=git --no-pager diff --no-index --` and a bounded
48 KiB synthetic file. Resize occurs during the real child command's output;
there is no delay, synthetic target output, lowered fence or core exception.
Actual success and confirmed descendant/workspace cleanup remain required.
This adds a useful diff/return interaction; it does not establish quiet resize.

E05 subsequent pre-execution correction: the unpaged 1,200-line diff completed
before its early `@@` anchor could be observed, so the attempt timed out at the
readiness assertion before either resize. Use Git's documented pager option with
its installed `less` pager, inspect the first diff hunk, resize while the actual
pager is waiting, quit the pager, then explicitly decline overwrite. Set
`LESSHISTFILE=-` and `LESSSECURE=1`; no external commands/editor or history write.
This is a meaningful real child transition with long-content review, not a
timing delay or generated substitute output. Both earlier attempts remain red.
