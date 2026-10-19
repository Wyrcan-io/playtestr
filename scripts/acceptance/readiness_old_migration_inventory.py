"""Inventory original saved outcomes without acquiring or executing another target."""
from readiness_evidence import ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    original = ROOT/'docs/validation/ten-new-project-adversarial-pass'
    candidates = load(original/'candidates.json')
    audit = load(original/'final-audit.json')
    projects = []
    for name in ['cookiecutter','copier','lf','superfile','helix','glow','broot','yazi','ranger','nnn']:
        matches = [r for r in candidates if r['repo'].split('/')[-1].lower() == name
                   and r['disposition'] == 'selected']
        if len(matches) != 1:
            raise RuntimeError('original canonical source pin is ambiguous: '+name)
        candidate = matches[0]
        scenarios = original/name/'scenarios.json'
        plan = load(scenarios)
        hosts = sorted({r['host'] for r in audit['project_host_pairs'] if r['project'] == name})
        if 'linux' not in hosts or len(hosts) < 2 or not set(hosts) <= {'linux','macos','windows'}:
            raise RuntimeError('original host boundary differs: '+name)
        cases = []
        for row in plan['cases']:
            counts = {key:(len(row[key]) if isinstance(row.get(key), (dict,list)) else int(bool(row.get(key)))) for key in
                      ['expected_files','absent_paths','expected_directories','empty_directories','exact_tree']}
            cases.append(dict(name=row['name'], original_purpose=row['purpose'], oracle_counts=counts,
                source_case_hosts=row.get('qualified_hosts'),
                preparation_status='Needs public v3 same-execution conversion and fresh native execution; no migration credit.'))
        projects.append(dict(project=name, repository=candidate['repo'], pin=candidate['sha'],
            original_scenarios_sha256=sha256(scenarios), previously_qualified_hosts=hosts,
            cases=cases, migration_executed=False, source_reacquired=False))
    if sum(len(p['cases']) for p in projects) != 130:
        raise RuntimeError('original scenario inventory differs')
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration-inventory.json',
        dict(projects=projects, original_scenario_count=130,
             original_audit_sha256=sha256(original/'final-audit.json'),
             original_candidates_sha256=sha256(original/'candidates.json'),
             qualification='Historical source inventory only. No source acquired, target run, migrated assertion or new admission.',
             migrated_projects=0, new_project_credit=0, runner_admission_credit=0))
    print('Inventoried 130 original scenarios and their historical native boundaries; execution remains open.')


if __name__ == '__main__':
    main()
