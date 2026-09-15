package discovery

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func touch(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte("{}"), 0644); err != nil {
		t.Fatal(err)
	}
}

func TestResolveExpansionOrderDedupAndExclusions(t *testing.T) {
	root := t.TempDir()
	a := filepath.Join(root, "a.json")
	b := filepath.Join(root, "nested", "b.json")
	touch(t, b)
	touch(t, a)
	touch(t, filepath.Join(root, "notes.txt"))
	touch(t, filepath.Join(root, "artifacts", "old.json"))

	got, err := Resolve([]string{b, root, a})
	if err != nil {
		t.Fatal(err)
	}
	want := []string{b, a}
	if len(got) != len(want) {
		t.Fatalf("selected %v, want %v", got, want)
	}
	for i := range want {
		if got[i].Path != want[i] {
			t.Fatalf("selected[%d] = %q, want %q", i, got[i].Path, want[i])
		}
	}
}

func TestResolveDeduplicatesHardLinks(t *testing.T) {
	root := t.TempDir()
	original := filepath.Join(root, "original.json")
	alias := filepath.Join(root, "alias.json")
	touch(t, original)
	if err := os.Link(original, alias); err != nil {
		t.Skipf("hard links unavailable: %v", err)
	}
	got, err := Resolve([]string{alias, original})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Path != alias {
		t.Fatalf("selected = %+v", got)
	}
}

func TestResolveEmptyAndDirectoryErrors(t *testing.T) {
	empty := t.TempDir()
	for _, input := range []string{empty, filepath.Join(empty, "missing")} {
		_, err := Resolve([]string{input})
		if err == nil {
			t.Fatalf("Resolve(%q) succeeded", input)
		}
	}
}

func TestResolveUnreadableDirectory(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("portable Windows ACL mutation is outside this unit test")
	}
	root := t.TempDir()
	blocked := filepath.Join(root, "blocked")
	if err := os.Mkdir(blocked, 0700); err != nil {
		t.Fatal(err)
	}
	touch(t, filepath.Join(blocked, "spec.json"))
	if err := os.Chmod(blocked, 0000); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chmod(blocked, 0700) })
	if _, err := Resolve([]string{blocked}); err == nil {
		if os.Geteuid() == 0 {
			t.Skip("root can read the permission fixture")
		}
		t.Fatal("unreadable directory was accepted")
	}
}

func TestResolveLimits(t *testing.T) {
	root := t.TempDir()
	touch(t, filepath.Join(root, "one.json"))
	touch(t, filepath.Join(root, "two.json"))
	if _, err := resolve([]string{root}, nil, 1, 10); err == nil || !strings.Contains(err.Error(), "visited entries") {
		t.Fatalf("visit limit error = %v", err)
	}
	if _, err := resolve([]string{root}, nil, 10, 1); err == nil || !strings.Contains(err.Error(), "selection") {
		t.Fatalf("selection limit error = %v", err)
	}
}

func TestResolveExcludesConfiguredOutputTree(t *testing.T) {
	root := t.TempDir()
	touch(t, filepath.Join(root, "suite.json"))
	output := filepath.Join(root, "ci-output")
	touch(t, filepath.Join(output, "old-report.json"))
	got, err := ResolveExcluding([]string{root}, []string{output})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || filepath.Base(got[0].Path) != "suite.json" {
		t.Fatalf("selected = %+v", got)
	}
}

func TestResolveDoesNotFollowDirectorySymlinks(t *testing.T) {
	root := t.TempDir()
	external := t.TempDir()
	touch(t, filepath.Join(external, "outside.json"))
	if err := os.Symlink(external, filepath.Join(root, "linked")); err != nil {
		if runtime.GOOS == "windows" {
			t.Skip("creating symlinks requires Windows developer mode or elevation")
		}
		t.Fatal(err)
	}
	touch(t, filepath.Join(root, "inside.json"))
	got, err := Resolve([]string{root})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || filepath.Base(got[0].Path) != "inside.json" {
		t.Fatalf("selected = %+v", got)
	}
}

func TestResolveCaseBehaviorMatchesHost(t *testing.T) {
	root := t.TempDir()
	upper := filepath.Join(root, "Case.json")
	lower := filepath.Join(root, "case.json")
	touch(t, upper)
	if runtime.GOOS != "windows" {
		touch(t, lower)
	}
	got, err := Resolve([]string{root})
	if err != nil {
		t.Fatal(err)
	}
	want := 1
	if upperInfo, upperErr := os.Stat(upper); upperErr == nil {
		if lowerInfo, lowerErr := os.Stat(lower); lowerErr == nil && !os.SameFile(upperInfo, lowerInfo) {
			want = 2
		}
	}
	if len(got) != want {
		t.Fatalf("selected %d specs, want %d", len(got), want)
	}
}

func TestResolveWindowsSeparators(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Windows path syntax")
	}
	root := t.TempDir()
	path := filepath.Join(root, "nested", "spec.json")
	touch(t, path)
	windowsPath := strings.ReplaceAll(path, "/", `\`)
	got, err := Resolve([]string{windowsPath})
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 1 || got[0].Path != filepath.Clean(windowsPath) {
		t.Fatalf("selected = %+v", got)
	}
}
