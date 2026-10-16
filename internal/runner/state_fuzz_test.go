package runner

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"path/filepath"
	"strings"
	"testing"
)

func FuzzStatePathContainment(f *testing.F) {
	for _, seed := range []string{"out/result.bin", "../escape", "C:stream", "CON.txt", "a/../b", "caf\u00e9 notes/file", ".", "a\\b", "COM\u00b9"} {
		f.Add(seed)
	}
	f.Fuzz(func(t *testing.T, path string) {
		if len(path) > 8192 {
			t.Skip()
		}
		if validateStatePath(path, true) != nil {
			return
		}
		native := filepath.FromSlash(path)
		if !filepath.IsLocal(native) || filepath.Clean(native) != native || strings.ContainsAny(path, "\\:\x00") {
			t.Fatal("accepted path is not a canonical local path")
		}
	})
}

func FuzzStateSpecRoundTrip(f *testing.F) {
	for _, seed := range []string{
		`{"version":3,"command":["must-not-launch"],"workspace":{"fixture":"fixture"},"steps":[{"expect":"ready"},{"state":{"path":"out.bin","kind":"file","bytes_base64":"AAENCg=="}}]}`,
		`{"version":3,"command":["must-not-launch"],"workspace":{"fixture":"fixture"},"steps":[{"expect":"ready"},{"state":{"path":".","kind":"entries","entries":[]}}]}`,
		`{"version":2,"command":["must-not-launch"],"steps":[{"state":{"path":"../escape","kind":"absent"}}]}`,
	} {
		f.Add([]byte(seed))
	}
	f.Fuzz(func(t *testing.T, data []byte) {
		if len(data) > 8192 {
			t.Skip()
		}
		spec, err := decodeSpec(data, "fuzz.json")
		if err != nil {
			return
		}
		encoded, err := json.Marshal(spec)
		if err != nil {
			t.Fatal(err)
		}
		again, err := decodeSpec(encoded, "fuzz.json")
		if err != nil {
			t.Fatalf("accepted spec cannot round trip: %v", err)
		}
		reencoded, err := json.Marshal(again)
		if err != nil || !bytes.Equal(encoded, reencoded) {
			t.Fatal("round trip changed accepted semantics")
		}
		for _, step := range again.Steps {
			if step.State == nil {
				continue
			}
			n, err := validateStateAssertion(*step.State)
			if err != nil {
				t.Fatal("accepted state assertion is invalid")
			}
			if step.State.Kind == "file" {
				payload, err := base64.StdEncoding.Strict().DecodeString(*step.State.BytesBase64)
				if err != nil || len(payload) != n || n > maxStateFileBytes {
					t.Fatal("accepted byte contract changed")
				}
			}
		}
	})
}
