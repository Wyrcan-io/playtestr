# Cookiecutter scope declared before recording

Pinned source and local synthetic templates; Linux/Windows qualification planned. No host credit until executed.

| Case | Kind | User risk |
| --- | --- | --- |
| normal-project | normal | Generate a nondefault two-file project with dependent slug, chosen license and exact state |
| normal-structured-data | normal | Structured metadata and Unicode render while declared literal text and binary payload are copied exactly |
| normal-nested-template | normal | Select a template below an aggregate directory; generated nested source is exact |
| normal-reviewed-hook | normal | Explicitly approve a reviewed local hook and verify its separate saved effect |
| normal-preserve-existing | normal | Overwrite directory with skip-existing policy preserves protected bytes and adds missing generated file |
| edge-choice-recovery | edge | Out-of-range choice is visibly rejected before valid correction |
| edge-boolean-recovery | edge | Invalid Boolean cannot silently become true; correction reaches exact output |
| edge-json-recovery | edge | Array is rejected for dict metadata and valid object then persists |
| edge-cancel-after-edit | edge | Cancel after entering name; no output directory or protected file mutation |
| edge-existing-rejected | edge | Existing destination is rejected at exact nonzero exit and all original bytes survive |

All cases use fresh fixture/home/temp, 8-second steps, 120-second whole runs, two MiB target output, four MiB harness capture. Expected files are constructed independently in this recipe, not derived from target-generated output.
