//go:build !windows

package report

import "io/fs"

func platformReparsePoint(fs.FileInfo) bool { return false }
