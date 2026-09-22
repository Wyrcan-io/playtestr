//go:build competitive_bad && !windows

package main

// modalAfterDismiss is the reviewed C3 mutation: Escape redraws but leaves the
// modal visible after resize.
func modalAfterDismiss(modal bool) bool { return modal }
