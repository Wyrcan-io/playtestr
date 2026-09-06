// Command package-release creates one native Playtestr release archive.
package main

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"crypto/sha256"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var safeValue = regexp.MustCompile(`^[A-Za-z0-9._-]+$`)

type archiveFile struct {
	name string
	path string
	mode os.FileMode
}

func main() {
	binary := flag.String("binary", "", "path to the already-built native Playtestr binary")
	version := flag.String("version", "", "release version, for example v0.1.0-rc.1")
	targetOS := flag.String("os", "", "target operating system")
	arch := flag.String("arch", "", "target architecture")
	out := flag.String("out", "dist", "output directory")
	flag.Parse()
	if err := packageRelease(*binary, *version, *targetOS, *arch, *out); err != nil {
		fmt.Fprintln(os.Stderr, "package release:", err)
		os.Exit(1)
	}
}

func packageRelease(binary, version, targetOS, arch, out string) error {
	for name, value := range map[string]string{"version": version, "os": targetOS, "arch": arch} {
		if value == "" || !safeValue.MatchString(value) {
			return fmt.Errorf("%s must contain only letters, numbers, dots, underscores, or hyphens", name)
		}
	}
	if binary == "" {
		return fmt.Errorf("binary is required")
	}
	info, err := os.Stat(binary)
	if err != nil {
		return fmt.Errorf("open binary %s: %w", binary, err)
	}
	if info.IsDir() {
		return fmt.Errorf("binary is a directory: %s", binary)
	}
	if err := os.MkdirAll(out, 0755); err != nil {
		return fmt.Errorf("create output directory: %w", err)
	}
	base := fmt.Sprintf("playtestr_%s_%s_%s", strings.TrimPrefix(version, "v"), targetOS, arch)
	binaryName := "playtestr"
	if targetOS == "windows" {
		binaryName += ".exe"
	}
	files := []archiveFile{
		{name: filepath.ToSlash(filepath.Join(base, binaryName)), path: binary, mode: 0755},
		{name: filepath.ToSlash(filepath.Join(base, "LICENSE")), path: "LICENSE", mode: 0644},
		{name: filepath.ToSlash(filepath.Join(base, "README.md")), path: "README.md", mode: 0644},
	}
	extension := ".tar.gz"
	if targetOS == "windows" {
		extension = ".zip"
	}
	archivePath := filepath.Join(out, base+extension)
	if targetOS == "windows" {
		if err := writeZip(archivePath, files); err != nil {
			return err
		}
	} else if err := writeTarGzip(archivePath, files); err != nil {
		return err
	}
	data, err := os.ReadFile(archivePath)
	if err != nil {
		return fmt.Errorf("read archive for checksum: %w", err)
	}
	sum := sha256.Sum256(data)
	checksum := fmt.Sprintf("%x  %s\n", sum, filepath.Base(archivePath))
	if err := os.WriteFile(archivePath+".sha256", []byte(checksum), 0644); err != nil {
		return fmt.Errorf("write checksum: %w", err)
	}
	fmt.Println(archivePath)
	fmt.Println(archivePath + ".sha256")
	return nil
}

func writeZip(path string, files []archiveFile) (returnErr error) {
	output, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create zip: %w", err)
	}
	defer func() {
		if err := output.Close(); returnErr == nil && err != nil {
			returnErr = fmt.Errorf("close zip: %w", err)
		}
	}()
	archive := zip.NewWriter(output)
	for _, file := range files {
		data, err := os.ReadFile(file.path)
		if err != nil {
			_ = archive.Close()
			return fmt.Errorf("read archive input %s: %w", file.path, err)
		}
		header := &zip.FileHeader{Name: file.name, Method: zip.Deflate}
		header.SetMode(file.mode)
		entry, err := archive.CreateHeader(header)
		if err != nil {
			_ = archive.Close()
			return fmt.Errorf("create zip entry: %w", err)
		}
		if _, err := entry.Write(data); err != nil {
			_ = archive.Close()
			return fmt.Errorf("write zip entry: %w", err)
		}
	}
	if err := archive.Close(); err != nil {
		return fmt.Errorf("finish zip: %w", err)
	}
	return nil
}

func writeTarGzip(path string, files []archiveFile) (returnErr error) {
	output, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("create tarball: %w", err)
	}
	defer func() {
		if err := output.Close(); returnErr == nil && err != nil {
			returnErr = fmt.Errorf("close tarball: %w", err)
		}
	}()
	compressed := gzip.NewWriter(output)
	archive := tar.NewWriter(compressed)
	for _, file := range files {
		input, err := os.Open(file.path)
		if err != nil {
			return fmt.Errorf("open archive input %s: %w", file.path, err)
		}
		info, err := input.Stat()
		if err != nil {
			_ = input.Close()
			return fmt.Errorf("stat archive input %s: %w", file.path, err)
		}
		header := &tar.Header{Name: file.name, Mode: int64(file.mode.Perm()), Size: info.Size()}
		if err := archive.WriteHeader(header); err != nil {
			_ = input.Close()
			return fmt.Errorf("write tar header: %w", err)
		}
		if _, err := io.Copy(archive, input); err != nil {
			_ = input.Close()
			return fmt.Errorf("write tar entry: %w", err)
		}
		if err := input.Close(); err != nil {
			return fmt.Errorf("close archive input: %w", err)
		}
	}
	if err := archive.Close(); err != nil {
		return fmt.Errorf("finish tar: %w", err)
	}
	if err := compressed.Close(); err != nil {
		return fmt.Errorf("finish gzip: %w", err)
	}
	return nil
}
