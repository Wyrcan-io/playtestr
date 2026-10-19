"""Replay the observed snapshot/report classification failure on retained evidence."""
from readiness_cleanup_plop import verify_retained_report_cleanup
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    packet=RAW/'native/39275956482/playtestr-Linux'
    event=load(packet/'events/ae9c0dfb07034069867dd02b0e3d9af9-finished.json')
    log=packet/'core/ae9c0dfb07034069867dd02b0e3d9af9/console.log'
    if event['exit_code']!=1 or event['console_sha256']!=sha256(log) or 'JSONDecodeError' not in log.read_text():
        raise RuntimeError('actual first cleanup failure differs')
    verify_retained_report_cleanup(packet/'rclone')
    journey=next((packet/'rclone/first-use').glob('*/journey.json'))
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/first-cleanup-disposition.json',
        dict(run='39275956482', host='linux-amd64', failed_attempt=event['id'], log_sha256=sha256(log),
             journey_sha256=sha256(journey),
             cause='Acceptance cleanup assumed every .json file was JSON; full-screen snapshot saved-config.json is ordinary plain-text snapshot content.',
             repair='Exclude only snapshot payloads explicitly referenced by public specs, with confined baseline paths. Malformed report evidence and failed cleanup remain rejected.',
             regression='Actual retained Linux packet passes corrected report classification; four negative/positive unit controls pass.',
             qualification='Original job remains failed. Full source retention/removal and fresh native first-use rerun still required.',
             production_go_changed=False, runner_archive_changed=False))
    print('Actual retained cleanup failure reproduced and classified; original native job remains failed.')


if __name__ == '__main__':
    main()
