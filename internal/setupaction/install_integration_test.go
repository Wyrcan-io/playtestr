package setupaction_test

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"testing"
	"time"
)

const testVersion = "v9.8.7"

func TestMain(m *testing.M) {
	if os.Getenv("PLAYTESTR_SETUP_FIXTURE") == "1" && len(os.Args) == 2 && os.Args[1] == "--version" {
		fmt.Println("playtestr " + testVersion)
		os.Exit(0)
	}
	os.Exit(m.Run())
}

func TestSetupActionInstallsVerifiedBinaryAndOverridesStalePath(t *testing.T) {
	requireSupportedHost(t)
	releaseDir := makeRelease(t, nil)
	root := filepath.Join(t.TempDir(), "installation root with spaces")
	output := filepath.Join(t.TempDir(), "github output")
	pathOutput := filepath.Join(t.TempDir(), "github path")

	result := runInstaller(t, "-Version", testVersion, "-InstallRoot", root,
		"-DownloadDirectory", releaseDir, "-OutputFile", output, "-PathFile", pathOutput)
	if result.err != nil {
		t.Fatalf("installer failed: %v\n%s", result.err, result.output)
	}
	values := readEnvironmentFile(t, output)
	if values["version"] != testVersion {
		t.Fatalf("version output = %q", values["version"])
	}
	binaryPath := values["binary-path"]
	installDir := values["install-dir"]
	wantBinaryHash := sha256.Sum256(releaseBinary(t))
	if values["binary-sha256"] != fmt.Sprintf("%x", wantBinaryHash) {
		t.Fatalf("binary hash = %q, want %x", values["binary-sha256"], wantBinaryHash)
	}
	archiveData, err := os.ReadFile(filepath.Join(releaseDir, releaseArchiveName()))
	if err != nil {
		t.Fatal(err)
	}
	wantArchiveHash := sha256.Sum256(archiveData)
	if values["archive-sha256"] != fmt.Sprintf("%x", wantArchiveHash) {
		t.Fatalf("archive hash = %q, want %x", values["archive-sha256"], wantArchiveHash)
	}
	if !filepath.IsAbs(binaryPath) || filepath.Dir(binaryPath) != installDir {
		t.Fatalf("invalid action paths: binary=%q dir=%q", binaryPath, installDir)
	}
	if got := strings.TrimSpace(runCommand(t, binaryPath, "--version")); got != "playtestr "+testVersion {
		t.Fatalf("installed version = %q", got)
	}
	pathLine, err := os.ReadFile(pathOutput)
	if err != nil {
		t.Fatal(err)
	}
	if strings.TrimSpace(string(pathLine)) != installDir {
		t.Fatalf("GITHUB_PATH = %q, want %q", strings.TrimSpace(string(pathLine)), installDir)
	}

	staleDir := t.TempDir()
	staleName := "playtestr"
	if runtime.GOOS == "windows" {
		staleName += ".exe"
	}
	if err := os.WriteFile(filepath.Join(staleDir, staleName), []byte("stale executable"), 0755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", installDir+string(os.PathListSeparator)+staleDir+string(os.PathListSeparator)+os.Getenv("PATH"))
	resolved, err := exec.LookPath("playtestr")
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Clean(resolved) != filepath.Clean(binaryPath) {
		t.Fatalf("PATH resolved %q, want verified binary %q", resolved, binaryPath)
	}
	entries, err := os.ReadDir(root)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1 || strings.HasPrefix(entries[0].Name(), ".staging-") {
		t.Fatalf("install root contains unexpected entries: %v", entries)
	}
}

func TestSetupActionRejectsUnsafeOrUnverifiedInputs(t *testing.T) {
	requireSupportedHost(t)
	tests := []struct {
		name    string
		prepare func(*testing.T) string
		args    []string
		want    string
	}{
		{
			name:    "missing release",
			prepare: func(t *testing.T) string { return t.TempDir() },
			want:    "Cannot find path",
		},
		{
			name: "wrong checksum",
			prepare: func(t *testing.T) string {
				dir := makeRelease(t, nil)
				archive := releaseArchiveName()
				if err := os.WriteFile(filepath.Join(dir, archive+".sha256"), []byte(strings.Repeat("0", 64)+"  "+archive+"\n"), 0644); err != nil {
					t.Fatal(err)
				}
				return dir
			},
			want: "checksum mismatch",
		},
		{
			name: "corrupt archive with matching checksum",
			prepare: func(t *testing.T) string {
				dir := makeRelease(t, nil)
				archivePath := filepath.Join(dir, releaseArchiveName())
				if err := os.WriteFile(archivePath, []byte("not an archive"), 0644); err != nil {
					t.Fatal(err)
				}
				writeChecksum(t, archivePath)
				return dir
			},
			want: "cannot inspect release archive",
		},
		{
			name: "escaping archive member",
			prepare: func(t *testing.T) string {
				return makeRelease(t, map[string][]byte{"../escaped": []byte("escape")})
			},
			want: "archive members do not match",
		},
		{
			name:    "missing executable member",
			prepare: makeReleaseWithoutExecutable,
			want:    "archive members do not match",
		},
		{
			name:    "unsupported architecture",
			prepare: func(t *testing.T) string { return makeRelease(t, nil) },
			args:    []string{"-TargetOS", "linux", "-TargetArch", "arm64"},
			want:    "unsupported Playtestr release target",
		},
		{
			name:    "non-exact version",
			prepare: func(t *testing.T) string { return makeRelease(t, nil) },
			args:    []string{"-Version", "latest"},
			want:    "version must be an exact release",
		},
		{
			name:    "supported but non-native platform",
			prepare: func(t *testing.T) string { return makeRelease(t, nil) },
			args:    wrongNativeTarget(),
			want:    "does not match native host",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			directory := tt.prepare(t)
			root := filepath.Join(t.TempDir(), "failed install root")
			output := filepath.Join(t.TempDir(), "github-output")
			pathOutput := filepath.Join(t.TempDir(), "github-path")
			args := []string{"-Version", testVersion, "-InstallRoot", root, "-DownloadDirectory", directory, "-OutputFile", output, "-PathFile", pathOutput}
			if len(tt.args) > 0 {
				for i := 0; i < len(tt.args); i += 2 {
					for j := 0; j < len(args); j += 2 {
						if args[j] == tt.args[i] {
							args = append(args[:j], args[j+2:]...)
							break
						}
					}
					args = append(args, tt.args[i], tt.args[i+1])
				}
			}
			result := runInstaller(t, args...)
			if result.err == nil || !strings.Contains(result.output, tt.want) {
				t.Fatalf("error = %v, output = %q, want failure containing %q", result.err, result.output, tt.want)
			}
			assertNotExposed(t, root, output, pathOutput)
		})
	}
}

func TestSetupActionDownloadsVerifiedArchiveAndRunsOffline(t *testing.T) {
	requireSupportedHost(t)
	releaseDir := makeRelease(t, nil)
	server := httptest.NewServer(http.StripPrefix("/"+testVersion+"/", http.FileServer(http.Dir(releaseDir))))

	root := filepath.Join(t.TempDir(), "downloaded installation with spaces")
	output := filepath.Join(t.TempDir(), "github-output")
	pathOutput := filepath.Join(t.TempDir(), "github-path")
	result := runInstaller(t, "-Version", testVersion, "-InstallRoot", root,
		"-DownloadBaseUrl", server.URL, "-DownloadAttempts", "1",
		"-OutputFile", output, "-PathFile", pathOutput)
	server.Close()
	if result.err != nil {
		t.Fatalf("network installer failed: %v\n%s", result.err, result.output)
	}
	values := readEnvironmentFile(t, output)
	if got := strings.TrimSpace(runCommand(t, values["binary-path"], "--version")); got != "playtestr "+testVersion {
		t.Fatalf("offline installed version = %q", got)
	}
}

func TestSetupActionRejectsPartialAndOversizedDownloads(t *testing.T) {
	requireSupportedHost(t)
	tests := []struct {
		name    string
		handler http.HandlerFunc
		want    string
	}{
		{
			name: "partial response",
			handler: func(w http.ResponseWriter, r *http.Request) {
				hijacker, ok := w.(http.Hijacker)
				if !ok {
					t.Error("HTTP server does not support hijacking")
					return
				}
				connection, buffer, err := hijacker.Hijack()
				if err != nil {
					t.Error(err)
					return
				}
				_, _ = buffer.WriteString("HTTP/1.1 200 OK\r\nContent-Length: 1024\r\n\r\npartial")
				_ = buffer.Flush()
				_ = connection.Close()
			},
			want: "failed after 1 attempts",
		},
		{
			name: "oversized response",
			handler: func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Length", fmt.Sprint(64*1024*1024+1))
				w.WriteHeader(http.StatusOK)
			},
			want: "download exceeds",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			server := httptest.NewServer(tt.handler)
			defer server.Close()
			root := filepath.Join(t.TempDir(), "failed network install")
			output := filepath.Join(t.TempDir(), "github-output")
			pathOutput := filepath.Join(t.TempDir(), "github-path")
			result := runInstaller(t, "-Version", testVersion, "-InstallRoot", root,
				"-DownloadBaseUrl", server.URL, "-DownloadAttempts", "1",
				"-OutputFile", output, "-PathFile", pathOutput)
			if result.err == nil || !strings.Contains(result.output, tt.want) {
				t.Fatalf("error = %v, output = %q, want failure containing %q", result.err, result.output, tt.want)
			}
			assertNotExposed(t, root, output, pathOutput)
		})
	}
}

func TestSetupActionRollsBackFailedOutputPublication(t *testing.T) {
	requireSupportedHost(t)
	releaseDir := makeRelease(t, nil)
	for _, blocked := range []string{"output", "path"} {
		t.Run(blocked, func(t *testing.T) {
			root := filepath.Join(t.TempDir(), "rolled back install")
			output := filepath.Join(t.TempDir(), "github-output")
			pathOutput := filepath.Join(t.TempDir(), "github-path")
			blockedPath := output
			if blocked == "path" {
				blockedPath = pathOutput
			}
			if err := os.Mkdir(blockedPath, 0755); err != nil {
				t.Fatal(err)
			}
			result := runInstaller(t, "-Version", testVersion, "-InstallRoot", root,
				"-DownloadDirectory", releaseDir, "-OutputFile", output, "-PathFile", pathOutput)
			if result.err == nil {
				t.Fatal("blocked action output destination was accepted")
			}
			assertNotExposed(t, root, output, pathOutput)
		})
	}
}

func TestSetupActionBoundsNetworkTimeout(t *testing.T) {
	requireSupportedHost(t)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Length", "4")
		w.WriteHeader(http.StatusOK)
		if flusher, ok := w.(http.Flusher); ok {
			flusher.Flush()
		}
		select {
		case <-time.After(3 * time.Second):
			_, _ = io.WriteString(w, "late")
		case <-r.Context().Done():
		}
	}))
	defer server.Close()

	root := filepath.Join(t.TempDir(), "timeout install")
	output := filepath.Join(t.TempDir(), "github-output")
	pathOutput := filepath.Join(t.TempDir(), "github-path")
	started := time.Now()
	result := runInstaller(t, "-Version", testVersion, "-InstallRoot", root,
		"-DownloadBaseUrl", server.URL, "-RequestTimeoutSeconds", "1", "-DownloadAttempts", "1",
		"-OutputFile", output, "-PathFile", pathOutput)
	if result.err == nil || !strings.Contains(result.output, "after 1 attempts") {
		t.Fatalf("timeout error = %v, output = %q", result.err, result.output)
	}
	if elapsed := time.Since(started); elapsed > 5*time.Second {
		t.Fatalf("bounded timeout took %s", elapsed)
	}
	assertNotExposed(t, root, output, pathOutput)
}

type commandResult struct {
	output string
	err    error
}

func runInstaller(t *testing.T, args ...string) commandResult {
	t.Helper()
	shell, shellArgs := powerShell(t)
	_, file, _, _ := runtime.Caller(0)
	script := filepath.Join(filepath.Dir(file), "..", "..", "setup-playtestr", "install.ps1")
	commandArgs := append(shellArgs, "-File", script)
	commandArgs = append(commandArgs, args...)
	command := exec.Command(shell, commandArgs...)
	command.Env = append(os.Environ(), "PLAYTESTR_SETUP_FIXTURE=1")
	output, err := command.CombinedOutput()
	return commandResult{output: string(output), err: err}
}

func powerShell(t *testing.T) (string, []string) {
	t.Helper()
	if path, err := exec.LookPath("pwsh"); err == nil {
		return path, []string{"-NoLogo", "-NoProfile", "-NonInteractive"}
	}
	if path, err := exec.LookPath("powershell"); err == nil {
		return path, []string{"-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass"}
	}
	t.Skip("PowerShell is required to exercise the composite action installer")
	return "", nil
}

func makeRelease(t *testing.T, extra map[string][]byte) string {
	t.Helper()
	base := releaseBaseName()
	files := map[string][]byte{}
	for _, name := range []string{"LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"} {
		files[base+"/"+name] = []byte(name + "\n")
	}
	binaryName := "playtestr"
	if runtime.GOOS == "windows" {
		binaryName += ".exe"
	}
	files[base+"/"+binaryName] = releaseBinary(t)
	for name, data := range extra {
		files[name] = data
	}
	return writeRelease(t, files)
}

func makeReleaseWithoutExecutable(t *testing.T) string {
	t.Helper()
	base := releaseBaseName()
	files := map[string][]byte{}
	for _, name := range []string{"LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"} {
		files[base+"/"+name] = []byte(name + "\n")
	}
	return writeRelease(t, files)
}

func writeRelease(t *testing.T, files map[string][]byte) string {
	t.Helper()
	directory := t.TempDir()
	archivePath := filepath.Join(directory, releaseArchiveName())
	if runtime.GOOS == "windows" {
		writeZip(t, archivePath, files)
	} else {
		writeTarGzip(t, archivePath, files)
	}
	writeChecksum(t, archivePath)
	return directory
}

func wrongNativeTarget() []string {
	if runtime.GOOS == "windows" {
		return []string{"-TargetOS", "linux", "-TargetArch", "amd64"}
	}
	return []string{"-TargetOS", "windows", "-TargetArch", "amd64"}
}

func releaseBinary(t *testing.T) []byte {
	t.Helper()
	data, err := os.ReadFile(os.Args[0])
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func writeZip(t *testing.T, path string, files map[string][]byte) {
	t.Helper()
	output, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	archive := zip.NewWriter(output)
	for _, name := range sortedNames(files) {
		header := &zip.FileHeader{Name: name, Method: zip.Deflate}
		header.SetMode(0755)
		entry, err := archive.CreateHeader(header)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := entry.Write(files[name]); err != nil {
			t.Fatal(err)
		}
	}
	if err := archive.Close(); err != nil {
		t.Fatal(err)
	}
	if err := output.Close(); err != nil {
		t.Fatal(err)
	}
}

func writeTarGzip(t *testing.T, path string, files map[string][]byte) {
	t.Helper()
	output, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	compressed := gzip.NewWriter(output)
	archive := tar.NewWriter(compressed)
	for _, name := range sortedNames(files) {
		data := files[name]
		header := &tar.Header{Name: name, Mode: 0755, Size: int64(len(data)), Typeflag: tar.TypeReg}
		if err := archive.WriteHeader(header); err != nil {
			t.Fatal(err)
		}
		if _, err := archive.Write(data); err != nil {
			t.Fatal(err)
		}
	}
	if err := archive.Close(); err != nil {
		t.Fatal(err)
	}
	if err := compressed.Close(); err != nil {
		t.Fatal(err)
	}
	if err := output.Close(); err != nil {
		t.Fatal(err)
	}
}

func writeChecksum(t *testing.T, archivePath string) {
	t.Helper()
	data, err := os.ReadFile(archivePath)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(data)
	text := fmt.Sprintf("%x  %s\n", sum, filepath.Base(archivePath))
	if err := os.WriteFile(archivePath+".sha256", []byte(text), 0644); err != nil {
		t.Fatal(err)
	}
}

func sortedNames(files map[string][]byte) []string {
	names := make([]string, 0, len(files))
	for name := range files {
		names = append(names, name)
	}
	sort.Strings(names)
	return names
}

func releaseBaseName() string {
	return fmt.Sprintf("playtestr_%s_%s_%s", strings.TrimPrefix(testVersion, "v"), targetOS(), targetArch())
}

func releaseArchiveName() string {
	extension := "tar.gz"
	if runtime.GOOS == "windows" {
		extension = "zip"
	}
	return releaseBaseName() + "." + extension
}

func targetOS() string {
	if runtime.GOOS == "darwin" {
		return "darwin"
	}
	return runtime.GOOS
}

func targetArch() string {
	if runtime.GOARCH == "amd64" {
		return "amd64"
	}
	return runtime.GOARCH
}

func requireSupportedHost(t *testing.T) {
	t.Helper()
	target := targetOS() + "/" + targetArch()
	if target != "linux/amd64" && target != "darwin/arm64" && target != "windows/amd64" {
		t.Skipf("host %s is not an advertised release target", target)
	}
}

func readEnvironmentFile(t *testing.T, path string) map[string]string {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	values := map[string]string{}
	for _, line := range strings.Split(strings.TrimSpace(string(data)), "\n") {
		key, value, ok := strings.Cut(strings.TrimSuffix(line, "\r"), "=")
		if ok {
			values[key] = value
		}
	}
	return values
}

func assertNotExposed(t *testing.T, root, output, pathOutput string) {
	t.Helper()
	for _, path := range []string{output, pathOutput} {
		if data, err := os.ReadFile(path); err == nil && len(data) > 0 {
			t.Errorf("failure exposed environment entry in %s: %q", path, data)
		}
	}
	entries, err := os.ReadDir(root)
	if err != nil {
		if os.IsNotExist(err) {
			return
		}
		t.Fatal(err)
	}
	if len(entries) != 0 {
		t.Errorf("failed installation left files in %s: %v", root, entries)
	}
}

func runCommand(t *testing.T, path string, args ...string) string {
	t.Helper()
	command := exec.Command(path, args...)
	command.Env = append(os.Environ(), "PLAYTESTR_SETUP_FIXTURE=1")
	output, err := command.CombinedOutput()
	if err != nil {
		t.Fatalf("run %s: %v: %s", path, err, output)
	}
	return string(output)
}
