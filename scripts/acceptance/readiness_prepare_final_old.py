"""Prepare scoped workflows for six original migrations needing rc.5 rechecks."""
from readiness_evidence import ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    template=(ROOT/'.github/workflows/runner-readiness-old-superfile.yml').read_text(encoding='utf-8')
    declarations=[]
    for project in ['cookiecutter','copier','lf','superfile','helix','glow']:
        workflow=template.replace('original Superfile migration','final original '+project+' migration')
        workflow=workflow.replace('runner-readiness-old-superfile.yml','runner-readiness-final-old-'+project+'.yml')
        workflow=workflow.replace('superfile',project)
        workflow=workflow.replace('  PYTHONDONTWRITEBYTECODE:', '  READINESS_EVIDENCE_PHASE: final-archive\n  PYTHONDONTWRITEBYTECODE:')
        workflow=workflow.replace('run-id: 39147652486','run-id: 39450029736')
        workflow=workflow.replace('provisional-v1','migration-v2').replace('0.4.0-rc.4','0.4.0-rc.5')
        workflow=workflow.replace('readiness_install_provisional.py --archive','readiness_install_provisional.py --series migration-v2 --archive')
        workflow=workflow.replace('python3 ', 'python ')
        workflow=workflow.replace('${{ matrix.archive_target }}.tar.gz','${{ matrix.archive_target }}.${{ matrix.extension }}')
        workflow=workflow.replace('            archive_target: linux_amd64','            archive_target: linux_amd64\n            extension: tar.gz')
        workflow=workflow.replace('            archive_target: darwin_arm64','            archive_target: darwin_arm64\n            extension: tar.gz')
        hosts=['linux','macos']
        if project not in {'superfile','glow'}:
            hosts=['linux','windows']
            workflow=workflow.replace('os: macos-15\n            host: macos\n            target: darwin-arm64\n            archive_target: darwin_arm64\n            extension: tar.gz',
                'os: windows-2025\n            host: windows\n            target: windows-amd64\n            archive_target: windows_amd64\n            extension: zip')
        for phase in ['test','corruption']:
            workflow=workflow.replace('readiness_old_'+project+'_'+phase+'.py','readiness_old_'+project+'_'+phase+'.py --series migration-v2')
        workflow=workflow.replace('timeout-minutes: 30','timeout-minutes: 45')
        if project=='cookiecutter':workflow=workflow.replace('all twelve','all ten')
        if project=='helix':
            marker='      - name: Materialize original native prefixes and public saved-state assertions'
            workflow=workflow.replace(marker,
                '      - name: Build reviewed original target with locked offline dependencies\n'
                '        id: build\n'
                '        run: python scripts/acceptance/readiness_check.py --label old-helix-native-reviewed-build --timeout 1100 -- python scripts/acceptance/readiness_old_helix_build.py\n'+marker)
            workflow=workflow.replace('old-helix-native-real-corruption-recovery --timeout 600','old-helix-native-real-corruption-recovery --timeout 1100')
        readiness='build' if project=='helix' else 'prepare'
        before=("        if: always() && steps.prepare.outcome == 'success'\n"
            '        run: python scripts/acceptance/readiness_check.py --label old-'+project+'-native-checked-cleanup --timeout 240 -- python scripts/acceptance/readiness_cleanup_plop.py --project old-'+project)
        after=("        if: always() && steps."+readiness+".outcome == 'success' && runner.os != 'Windows'\n"
            '        run: python scripts/acceptance/readiness_check.py --label old-'+project+'-native-checked-cleanup --timeout 240 -- python scripts/acceptance/readiness_cleanup_plop.py --project old-'+project)
        if hosts[-1]=='windows':
            after+=('\n      - name: Verify Windows source restoration and checked native removal\n'
                "        if: always() && steps."+readiness+".outcome == 'success' && runner.os == 'Windows'\n"
                '        run: |\n'
                '          python scripts/acceptance/readiness_check.py --label old-'+project+'-native-process-proof --timeout 60 -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/acceptance/readiness_windows_process_proof.ps1 -Project old-'+project+'\n'
                '          python scripts/acceptance/readiness_check.py --label old-'+project+'-native-source-retention --timeout 240 -- python scripts/acceptance/readiness_cleanup_plop.py --project old-'+project+' --prepare-only\n'
                '          python scripts/acceptance/readiness_check.py --label old-'+project+'-native-source-removal --timeout 180 -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/acceptance/readiness_remove_plop.ps1 -Project old-'+project)
        if before not in workflow:raise RuntimeError('cleanup template changed')
        workflow=workflow.replace(before,after)
        if project in {'cookiecutter','copier','lf'}:
            # Their established independent auditor verifies these small exact
            # source archives directly; keep the historical receipt layout.
            workflow=workflow.replace('            !artifacts/runner-readiness-ten-project-pass/old-'+project+'/**/source.tar.gz\n','')
        path=ROOT/'.github/workflows'/('runner-readiness-final-old-'+project+'.yml')
        path.write_text(workflow,encoding='utf-8',newline='\n')
        declarations.append(dict(project=project,hosts=hosts,workflow_sha256=sha256(path),
            prior_migration_sha256=sha256(docs/'old-migration'/project/'admission.json') if (docs/'old-migration'/project/'admission.json').is_file() else None))
    immutable_json(docs/'final-old-migration-declaration.json',dict(projects=declarations,
        candidate_freeze_sha256=sha256(docs/'migration-candidate-freeze.json'),
        scope='Fresh exact rc.5 private archives for first six original migrations previously qualified on rc.4. Preserve original native case prefixes, all public saved-state oracles and actual source corruption/legacy false-green/recovery. Historical defaults and receipts remain unchanged. Standard native hosts, at most two application jobs, sequential project dispatch. Remaining four original migrations already bind rc.5; global final audit must verify those exact identities. No execution or admission credit from this declaration.'))
    print('Prepared six original migration recheck workflows; no targets acquired or executed.')


if __name__=='__main__':main()
