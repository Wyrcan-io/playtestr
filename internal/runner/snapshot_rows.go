package runner

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"strings"
)

// snapshotRows is an explicit versioned baseline format, independent of specs.
// A .rows.json file selects whole physical viewport rows, never inferred masks.
type snapshotRows struct {
	Version int    `json:"snapshot_version"`
	First   int    `json:"first_row"`
	Last    int    `json:"last_row"`
	Text    string `json:"text"`
}

func decodeSnapshotRows(data []byte) (snapshotRows, error) {
	var rows snapshotRows
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&rows); err != nil {
		return rows, fmt.Errorf("decode row snapshot: %w", err)
	}
	if err := decoder.Decode(new(any)); err != io.EOF {
		return rows, fmt.Errorf("row snapshot must contain exactly one JSON object")
	}
	if rows.Version != 1 {
		return rows, fmt.Errorf("unsupported row snapshot version %d", rows.Version)
	}
	if rows.First < 1 || rows.Last < rows.First || rows.Last > 500 {
		return rows, fmt.Errorf("row snapshot requires 1 <= first_row <= last_row <= 500")
	}
	if strings.TrimSpace(rows.Text) == "" {
		return rows, fmt.Errorf("row snapshot requires nonempty visible text")
	}
	if strings.Count(normalize(rows.Text), "\n") > rows.Last-rows.First+1 {
		return rows, fmt.Errorf("row snapshot text exceeds its selected row count")
	}
	return rows, nil
}

func (rows snapshotRows) capture(screen string, viewportRows int) (string, error) {
	if rows.First < 1 || rows.Last < rows.First || rows.Last > viewportRows {
		return "", fmt.Errorf("snapshot rows %d..%d exceed current %d-row viewport", rows.First, rows.Last, viewportRows)
	}
	lines := strings.Split(screen, "\n")
	for len(lines) < rows.Last {
		lines = append(lines, "")
	}
	text := normalize(strings.Join(lines[rows.First-1:rows.Last], "\n"))
	if strings.TrimSpace(text) == "" {
		return "", fmt.Errorf("row snapshot selects no visible content; choose meaningful rows")
	}
	return text, nil
}

func (rows snapshotRows) encode(text string) (string, error) {
	rows.Text = text
	data, err := json.MarshalIndent(rows, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data) + "\n", nil
}
