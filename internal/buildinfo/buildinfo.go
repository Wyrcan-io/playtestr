// Package buildinfo contains values injected into release binaries.
package buildinfo

// Version is overridden with -ldflags for release builds.
var Version = "dev"
