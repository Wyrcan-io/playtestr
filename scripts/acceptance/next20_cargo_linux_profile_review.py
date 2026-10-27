"""Review the observed native emoji variant without altering canonical assertions."""
import json

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';packet=RAW/'native/40462439055/next20-cargo-linux-preflight'
    original=package/'snapshots/normal-project.rows.json';frozen=json.loads((package/'development-test-freeze.json').read_text())
    if sha256(original)!=frozen['inputs']['snapshots/normal-project.rows.json']:raise ValueError('original frozen snapshot changed')
    expected=json.loads(original.read_text(encoding='utf-8-sig'))
    if expected['first_row']!=4 or expected['last_row']!=9:raise ValueError('original selected row scope changed')
    # These exact prefixes follow upstream's reviewed console::Emoji values.
    native_text='\U0001f527   project-name: synthetic-notes ...\n\U0001f527   Generating template ...\n\U0001f937   Project owner: Ada\n? \U0001f937   Project mode \u203a\n\u276f basic\n  extended\n'
    screen=packet/'cargo-generate/host-contracts/normal-project.json.actual.txt'
    selected=''.join(screen.read_text(encoding='utf-8').splitlines(keepends=True)[3:9])
    if selected!=native_text:raise ValueError('observed Linux rows differ from independently reviewed native emoji text')
    dep=RAW/'r/registry/src/index.crates.io-1949cf8c6b5b557f/console-0.16.6/src'
    source_files={str(n):sha256(dep/n) for n in ['utils.rs','unix_term.rs','windows_term/mod.rs']}
    if 'env::var("WT_SESSION").is_ok()' not in (dep/'windows_term/mod.rs').read_text(encoding='utf-8') or 'lang.to_uppercase().ends_with("UTF-8")' not in (dep/'unix_term.rs').read_text(encoding='utf-8'):
        raise ValueError('reviewed console emoji-selection source changed')
    destination=package/'native-profiles/linux/snapshots/normal-project.rows.json'
    immutable_json(destination,dict(expected,text=native_text))
    immutable_json(package/'native-linux-profile-review-v2.json',dict(schema_version=1,revision=2,
        first_run='40462439055',qualification_revision='bb1fa7aa5bf847de74327ca077e31b7ab87f631e',
        first_outcome=dict(passed=19,failed=1,category='snapshot_mismatch',failed_case='N01'),
        canonical_snapshot_sha256=sha256(original),native_snapshot=destination.relative_to(package).as_posix(),
        native_snapshot_sha256=sha256(destination),actual_first_screen_sha256=sha256(screen),
        console_source_sha256=source_files,upstream_emoji_source_sha256=sha256(RAW/'active/cargo-generate/src/src/emoji.rs'),
        review='console0.16.6 chooses emoji on UTF-8 LANG for Unix, and only with WT_SESSION on Windows. The isolated Windows route uses the empty fallback; actual Linux emits the reviewed wrench/shrug glyphs. Exact same six selected rows, project/owner/mode text and menu entries remain asserted. No normalization, row removal, interaction change or saved-state weakening.',
        native_environment=dict(LANG='C.UTF-8',LC_ALL='C.UTF-8'),canonical_inputs_unchanged=True,
        replacement_budget=dict(first_actual_job_seconds=286,first_conservative_minutes=5,
            replacement_job_minutes_ceiling=30,aggregate_native_minutes_ceiling=35,original_native_minutes_ceiling=35,
            maximum_parallel_target_jobs=1,automatic_push_harness_minutes_ceiling=15),
        disposition='First19/20 series remains rejected. Rerun all20 after source-matched harness; no per-case automatic retry, old19 transfer, source fault removal or Playtestr archive rebuild.',
        final_ordinary_credit=0,project_credit=0))
    print('Reviewed exact Linux emoji snapshot profile; original six-row Windows snapshot and all saved-state oracles unchanged.')


if __name__=='__main__':main()
