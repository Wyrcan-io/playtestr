"""Read narrowly declared omitted documentation links; never follow target links."""
import json
import re

from next20_check import DOC


def policy(path,project,pin):
    path=path.resolve(strict=True);path.relative_to((DOC/project).resolve(strict=True))
    value=json.loads(path.read_text(encoding='utf-8'))
    return value,validate_links(value,pin)


def validate_links(value,pin):
    links=value['omitted_documentation_links']
    if value.get('schema_version')!=1 or value['pin']!=pin or not isinstance(links,dict) or not 1<=len(links)<=8:raise ValueError('wrong pinned documentation-link policy')
    for name,target in links.items():
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.md',name) or not re.fullmatch(r'[A-Za-z0-9_-]+\.md',target) or name==target:
            raise ValueError('only explicit sibling Markdown documentation aliases may be omitted')
    return links
