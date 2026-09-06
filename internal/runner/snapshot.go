package runner

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"unicode/utf8"
)

const (
	maxSnapshotBytes = 2_000_000
	maxSnapshotLines = 10_000
	maxDiffBytes     = 256 * 1024
)

type snapshotUpdates map[string]string

type snapshotMismatchError struct {
	name   string
	actual string
	diff   string
}

func (e *snapshotMismatchError) Error() string {
	return fmt.Sprintf("snapshot %q did not match\n%s", e.name, e.diff)
}

func newSnapshotMismatch(name, expected, actual string) error {
	return &snapshotMismatchError{
		name:   name,
		actual: actual,
		diff:   unifiedTextDiff(name, expected, actual),
	}
}

func readSnapshot(path string) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, maxSnapshotBytes+1))
	if err != nil {
		return nil, err
	}
	if len(data) > maxSnapshotBytes {
		return nil, fmt.Errorf("snapshot exceeds %d bytes", maxSnapshotBytes)
	}
	if bytes.Count(data, []byte{'\n'})+1 > maxSnapshotLines {
		return nil, fmt.Errorf("snapshot exceeds %d lines", maxSnapshotLines)
	}
	if !utf8.Valid(data) {
		return nil, fmt.Errorf("snapshot is not valid UTF-8")
	}
	return data, nil
}

func commitSnapshotUpdates(updates snapshotUpdates, out io.Writer) error {
	paths := make([]string, 0, len(updates))
	for path := range updates {
		paths = append(paths, path)
	}
	sort.Strings(paths)
	for _, path := range paths {
		content := []byte(updates[path])
		current, err := readSnapshot(path)
		status := "updated"
		switch {
		case err == nil && bytes.Equal(current, content):
			fmt.Fprintf(out, "Snapshot unchanged: %s\n", path)
			continue
		case err == nil:
		case errors.Is(err, os.ErrNotExist):
			status = "created"
		default:
			return fmt.Errorf("read existing snapshot %s: %w", path, err)
		}
		if err := writeFileAtomic(path, content, 0644); err != nil {
			return err
		}
		fmt.Fprintf(out, "Snapshot %s: %s\n", status, path)
	}
	return nil
}

func writeFileAtomic(path string, data []byte, mode os.FileMode) (returnErr error) {
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return fmt.Errorf("create snapshot directory: %w", err)
	}
	temporary, err := os.CreateTemp(filepath.Dir(path), ".playtestr-snapshot-*")
	if err != nil {
		return fmt.Errorf("create temporary snapshot: %w", err)
	}
	temporaryPath := temporary.Name()
	defer func() {
		_ = temporary.Close()
		_ = os.Remove(temporaryPath)
	}()
	if err := temporary.Chmod(mode); err != nil {
		return fmt.Errorf("set temporary snapshot permissions: %w", err)
	}
	if _, err := temporary.Write(data); err != nil {
		return fmt.Errorf("write temporary snapshot: %w", err)
	}
	if err := temporary.Sync(); err != nil {
		return fmt.Errorf("sync temporary snapshot: %w", err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close temporary snapshot: %w", err)
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return fmt.Errorf("replace snapshot %s: %w", path, err)
	}
	return nil
}

type diffLine struct {
	kind byte
	text string
}

func unifiedTextDiff(name, expected, actual string) string {
	oldLines := snapshotLines(expected)
	newLines := snapshotLines(actual)
	ops := lineDiff(oldLines, newLines)
	ranges := diffRanges(ops, 3)
	var result strings.Builder
	fmt.Fprintf(&result, "--- expected: %s\n+++ actual: %s\n", name, name)
	for _, change := range ranges {
		oldStart, newStart := diffPosition(ops, change[0])
		oldCount, newCount := diffCounts(ops[change[0]:change[1]])
		fmt.Fprintf(&result, "@@ -%d,%d +%d,%d @@\n", oldStart, oldCount, newStart, newCount)
		for _, line := range ops[change[0]:change[1]] {
			result.WriteByte(line.kind)
			result.WriteString(line.text)
			result.WriteByte('\n')
		}
	}
	return boundText(result.String(), maxDiffBytes)
}

func snapshotLines(value string) []string {
	if strings.HasSuffix(value, "\n") {
		value = strings.TrimSuffix(value, "\n")
	}
	return strings.Split(value, "\n")
}

func lineDiff(oldLines, newLines []string) []diffLine {
	rows := len(oldLines) + 1
	cols := len(newLines) + 1
	lcs := make([]int, rows*cols)
	for oldIndex := len(oldLines) - 1; oldIndex >= 0; oldIndex-- {
		for newIndex := len(newLines) - 1; newIndex >= 0; newIndex-- {
			position := oldIndex*cols + newIndex
			if oldLines[oldIndex] == newLines[newIndex] {
				lcs[position] = lcs[(oldIndex+1)*cols+newIndex+1] + 1
			} else {
				lcs[position] = max(lcs[(oldIndex+1)*cols+newIndex], lcs[oldIndex*cols+newIndex+1])
			}
		}
	}
	result := make([]diffLine, 0, len(oldLines)+len(newLines))
	oldIndex, newIndex := 0, 0
	for oldIndex < len(oldLines) && newIndex < len(newLines) {
		switch {
		case oldLines[oldIndex] == newLines[newIndex]:
			result = append(result, diffLine{' ', oldLines[oldIndex]})
			oldIndex++
			newIndex++
		case lcs[(oldIndex+1)*cols+newIndex] >= lcs[oldIndex*cols+newIndex+1]:
			result = append(result, diffLine{'-', oldLines[oldIndex]})
			oldIndex++
		default:
			result = append(result, diffLine{'+', newLines[newIndex]})
			newIndex++
		}
	}
	for ; oldIndex < len(oldLines); oldIndex++ {
		result = append(result, diffLine{'-', oldLines[oldIndex]})
	}
	for ; newIndex < len(newLines); newIndex++ {
		result = append(result, diffLine{'+', newLines[newIndex]})
	}
	return result
}

func diffRanges(lines []diffLine, contextLines int) [][2]int {
	var ranges [][2]int
	for index, line := range lines {
		if line.kind == ' ' {
			continue
		}
		start := max(0, index-contextLines)
		end := min(len(lines), index+contextLines+1)
		if len(ranges) > 0 && start <= ranges[len(ranges)-1][1] {
			ranges[len(ranges)-1][1] = end
		} else {
			ranges = append(ranges, [2]int{start, end})
		}
	}
	return ranges
}

func diffPosition(lines []diffLine, end int) (oldLine, newLine int) {
	oldLine, newLine = 1, 1
	for _, line := range lines[:end] {
		if line.kind != '+' {
			oldLine++
		}
		if line.kind != '-' {
			newLine++
		}
	}
	return oldLine, newLine
}

func diffCounts(lines []diffLine) (oldCount, newCount int) {
	for _, line := range lines {
		if line.kind != '+' {
			oldCount++
		}
		if line.kind != '-' {
			newCount++
		}
	}
	return oldCount, newCount
}

func boundText(value string, limit int) string {
	if len(value) <= limit {
		return value
	}
	end := limit
	for end > 0 && !utf8.RuneStart(value[end]) {
		end--
	}
	return value[:end] + "\n... diff truncated by Playtestr ...\n"
}
