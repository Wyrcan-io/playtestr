package schema_test

import (
	"encoding/json"
	"os"
	"slices"
	"testing"
)

func TestVersionedSchemaContracts(t *testing.T) {
	v1 := readSchema(t, "playtestr-spec-v1.schema.json")
	v2 := readSchema(t, "playtestr-spec-v2.schema.json")
	if property(t, v1, "version")["const"] != float64(1) || property(t, v2, "version")["const"] != float64(2) {
		t.Fatal("spec schemas do not declare distinct versions")
	}
	if _, exists := properties(t, v1)["workspace"]; exists {
		t.Fatal("spec v1 was expanded with workspace")
	}
	if _, exists := properties(t, v2)["cwd"]; exists {
		t.Fatal("spec v2 must not admit ambiguous top-level cwd")
	}
	required := strings(t, v2["required"])
	for _, name := range []string{"version", "command", "workspace", "steps"} {
		if !slices.Contains(required, name) {
			t.Fatalf("spec v2 does not require %q", name)
		}
	}
	workspace := property(t, v2, "workspace")
	if workspace["additionalProperties"] != false || !slices.Contains(strings(t, workspace["required"]), "fixture") {
		t.Fatal("spec v2 workspace is not strict or does not require fixture")
	}

	report1 := readSchema(t, "playtestr-report-v1.schema.json")
	report2 := readSchema(t, "playtestr-report-v2.schema.json")
	if property(t, report1, "report_version")["const"] != float64(1) || property(t, report2, "report_version")["const"] != float64(2) {
		t.Fatal("report schemas do not declare distinct versions")
	}
	definitions := report2["$defs"].(map[string]any)
	result := definitions["result"].(map[string]any)
	if _, exists := result["properties"].(map[string]any)["workspace"]; !exists {
		t.Fatal("report v2 result lacks workspace metadata")
	}
	failure := definitions["failure"].(map[string]any)
	categories := strings(t, failure["properties"].(map[string]any)["category"].(map[string]any)["enum"])
	for _, category := range []string{"workspace_setup_failure", "workspace_cleanup_failure"} {
		if !slices.Contains(categories, category) {
			t.Fatalf("report v2 lacks %q", category)
		}
	}
}

func readSchema(t *testing.T, name string) map[string]any {
	t.Helper()
	data, err := os.ReadFile(name)
	if err != nil {
		t.Fatal(err)
	}
	var document map[string]any
	if err := json.Unmarshal(data, &document); err != nil {
		t.Fatal(err)
	}
	return document
}

func properties(t *testing.T, document map[string]any) map[string]any {
	t.Helper()
	value, ok := document["properties"].(map[string]any)
	if !ok {
		t.Fatal("schema properties are missing")
	}
	return value
}

func property(t *testing.T, document map[string]any, name string) map[string]any {
	t.Helper()
	value, ok := properties(t, document)[name].(map[string]any)
	if !ok {
		t.Fatalf("schema property %q is missing", name)
	}
	return value
}

func strings(t *testing.T, value any) []string {
	t.Helper()
	items, ok := value.([]any)
	if !ok {
		t.Fatal("schema string array is missing")
	}
	result := make([]string, len(items))
	for index, item := range items {
		result[index], ok = item.(string)
		if !ok {
			t.Fatal("schema array contains a non-string")
		}
	}
	return result
}
