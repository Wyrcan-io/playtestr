package corpus_test

import (
	"bytes"
	"encoding/json"
	"fmt"
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

type workflowResult struct {
	SchemaVersion int    `json:"schema_version"`
	RecordedOn    string `json:"recorded_on"`
	Project       struct {
		ID           string `json:"id"`
		Version      string `json:"version"`
		BinarySHA256 string `json:"binary_sha256"`
	} `json:"project"`
	Runner struct {
		SourceCommit string `json:"source_commit"`
		Host         string `json:"host"`
		Command      string `json:"command"`
	} `json:"runner"`
	StartingState struct {
		Fixture       string `json:"fixture"`
		FixtureSHA256 string `json:"fixture_sha256"`
		Home          string `json:"home"`
		Temp          string `json:"temp"`
	} `json:"starting_state"`
	Setup struct {
		Operation string `json:"operation"`
		ElapsedMS int    `json:"elapsed_ms"`
		Network   bool   `json:"network"`
	} `json:"setup"`
	Limits struct {
		RunMS       int   `json:"run_ms"`
		StepMS      int   `json:"step_ms"`
		OutputBytes int64 `json:"output_bytes"`
	} `json:"limits"`
	Workflows []struct {
		ID                       string                      `json:"id"`
		Spec                     string                      `json:"spec"`
		ExpectedScreen           string                      `json:"expected_screen"`
		IndependentPostcondition string                      `json:"independent_postcondition"`
		RunnerOutcome            string                      `json:"runner_outcome"`
		CampaignInterpretation   string                      `json:"campaign_interpretation"`
		TargetCommand            []string                    `json:"target_command"`
		Viewport                 struct{ Width, Height int } `json:"viewport"`
		ExpectedExit             int                         `json:"expected_exit"`
		DurationMS               int                         `json:"duration_ms"`
	} `json:"workflows"`
	Control struct {
		KnownBadSpec         string `json:"known_bad_spec"`
		ObservedCategory     string `json:"observed_category"`
		ObservedDifference   string `json:"observed_difference"`
		RecoverySpec         string `json:"recovery_spec"`
		ObservedRunnerStatus int    `json:"observed_runner_status"`
		TargetExit           int    `json:"target_exit"`
		RecoveryRunnerStatus int    `json:"recovery_runner_status"`
		CleanupConfirmed     bool   `json:"cleanup_confirmed"`
	} `json:"control"`
	Cleanup struct {
		AllTargetExitsConfirmed  bool `json:"all_target_exits_confirmed"`
		AllWorkspacesCleaned     bool `json:"all_workspaces_cleaned"`
		OriginalFixtureUnchanged bool `json:"original_fixture_unchanged"`
	} `json:"cleanup"`
	Exclusions []string `json:"exclusions"`
}

type boundaryMap struct {
	SchemaVersion int `json:"schema_version"`
	Projects      []struct {
		ID        string `json:"id"`
		Workflows []struct {
			ID        string `json:"id"`
			Kind      string `json:"kind"`
			Rationale string `json:"rationale"`
		} `json:"workflows"`
	} `json:"projects"`
}

type qualificationPlan struct {
	SchemaVersion int      `json:"schema_version"`
	Attempts      int      `json:"attempts_per_workflow_host"`
	Hosts         []string `json:"hosts"`
	Workflows     []struct {
		ID, Project, Spec, Class string
	} `json:"workflows"`
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
			parts := strings.SplitN(entry.Reference, "#", 2)
			path := filepath.Join(root, filepath.FromSlash(parts[0]))
			if _, err := os.Stat(path); err != nil {
				t.Errorf("case %s references missing file %s", entry.ID, entry.Reference)
			} else if len(parts) == 2 {
				data, err := os.ReadFile(path)
				if err != nil || !bytes.Contains(data, []byte("func "+parts[1]+"(")) {
					t.Errorf("case %s references missing test anchor %s", entry.ID, entry.Reference)
				}
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

func TestTwoReviewedBoundaryWorkflowsPerProject(t *testing.T) {
	root := repositoryRoot(t)
	var got boundaryMap
	readJSON(t, filepath.Join(root, "corpus", "boundary-map.json"), &got)
	if got.SchemaVersion != 1 || len(got.Projects) != 15 {
		t.Fatalf("boundary map version/projects = %d/%d, want 1/15", got.SchemaVersion, len(got.Projects))
	}
	available := make(map[string]bool)
	specs, err := filepath.Glob(filepath.Join(root, "corpus", "workflows", "*", "*.json"))
	if err != nil {
		t.Fatal(err)
	}
	for _, path := range specs {
		var spec struct {
			Name string `json:"name"`
		}
		readJSON(t, path, &spec)
		fields := strings.Fields(spec.Name)
		if len(fields) > 0 {
			available[fields[0]] = true
		}
	}
	seenProjects := make(map[string]bool)
	seenWorkflows := make(map[string]bool)
	for _, project := range got.Projects {
		if seenProjects[project.ID] || project.ID == "" {
			t.Fatalf("empty or duplicate boundary project %q", project.ID)
		}
		seenProjects[project.ID] = true
		if len(project.Workflows) != 2 {
			t.Errorf("project %s has %d reviewed boundary workflows, want 2", project.ID, len(project.Workflows))
		}
		for _, workflow := range project.Workflows {
			if seenWorkflows[workflow.ID] || !strings.HasPrefix(workflow.ID, project.ID+"-") || strings.TrimSpace(workflow.Kind) == "" || strings.TrimSpace(workflow.Rationale) == "" {
				t.Errorf("invalid or duplicate boundary workflow for %s: %+v", project.ID, workflow)
			}
			seenWorkflows[workflow.ID] = true
			if !available[workflow.ID] {
				t.Errorf("boundary workflow %s has no implemented spec", workflow.ID)
			}
		}
	}
}

func TestQualificationPlanDimensionsAndInputs(t *testing.T) {
	root := repositoryRoot(t)
	var got qualificationPlan
	readJSON(t, filepath.Join(root, "release", "qualification-plan.json"), &got)
	if got.SchemaVersion != 1 || got.Attempts != 100 || len(got.Hosts) != 3 || len(got.Workflows) != 10 {
		t.Fatalf("qualification dimensions = version %d, attempts %d, hosts %d, workflows %d", got.SchemaVersion, got.Attempts, len(got.Hosts), len(got.Workflows))
	}
	wantHosts := []string{"darwin_arm64", "linux_amd64", "windows_amd64"}
	sort.Strings(got.Hosts)
	if strings.Join(got.Hosts, ",") != strings.Join(wantHosts, ",") {
		t.Fatalf("qualification hosts = %v, want %v", got.Hosts, wantHosts)
	}
	projects := make(map[string]bool)
	workflows := make(map[string]bool)
	classes := make(map[string]bool)
	for _, workflow := range got.Workflows {
		if workflow.ID == "" || workflow.Project == "" || workflow.Class == "" || workflows[workflow.ID] {
			t.Fatalf("invalid or duplicate qualification workflow: %+v", workflow)
		}
		if _, err := os.Stat(filepath.Join(root, filepath.FromSlash(workflow.Spec))); err != nil {
			t.Errorf("qualification workflow %s references missing spec %s", workflow.ID, workflow.Spec)
		}
		projects[workflow.Project] = true
		workflows[workflow.ID] = true
		classes[workflow.Class] = true
	}
	if len(projects) < 5 || len(classes) < 8 {
		t.Fatalf("qualification breadth = %d projects, %d classes; want at least 5/8", len(projects), len(classes))
	}
	if len(got.Hosts)*len(got.Workflows)*got.Attempts != 3000 {
		t.Fatalf("qualification execution count is not exactly 3,000")
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

func TestCompletedGumWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "gum-windows-amd64.json", "GUM", "v0.17.0", "snapshot_mismatch")
}

func TestCompletedFZFWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "fzf-windows-amd64.json", "FZF", "v0.74.4", "snapshot_mismatch")
}

func TestCompletedMicroWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "micro-windows-amd64.json", "MICRO", "v2.0.14", "unexpected_exit")
}

func TestCompletedTelevisionWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "television-windows-amd64.json", "TV", "0.15.9", "snapshot_mismatch")
}

func TestCompletedNPKillWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "npkill-windows-amd64.json", "NPK", "0.12.2", "assertion_timeout")
}

func TestCompletedCreateViteWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "create-vite-windows-amd64.json", "CV", "9.2.1", "unexpected_exit")
}

func TestCompletedIPMWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "ipm-windows-amd64.json", "IPM", "1.3.3", "unexpected_exit")
}

func TestCompletedBottomWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "bottom-windows-amd64.json", "BT", "0.14.9", "assertion_timeout")
}

func TestCompletedLiteCLIWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "litecli-windows-amd64.json", "LITE", "1.17.1", "assertion_timeout")
}

func TestCompletedPostingWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "posting-windows-amd64.json", "POST", "2.10.0", "assertion_timeout")
}

func TestCompletedMitmproxyWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "mitmproxy-windows-amd64.json", "MITM", "12.2.3", "assertion_timeout")
}

func TestCompletedGitUIWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "gitui-windows-amd64.json", "GUI", "0.28.1", "unexpected_exit")
}

func TestCompletedLazygitWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "lazygit-windows-amd64.json", "LG", "0.65.0", "unexpected_exit")
}

func TestCompletedTIGWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "tig-windows-amd64.json", "TIG", "2.6.1", "assertion_timeout")
}

func TestCompletedTaskwarriorTUIWorkflowRecords(t *testing.T) {
	validateCompletedWorkflowRecord(t, "taskwarrior-tui-windows-amd64.json", "TASK", "0.27.0", "assertion_timeout")
}

func validateCompletedWorkflowRecord(t *testing.T, resultFile, projectID, projectVersion, controlCategory string) {
	t.Helper()
	root := repositoryRoot(t)
	var got workflowResult
	readJSON(t, filepath.Join(root, "corpus", "results", resultFile), &got)
	if got.SchemaVersion != 1 || got.Project.ID != projectID || got.Project.Version != projectVersion || got.Runner.Host != "windows_amd64" {
		t.Fatalf("result identity = version %d project %s/%s host %s", got.SchemaVersion, got.Project.ID, got.Project.Version, got.Runner.Host)
	}
	hash := regexp.MustCompile(`^[0-9a-f]{64}$`)
	if !hash.MatchString(got.Project.BinarySHA256) || !hash.MatchString(got.StartingState.FixtureSHA256) || !regexp.MustCompile(`^[0-9a-f]{40}$`).MatchString(got.Runner.SourceCommit) {
		t.Fatalf("result hashes are not exact: project=%q fixture=%q runner=%q", got.Project.BinarySHA256, got.StartingState.FixtureSHA256, got.Runner.SourceCommit)
	}
	if got.Setup.ElapsedMS <= 0 || got.Limits.RunMS <= 0 || got.Limits.StepMS <= 0 || got.Limits.OutputBytes <= 0 || len(got.Exclusions) == 0 {
		t.Fatalf("result omits setup, bounds, or exclusions: %+v", got)
	}
	if len(got.Workflows) != 8 {
		t.Fatalf("completed Gum workflows = %d, want 8", len(got.Workflows))
	}
	for index, workflow := range got.Workflows {
		wantID := fmt.Sprintf("%s-%02d", projectID, index+1)
		if workflow.ID != wantID || len(workflow.TargetCommand) == 0 || workflow.Viewport.Width <= 0 || workflow.Viewport.Height <= 0 || workflow.DurationMS <= 0 || workflow.RunnerOutcome != "passed" || workflow.CampaignInterpretation == "" || workflow.IndependentPostcondition == "" {
			t.Errorf("workflow %s record is incomplete: %+v", wantID, workflow)
			continue
		}
		var spec struct {
			Version        int      `json:"version"`
			Command        []string `json:"command"`
			Width          int      `json:"width"`
			Height         int      `json:"height"`
			TimeoutMS      int      `json:"timeout_ms"`
			RunTimeoutMS   int      `json:"run_timeout_ms"`
			MaxOutputBytes int64    `json:"max_output_bytes"`
		}
		readJSON(t, filepath.Join(root, filepath.FromSlash(workflow.Spec)), &spec)
		if spec.Version != 2 || strings.Join(spec.Command, "\x00") != strings.Join(workflow.TargetCommand, "\x00") || spec.Width != workflow.Viewport.Width || spec.Height != workflow.Viewport.Height || spec.TimeoutMS > got.Limits.StepMS || spec.RunTimeoutMS > got.Limits.RunMS || spec.MaxOutputBytes > got.Limits.OutputBytes {
			t.Errorf("workflow %s result/spec contract differs: result=%+v spec=%+v", workflow.ID, workflow, spec)
		}
	}
	if got.Control.ObservedRunnerStatus != 1 || got.Control.ObservedCategory != controlCategory || got.Control.RecoveryRunnerStatus != 0 || !got.Control.CleanupConfirmed {
		t.Fatalf("known-bad/recovery control = %+v", got.Control)
	}
	for _, path := range []string{got.Control.KnownBadSpec, got.Control.RecoverySpec} {
		if _, err := os.Stat(filepath.Join(root, filepath.FromSlash(path))); err != nil {
			t.Errorf("control references missing spec %q: %v", path, err)
		}
	}
	if !got.Cleanup.AllTargetExitsConfirmed || !got.Cleanup.AllWorkspacesCleaned || !got.Cleanup.OriginalFixtureUnchanged {
		t.Fatalf("cleanup result = %+v", got.Cleanup)
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
