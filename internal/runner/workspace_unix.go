//go:build !windows

package runner

func workspaceReparsePoint(string) bool { return false }

func canonicalWorkspaceRoot(path string) (string, error) { return path, nil }

func hideWorkspaceMarker(string) error { return nil }
