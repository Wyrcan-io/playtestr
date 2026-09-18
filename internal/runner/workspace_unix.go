//go:build !windows

package runner

func workspaceReparsePoint(string) bool { return false }
