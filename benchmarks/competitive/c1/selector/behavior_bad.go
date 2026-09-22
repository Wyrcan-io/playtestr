//go:build competitive_bad

package main

// commitSelection is the reviewed C1 mutation: the cursor may move, but
// confirmation incorrectly commits the first record.
func commitSelection(_ int) int {
	return 0
}
