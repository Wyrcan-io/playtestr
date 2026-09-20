// Command generate-risk-map writes the reviewed Sprint 11 focused-risk inventory.
// It is test infrastructure, not part of the Playtestr runner.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type family struct {
	ID    string
	Title string
	Risks []string
}

type riskCase struct {
	ID        string `json:"id"`
	Family    string `json:"family"`
	Risk      string `json:"risk"`
	Layer     string `json:"layer"`
	Status    string `json:"status"`
	Reference string `json:"reference,omitempty"`
	Gap       string `json:"gap,omitempty"`
}

type document struct {
	SchemaVersion int        `json:"schema_version"`
	FrozenOn      string     `json:"frozen_on"`
	Cases         []riskCase `json:"cases"`
}

var layers = []string{
	"pure contract boundary",
	"runner integration boundary",
	"Windows amd64 native boundary",
	"Linux amd64 native boundary",
	"macOS arm64 native boundary",
}

var families = []family{
	{ID: "VAL", Title: "spec/schema/CLI validation", Risks: []string{
		"unsupported spec version", "unknown object field", "explicit null field", "missing command", "empty command element",
		"step with mixed actions", "unsupported key name", "nonpositive duration", "viewport below minimum", "viewport above maximum", "invalid environment name",
	}},
	{ID: "LIF", Title: "process/input/lifecycle", Risks: []string{
		"natural exit zero", "expected nonzero exit", "unexpected exit code", "exit before readiness", "silent target input",
		"startup timeout", "total run timeout", "blocked input cancellation", "output flood", "runner interrupt", "hung descendant cleanup", "repeated session cleanup",
	}},
	{ID: "REN", Title: "render/readiness/resize", Risks: []string{
		"split UTF-8 sequence", "split CSI escape", "screen erase and home", "carriage-return redraw", "alternate-screen enter and leave", "stale positive text",
		"observed text disappearance", "delayed redraw readiness", "continuous repaint", "narrow viewport resize", "wide viewport resize", "supported Unicode width",
	}},
	{ID: "SNP", Title: "snapshots/suites", Risks: []string{
		"missing baseline", "oversized baseline", "readable mismatch diff", "targeted baseline update", "later-step rollback", "cancellation rollback", "unknown selector", "duplicate basename artifact isolation",
	}},
	{ID: "WSP", Title: "workspace/environment/filesystem", Risks: []string{
		"fresh fixture copy", "prior-state contamination", "escaping relative path", "fixture link or junction", "entry and byte bounds", "managed environment conflict", "setup cancellation", "retained failed state", "cleanup failure",
	}},
	{ID: "ART", Title: "reports/install/artifact handling", Risks: []string{
		"mixed report versions", "hostile report text", "missing evidence", "evidence path escape", "aggregate evidence limit", "atomic output preservation", "corrupt archive or checksum", "interrupted download",
	}},
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: go run ./scripts/corpus/generate-risk-map.go <output>")
		os.Exit(2)
	}
	doc := document{SchemaVersion: 1, FrozenOn: "2026-09-20"}
	for _, family := range families {
		for riskIndex, risk := range family.Risks {
			for layerIndex, layer := range layers {
				entry := riskCase{
					ID:     fmt.Sprintf("%s-%03d", family.ID, riskIndex*len(layers)+layerIndex+1),
					Family: family.Title,
					Risk:   risk,
					Layer:  layer,
					Status: "planned_gap",
					Gap:    "No reviewed focused case at this exact risk/layer boundary.",
				}
				if reference := reviewedReference(family.ID, riskIndex, layerIndex); reference != "" {
					entry.Status = "reviewed_existing"
					entry.Reference = reference
					entry.Gap = ""
				}
				doc.Cases = append(doc.Cases, entry)
			}
		}
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		panic(err)
	}
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(os.Args[1]), 0755); err != nil {
		panic(err)
	}
	if err := os.WriteFile(os.Args[1], data, 0644); err != nil {
		panic(err)
	}
}

// reviewedReference is intentionally explicit. A source file is attached only
// where its assertions were reviewed for this particular risk/layer cell.
func reviewedReference(family string, risk, layer int) string {
	switch family {
	case "VAL":
		if layer == 0 {
			return "internal/runner/runner_test.go"
		}
	case "LIF":
		if layer == 1 || layer == 2 {
			return "internal/runner/runner_test.go"
		}
	case "REN":
		if layer == 0 && risk < 6 {
			return "internal/runner/terminal_test.go"
		}
		if layer == 1 && risk >= 6 {
			return "internal/runner/runner_test.go"
		}
		if layer == 2 {
			return "internal/runner/runner_test.go"
		}
	case "SNP":
		if layer == 0 || layer == 1 {
			return "internal/runner/snapshot_test.go"
		}
	case "WSP":
		if layer == 0 && (risk == 2 || risk == 4 || risk == 5) {
			return "internal/runner/workspace_test.go"
		}
		if layer == 1 {
			return "internal/runner/workspace_test.go"
		}
		if layer == 2 && (risk == 3 || risk == 8) {
			return "internal/runner/workspace_windows_test.go"
		}
		if layer == 3 && (risk == 3 || risk == 8) {
			return "internal/runner/workspace_unix_test.go"
		}
	case "ART":
		if layer == 0 && risk < 6 {
			return "internal/report/html_test.go"
		}
		if layer == 1 && risk >= 6 {
			return "internal/setupaction/install_integration_test.go"
		}
	}
	return ""
}
