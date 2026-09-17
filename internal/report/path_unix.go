//go:build !windows

package report

import (
	"io/fs"
	"path/filepath"
)

func platformReparsePoint(fs.FileInfo) bool { return false }

func platformCanonicalExisting(path string) (string, error) {
	return filepath.EvalSymlinks(path)
}
