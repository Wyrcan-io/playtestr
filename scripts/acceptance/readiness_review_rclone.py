"""Bind the reviewed local-config scope and original Rclone build inputs."""
import json

from readiness_evidence import ROOT, RAW, immutable_json, sha256


def main():
    source = RAW / 'active/rclone/src'
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    acquisition = json.loads((source.parent / 'acquisition.json').read_text())
    reviewed = ['README.md', 'COPYING', 'go.mod', 'go.sum', 'Makefile',
                'fs/versiontag.go', 'fs/versionsuffix.go', 'fs/config/ui.go',
                'fs/config/config.go', 'fs/config/configfile/configfile.go',
                'cmd/config/config.go', 'backend/local/local.go']
    record = dict(repository='rclone/rclone', pin=acquisition['pin'],
        archive_sha256=acquisition['archive_sha256'], license='MIT',
        primary_source='https://github.com/rclone/rclone/tree/'+acquisition['pin'],
        native_hosts=['linux-amd64', 'windows-amd64'],
        scope='Trusted local storage configuration wizard; synthetic plaintext config and sentinel only.',
        reviewed_source_files=reviewed,
        review_findings=[
            'ReadLine uses real-TTY liner input; each observed prompt needs a submitted line.',
            'NewRemote validates names, chooses a backend, confirms options and saves config.',
            'Save writes a temporary file, synchronizes, renames old/new, and removes its transient backup.',
            'Delete removes a selected section and saves without a separate confirmation.',
            'SaveConfig logs exhausted retries rather than returning an error; saved-state assertions are necessary.',
            'Makefile contains installation/resource/version hooks; use direct go build instead.',
            'go.mod requires Go 1.26.0; use an official checksum-verified owned Go 1.27.0 SDK.',
            'All source hashes below bind original build/embedded inputs; this catalog is not an audit of all backends.'
        ],
        excluded=['cloud credentials', 'remote connections', 'browser authentication', 'mounts',
                  'server operation', 'password encryption', 'Makefile/install/generate hooks'],
        build=dict(command=['go', 'build', '-p', '2', '-mod=readonly', '-trimpath', '-buildvcs=false',
                            '-ldflags', '-s -w', '-o', 'OWNED/bin/rclone', '.'],
                   cgo_enabled=False, expected_version='rclone v1.76.0-DEV',
                   active_forecast_mib=3072, active_hard_stop_mib=3840,
                   caches_and_home='Owned active/rclone descendants; no global installs.'),
        provisional_freeze_sha256=sha256(docs/'provisional-candidate-freeze.json'),
        reviewed_inputs={p.relative_to(source).as_posix():sha256(p)
                         for p in sorted(source.rglob('*')) if p.is_file()})
    immutable_json(docs/'rclone/source-review.json', record)
    (docs/'rclone/UPSTREAM_LICENSE.txt').write_bytes((source/'COPYING').read_bytes())
    print('Rclone local-config source review and original-input catalog recorded.')


if __name__ == '__main__':
    main()
