package corpus_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"testing"
)

type manifest struct {
	SchemaVersion int `json:"schema_version"`
	WorkflowCount int `json:"workflow_count"`
	Projects      []struct {
		ID                string                       `json:"id"`
		Version           string                       `json:"version"`
		Repository        string                       `json:"repository"`
		License           string                       `json:"license"`
		Runtime           string                       `json:"runtime"`
		Install           string                       `json:"install"`
		Lock              string                       `json:"lock"`
		CleanState        string                       `json:"clean_state"`
		ExternalResources string                       `json:"external_resources"`
		Disposal          string                       `json:"disposal"`
		Identity          struct{ Kind, Value string } `json:"identity"`
		Limits            struct {
			RunSeconds  int `json:"run_seconds"`
			OutputBytes int `json:"output_bytes"`
		} `json:"limits"`
		Hosts map[string]string `json:"hosts"`
	} `json:"projects"`
}

type riskMap struct {
	SchemaVersion int `json:"schema_version"`
	Cases         []struct {
		ID, Family, Risk, Layer, Status, Reference, Gap string
	} `json:"cases"`
}

type pilotRecords struct {
	Pilots []struct {
		ID           string   `json:"id"`
		Command      string   `json:"command"`
		ManualRoute  string   `json:"manual_route"`
		Expectation  string   `json:"expectation"`
		Oracle       string   `json:"oracle"`
		Cleanup      string   `json:"cleanup"`
		SetupSeconds *float64 `json:"setup_seconds"`
		Attempts     []struct {
			Variant, Runner, Campaign string
		} `json:"attempts"`
	} `json:"pilots"`
}

func TestCorpusContract(t *testing.T) {
	root := repositoryRoot(t)
	var got manifest
	readJSON(t, filepath.Join(root, "corpus", "manifest.json"), &got)
	if got.SchemaVersion != 1 || got.WorkflowCount != 120 || len(got.Projects) != 15 {
		t.Fatalf("manifest header/projects = version %d, workflows %d, projects %d", got.SchemaVersion, got.WorkflowCount, len(got.Projects))
	}
	wantHosts := []string{"windows_amd64", "linux_amd64", "macos_arm64"}
	prefixes := make(map[string]bool)
	hash := regexp.MustCompile(`^[0-9a-fA-F]{40}([0-9a-fA-F]{24})?$`)
	for _, project := range got.Projects {
		if prefixes[project.ID] {
			t.Fatalf("duplicate project ID %q", project.ID)
		}
		prefixes[project.ID] = true
		for name, value := range map[string]string{
			"version": project.Version, "repository": project.Repository, "license": project.License,
			"runtime": project.Runtime, "install": project.Install, "lock": project.Lock,
			"clean_state": project.CleanState, "external_resources": project.ExternalResources,
			"disposal": project.Disposal, "identity.kind": project.Identity.Kind,
		} {
			if strings.TrimSpace(value) == "" {
				t.Errorf("project %s has empty %s", project.ID, name)
			}
		}
		if !hash.MatchString(project.Identity.Value) {
			t.Errorf("project %s identity is not an exact SHA-1/SHA-256: %q", project.ID, project.Identity.Value)
		}
		if project.Limits.RunSeconds <= 0 || project.Limits.OutputBytes <= 0 {
			t.Errorf("project %s has unbounded limits", project.ID)
		}
		for _, host := range wantHosts {
			if project.Hosts[host] == "" {
				t.Errorf("project %s omits host %s", project.ID, host)
			}
		}
	}

	catalog, err := os.ReadFile(filepath.Join(root, "docs", "plans", "corpus-catalog.md"))
	if err != nil {
		t.Fatal(err)
	}
	re := regexp.MustCompile(`(?m)^\| ([A-Z]+-[0-9]{2}) \|`)
	matches := re.FindAllStringSubmatch(string(catalog), -1)
	if len(matches) != got.WorkflowCount {
		t.Fatalf("catalog has %d workflow rows, want %d", len(matches), got.WorkflowCount)
	}
	seen := make(map[string]bool)
	counts := make(map[string]int)
	for _, match := range matches {
		id := match[1]
		if seen[id] {
			t.Fatalf("duplicate workflow %s", id)
		}
		seen[id] = true
		prefix := strings.SplitN(id, "-", 2)[0]
		if !prefixes[prefix] {
			t.Errorf("workflow %s has no admitted project", id)
		}
		counts[prefix]++
	}
	for prefix := range prefixes {
		if counts[prefix] != 8 {
			t.Errorf("project %s maps %d workflows, want 8", prefix, counts[prefix])
		}
	}
}

func TestFocusedRiskMap(t *testing.T) {
	root := repositoryRoot(t)
	var got riskMap
	readJSON(t, filepath.Join(root, "corpus", "risk-map.json"), &got)
	if got.SchemaVersion != 1 || len(got.Cases) != 300 {
		t.Fatalf("risk map version/count = %d/%d, want 1/300", got.SchemaVersion, len(got.Cases))
	}
	wantFamilies := map[string]int{
		"spec/schema/CLI validation": 55, "process/input/lifecycle": 60,
		"render/readiness/resize": 60, "snapshots/suites": 40,
		"workspace/environment/filesystem": 45, "reports/install/artifact handling": 40,
	}
	ids := make(map[string]bool)
	counts := make(map[string]int)
	for _, entry := range got.Cases {
		if ids[entry.ID] || entry.ID == "" {
			t.Fatalf("empty or duplicate risk ID %q", entry.ID)
		}
		ids[entry.ID] = true
		counts[entry.Family]++
		if entry.Risk == "" || entry.Layer == "" {
			t.Errorf("case %s has no independently described risk/layer", entry.ID)
		}
		switch entry.Status {
		case "reviewed_existing":
			if entry.Reference == "" || entry.Gap != "" {
				t.Errorf("covered case %s has invalid reference/gap", entry.ID)
			}
			if _, err := os.Stat(filepath.Join(root, filepath.FromSlash(entry.Reference))); err != nil {
				t.Errorf("case %s references missing file %s", entry.ID, entry.Reference)
			}
		case "planned_gap":
			if entry.Gap == "" || entry.Reference != "" {
				t.Errorf("gap case %s has invalid reference/gap", entry.ID)
			}
		default:
			t.Errorf("case %s has unknown status %q", entry.ID, entry.Status)
		}
	}
	if !mapsEqual(counts, wantFamilies) {
		t.Fatalf("family counts = %v, want %v", counts, wantFamilies)
	}
}

func TestFivePilotRecords(t *testing.T) {
	root := repositoryRoot(t)
	var got pilotRecords
	readJSON(t, filepath.Join(root, "corpus", "pilots", "records.json"), &got)
	want := []string{"BT-06", "CV-01", "GUM-01", "LG-01", "LG-08"}
	var ids []string
	for _, pilot := range got.Pilots {
		ids = append(ids, pilot.ID)
		for name, value := range map[string]string{"command": pilot.Command, "manual route": pilot.ManualRoute, "expectation": pilot.Expectation, "oracle": pilot.Oracle, "cleanup": pilot.Cleanup} {
			if strings.TrimSpace(value) == "" {
				t.Errorf("pilot %s has empty %s", pilot.ID, name)
			}
		}
		if len(pilot.Attempts) < 3 {
			t.Errorf("pilot %s has only %d recorded attempt classes", pilot.ID, len(pilot.Attempts))
		}
		if pilot.SetupSeconds == nil || *pilot.SetupSeconds <= 0 {
			t.Errorf("pilot %s has no measured setup duration", pilot.ID)
		}
		for _, attempt := range pilot.Attempts {
			if strings.Contains(attempt.Runner, "pending") || attempt.Runner == "" || attempt.Campaign == "" {
				t.Errorf("pilot %s has unresolved attempt %+v", pilot.ID, attempt)
			}
		}
	}
	sort.Strings(ids)
	if strings.Join(ids, ",") != strings.Join(want, ",") {
		t.Fatalf("pilot IDs = %v, want %v", ids, want)
	}
}

func repositoryRoot(t *testing.T) string {
	t.Helper()
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	return filepath.Clean(filepath.Join(dir, "..", ".."))
}

func readJSON(t *testing.T, path string, target any) {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, target); err != nil {
		t.Fatalf("decode %s: %v", path, err)
	}
}

func mapsEqual(left, right map[string]int) bool {
	if len(left) != len(right) {
		return false
	}
	for key, value := range left {
		if right[key] != value {
			return false
		}
	}
	return true
}
