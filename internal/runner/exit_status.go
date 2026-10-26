package runner

// MaxNativeExitCode bounds a captured native status, including Windows DWORD
// termination and exception values. Unix signal statuses remain 128 + signal.
const MaxNativeExitCode uint64 = 1<<32 - 1
