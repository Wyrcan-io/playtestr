package runner

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
)

func (r *Recording) captureOutcome(step Step, err error) {
	// Retrying the same selected path resolves that path's capture failure; a
	// successful unrelated checkpoint cannot silently discard a failed request.
	if step.State != nil {
		step = Step{State: &StateAssertion{Path: step.State.Path, Kind: step.State.Kind}}
	}
	data, _ := json.Marshal(step)
	key := sha256.Sum256(data)
	if err == nil {
		delete(r.pendingCaptureErrors, key)
		return
	}
	r.replayed = false
	if r.pendingCaptureErrors == nil {
		r.pendingCaptureErrors = make(map[[32]byte]struct{})
	}
	if len(r.pendingCaptureErrors) >= 100 {
		r.pendingCaptureOverflow = true
		return
	}
	r.pendingCaptureErrors[key] = struct{}{}
}

// DiscardCaptureErrors explicitly omits failed requested controls. It never
// approves an expectation and still requires completion, review and fresh replay.
func (r *Recording) DiscardCaptureErrors() {
	r.pendingCaptureErrors = nil
	r.pendingCaptureOverflow = false
	r.replayed = false
}

func (r *Recording) validateCompletion() error {
	if len(r.pendingCaptureErrors) > 0 || r.pendingCaptureOverflow {
		return fmt.Errorf("unresolved capture failures: retry each failed control, rerecord, or explicitly /discard-errors before review and fresh replay")
	}
	ready := false
	for _, step := range r.spec.Steps {
		switch {
		case step.Key != "" || step.Text != "" || step.Resize != nil || step.WaitForRedraw:
			ready = false
		case step.Expect != "" || step.ExpectNot != "" || step.Exit != nil:
			ready = true
		}
	}
	if !ready {
		return fmt.Errorf("recording requires a positive completion checkpoint after its last input or resize; add /expect, /absent or /exit before review and replay")
	}
	return nil
}
