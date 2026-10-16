package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
)

// OpenRecording opens an existing reviewed spec for explicit selected maintenance.
// Its approved files remain unchanged until review, successful fresh replay and save.
func OpenRecording(ctx context.Context, path string) (*Recording, error) {
	absolute, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	absolute, err = canonicalRecordPath(absolute)
	if err != nil {
		return nil, err
	}
	if err := safeRecordPath(absolute); err != nil {
		return nil, err
	}
	spec, err := Load(absolute)
	if err != nil {
		return nil, err
	}
	file, err := os.Open(absolute)
	if err != nil {
		return nil, err
	}
	original, err := io.ReadAll(io.LimitReader(file, maxSpecBytes+1))
	file.Close()
	if err != nil || len(original) > maxSpecBytes {
		return nil, fmt.Errorf("cannot read bounded original specification")
	}
	snapshots := map[string]string{}
	total := 0
	for _, step := range spec.Steps {
		if step.Snapshot == "" {
			continue
		}
		snapshotPath := filepath.Join(filepath.Dir(absolute), "snapshots", step.Snapshot)
		if err := safeRecordPath(snapshotPath); err != nil {
			return nil, err
		}
		content, err := readSnapshot(snapshotPath)
		if err != nil {
			return nil, fmt.Errorf("load reviewed snapshot: %w", err)
		}
		total += len(content)
		if total > maxStagedSnapshotBytes {
			return nil, fmt.Errorf("reviewed snapshots exceed aggregate limit")
		}
		snapshots[step.Snapshot] = string(content)
	}
	r, err := StartRecording(ctx, absolute, spec)
	if err != nil {
		return nil, err
	}
	r.spec = spec
	r.snapshots = snapshots
	r.snapshotBytes = total
	r.maintenanceOriginal = original
	r.maintenanceSnapshots = make(map[string]string, len(snapshots))
	for name, content := range snapshots {
		r.maintenanceSnapshots[name] = content
	}
	return r, nil
}

// UpdateStateStep reconstructs the prefix in fresh state, recaptures only one
// existing state expectation, and retains the complete unrelated suffix.
func (r *Recording) UpdateStateStep(ctx context.Context, number int) (returnErr error) {
	if number < 1 || number > len(r.spec.Steps) || r.spec.Steps[number-1].State == nil {
		return fmt.Errorf("select an existing state step")
	}
	steps := r.Steps()
	snapshots := make(map[string]string, len(r.snapshots))
	for name, content := range r.snapshots {
		snapshots[name] = content
	}
	defer func() {
		r.snapshots = snapshots
		r.snapshotBytes = 0
		for _, content := range snapshots {
			r.snapshotBytes += len(content)
		}
		if returnErr != nil {
			r.spec.Steps = steps
			r.replayed = false
		}
	}()
	selected := steps[number-1].State
	if err := r.Rerecord(ctx, number-1); err != nil {
		return err
	}
	if err := r.CaptureState(selected.Path, selected.Kind); err != nil {
		return err
	}
	replacement := r.Steps()[number-1]
	steps[number-1] = replacement
	r.spec.Steps = steps
	r.replayed = false
	return nil
}

func (r *Recording) exportMaintenance(ctx context.Context, data []byte, snapshots map[string]string) error {
	// Existing screen files are deliberately maintained by the public selected
	// snapshot-update command. File expectation maintenance commits one spec only.
	if len(snapshots) != len(r.maintenanceSnapshots) {
		return fmt.Errorf("screen changes require a selected test --update --snapshot or a new recording")
	}
	for name, content := range snapshots {
		if original, ok := r.maintenanceSnapshots[name]; !ok || content != original {
			return fmt.Errorf("screen changes require a selected test --update --snapshot")
		}
		path := filepath.Join(filepath.Dir(r.path), "snapshots", name)
		if err := safeRecordPath(path); err != nil {
			return err
		}
		observed, err := readSnapshot(path)
		if err != nil || !bytes.Equal(observed, []byte(content)) {
			return fmt.Errorf("approved screen changed during maintenance; reopen the recording")
		}
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if err := safeRecordPath(r.path); err != nil {
		return err
	}
	file, err := os.Open(r.path)
	if err != nil {
		return err
	}
	current, err := io.ReadAll(io.LimitReader(file, maxSpecBytes+1))
	file.Close()
	if err != nil || !bytes.Equal(current, r.maintenanceOriginal) {
		return fmt.Errorf("approved specification changed during maintenance; reopen it")
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	data, err = preserveUnchangedSpecBytes(r.maintenanceOriginal, r.spec.Steps, data)
	if err != nil {
		return err
	}
	if err := writeFileAtomic(r.path, data, 0644); err != nil {
		return fmt.Errorf("save reviewed state maintenance: %w", err)
	}
	r.maintenanceOriginal = append([]byte(nil), data...)
	return nil
}

// Retain the exact original spelling/whitespace of every unchanged step and
// top-level field during selected maintenance. No unrelated JSON is regenerated.
func preserveUnchangedSpecBytes(original []byte, steps []Step, fallback []byte) ([]byte, error) {
	var old Spec
	if err := json.Unmarshal(bytes.TrimPrefix(original, []byte{0xef, 0xbb, 0xbf}), &old); err != nil {
		return nil, err
	}
	if len(old.Steps) != len(steps) {
		return fallback, nil
	}
	decoder := json.NewDecoder(bytes.NewReader(bytes.TrimPrefix(original, []byte{0xef, 0xbb, 0xbf})))
	prefix := len(original) - len(bytes.TrimPrefix(original, []byte{0xef, 0xbb, 0xbf}))
	if _, err := decoder.Token(); err != nil {
		return nil, err
	}
	start := -1
	var raw json.RawMessage
	for decoder.More() {
		key, err := decoder.Token()
		if err != nil {
			return nil, err
		}
		var value json.RawMessage
		if err := decoder.Decode(&value); err != nil {
			return nil, err
		}
		if key == "steps" {
			if start >= 0 {
				return nil, fmt.Errorf("ambiguous duplicate steps field")
			}
			raw = value
			start = prefix + int(decoder.InputOffset()) - len(raw)
		}
	}
	if start < 0 {
		return nil, fmt.Errorf("missing original steps")
	}
	array := json.NewDecoder(bytes.NewReader(raw))
	if _, err := array.Token(); err != nil {
		return nil, err
	}
	var output bytes.Buffer
	copied := 0
	for i := 0; array.More(); i++ {
		var step json.RawMessage
		if err := array.Decode(&step); err != nil {
			return nil, err
		}
		if reflect.DeepEqual(old.Steps[i], steps[i]) {
			continue
		}
		end := start + int(array.InputOffset())
		begin := end - len(step)
		output.Write(original[copied:begin])
		replacement, err := json.Marshal(steps[i])
		if err != nil {
			return nil, err
		}
		output.Write(replacement)
		copied = end
	}
	output.Write(original[copied:])
	return output.Bytes(), nil
}
