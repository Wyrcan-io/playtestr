package main

import (
	"archive/zip"
	"os"
	"path/filepath"
	"testing"
)

func TestPackageReleaseCreatesArchiveAndChecksum(t *testing.T) {
	t.Chdir(filepath.Join("..", ".."))
	directory := t.TempDir()
	binary := filepath.Join(directory, "playtestr.exe")
	if err := os.WriteFile(binary, []byte("test binary"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := packageRelease(binary, "v0.1.0-rc.1", "windows", "amd64", directory); err != nil {
		t.Fatal(err)
	}
	archivePath := filepath.Join(directory, "playtestr_0.1.0-rc.1_windows_amd64.zip")
	archive, err := zip.OpenReader(archivePath)
	if err != nil {
		t.Fatal(err)
	}
	defer archive.Close()
	wanted := map[string]bool{
		"playtestr_0.1.0-rc.1_windows_amd64/playtestr.exe": false,
		"playtestr_0.1.0-rc.1_windows_amd64/LICENSE":       false,
		"playtestr_0.1.0-rc.1_windows_amd64/README.md":     false,
	}
	for _, file := range archive.File {
		if _, ok := wanted[file.Name]; ok {
			wanted[file.Name] = true
		}
	}
	for name, found := range wanted {
		if !found {
			t.Errorf("archive is missing %s", name)
		}
	}
	if _, err := os.Stat(archivePath + ".sha256"); err != nil {
		t.Fatal(err)
	}
}
