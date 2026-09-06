package main

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
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
		"playtestr_0.1.0-rc.1_windows_amd64/playtestr.exe":          false,
		"playtestr_0.1.0-rc.1_windows_amd64/LICENSE":                false,
		"playtestr_0.1.0-rc.1_windows_amd64/README.md":              false,
		"playtestr_0.1.0-rc.1_windows_amd64/THIRD_PARTY_NOTICES.md": false,
	}
	for _, file := range archive.File {
		if _, ok := wanted[file.Name]; !ok {
			t.Errorf("archive contains unexpected member %s", file.Name)
			continue
		}
		wanted[file.Name] = true
		if file.FileInfo().Mode()&os.ModeType != 0 {
			t.Errorf("archive member %s is not a regular file", file.Name)
		}
		if strings.HasSuffix(file.Name, "playtestr.exe") && file.Mode().Perm() != 0755 {
			t.Errorf("binary mode = %o, want 755", file.Mode().Perm())
		}
	}
	for name, found := range wanted {
		if !found {
			t.Errorf("archive is missing %s", name)
		}
	}
	assertChecksum(t, archivePath)
}

func TestPackageReleaseCreatesTarWithExecutableMode(t *testing.T) {
	t.Chdir(filepath.Join("..", ".."))
	directory := t.TempDir()
	binary := filepath.Join(directory, "playtestr")
	if err := os.WriteFile(binary, []byte("test binary"), 0755); err != nil {
		t.Fatal(err)
	}
	if err := packageRelease(binary, "v0.1.0-rc.1", "linux", "amd64", directory); err != nil {
		t.Fatal(err)
	}
	archivePath := filepath.Join(directory, "playtestr_0.1.0-rc.1_linux_amd64.tar.gz")
	file, err := os.Open(archivePath)
	if err != nil {
		t.Fatal(err)
	}
	defer file.Close()
	compressed, err := gzip.NewReader(file)
	if err != nil {
		t.Fatal(err)
	}
	defer compressed.Close()
	archive := tar.NewReader(compressed)
	wanted := map[string]bool{
		"playtestr_0.1.0-rc.1_linux_amd64/playtestr":              false,
		"playtestr_0.1.0-rc.1_linux_amd64/LICENSE":                false,
		"playtestr_0.1.0-rc.1_linux_amd64/README.md":              false,
		"playtestr_0.1.0-rc.1_linux_amd64/THIRD_PARTY_NOTICES.md": false,
	}
	for {
		header, err := archive.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			t.Fatal(err)
		}
		if _, ok := wanted[header.Name]; !ok {
			t.Errorf("archive contains unexpected member %s", header.Name)
			continue
		}
		wanted[header.Name] = true
		if header.Typeflag != tar.TypeReg {
			t.Errorf("archive member %s is not a regular file", header.Name)
		}
		if strings.HasSuffix(header.Name, "/playtestr") && os.FileMode(header.Mode).Perm() != 0755 {
			t.Errorf("binary mode = %o, want 755", os.FileMode(header.Mode).Perm())
		}
	}
	for name, found := range wanted {
		if !found {
			t.Errorf("archive is missing %s", name)
		}
	}
	assertChecksum(t, archivePath)
}

func assertChecksum(t *testing.T, archivePath string) {
	t.Helper()
	data, err := os.ReadFile(archivePath)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(data)
	want := fmt.Sprintf("%x  %s\n", sum, filepath.Base(archivePath))
	got, err := os.ReadFile(archivePath + ".sha256")
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != want {
		t.Fatalf("checksum = %q, want %q", got, want)
	}
}
