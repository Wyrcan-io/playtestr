//go:build release_story_bad

package main

// reportedSize is the reviewed story defect: redraws report the stale viewport.
func reportedSize(_, _ int) (int, int) { return 60, 12 }
