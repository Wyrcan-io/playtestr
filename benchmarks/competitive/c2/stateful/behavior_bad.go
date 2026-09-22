//go:build competitive_bad

package main

// committedPort is the reviewed C2 mutation: success names the new value, but
// persistence incorrectly retains the old value.
func committedPort(_ int) int { return 8080 }
