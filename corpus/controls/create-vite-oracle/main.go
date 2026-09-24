package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

type packageJSON struct {
	Name            string            `json:"name"`
	Type            string            `json:"type"`
	Scripts         map[string]string `json:"scripts"`
	Dependencies    map[string]string `json:"dependencies"`
	DevDependencies map[string]string `json:"devDependencies"`
}

func main() {
	if len(os.Args) < 2 {
		fail("usage: create-vite-oracle PROFILE [create-vite arguments]")
	}
	profile := os.Args[1]
	executable, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	runtimeDir := "create-vite-runtime"
	if override := os.Getenv("PLAYTESTR_CREATE_VITE_RUNTIME"); override != "" {
		if filepath.Base(override) != override {
			fail("unsafe runtime directory %q", override)
		}
		runtimeDir = override
	}
	target := filepath.Join(filepath.Dir(executable), runtimeDir, "node_modules", "create-vite", "index.js")
	node, err := exec.LookPath("node")
	if err != nil {
		fail("locate node: %v", err)
	}
	command := exec.Command(node, append([]string{target}, os.Args[2:]...)...)
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := command.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fail("run create-vite: %v", err)
	}
	if err := verify(profile); err != nil {
		fail("profile %s: %v", profile, err)
	}
	fmt.Printf("PLAYTESTR-CV-ORACLE %s OK\n", profile)
}

func verify(profile string) error {
	switch profile {
	case "vanilla":
		return verifyProject("cv-vanilla", "cv-vanilla", "src/main.js", "")
	case "typescript":
		return verifyProject("cv-typescript", "cv-typescript", "src/main.ts", "")
	case "lit":
		return verifyProject("cv-lit", "cv-lit", "src/my-element.js", "lit")
	case "corrected":
		return verifyProject("Bad Name", "corrected-package", "src/main.js", "")
	case "refuse":
		data, err := os.ReadFile(filepath.Join("occupied", "sentinel.txt"))
		if err != nil || strings.TrimSpace(string(data)) != "PLAYTESTR-CV-SENTINEL" {
			return fmt.Errorf("occupied sentinel changed: %v", err)
		}
		if _, err := os.Stat(filepath.Join("occupied", "package.json")); !os.IsNotExist(err) {
			return fmt.Errorf("refused destination acquired package.json: %v", err)
		}
		return nil
	case "cancel":
		if _, err := os.Stat("cancelled-project"); !os.IsNotExist(err) {
			return fmt.Errorf("cancelled destination exists: %v", err)
		}
		return nil
	case "nested":
		if err := verifyProject(filepath.Join("nested", "cv-nested"), "cv-nested", "src/main.js", ""); err != nil {
			return err
		}
		data, err := os.ReadFile("neighbor.txt")
		if err != nil || strings.TrimSpace(string(data)) != "PLAYTESTR-CV-NEIGHBOR" {
			return fmt.Errorf("neighbor sentinel changed: %v", err)
		}
		return nil
	case "decline":
		if err := verifyProject("cv-decline", "cv-decline", "src/main.js", ""); err != nil {
			return err
		}
		for _, path := range []string{filepath.Join("cv-decline", "node_modules"), filepath.Join("cv-decline", "package-lock.json")} {
			if _, err := os.Stat(path); !os.IsNotExist(err) {
				return fmt.Errorf("declined install created %s: %v", path, err)
			}
		}
		return nil
	default:
		return fmt.Errorf("unknown profile")
	}
}

func verifyProject(directory, name, requiredFile, dependency string) error {
	data, err := os.ReadFile(filepath.Join(directory, "package.json"))
	if err != nil {
		return fmt.Errorf("read package: %w", err)
	}
	var pkg packageJSON
	if err := json.Unmarshal(data, &pkg); err != nil {
		return fmt.Errorf("decode package: %w", err)
	}
	if pkg.Name != name || pkg.Type != "module" || pkg.Scripts["dev"] != "vite" {
		return fmt.Errorf("package fields name=%q type=%q dev=%q", pkg.Name, pkg.Type, pkg.Scripts["dev"])
	}
	if dependency != "" && pkg.Dependencies[dependency] == "" {
		return fmt.Errorf("missing dependency %q", dependency)
	}
	if info, err := os.Stat(filepath.Join(directory, filepath.FromSlash(requiredFile))); err != nil || info.IsDir() {
		return fmt.Errorf("required file %s: %v", requiredFile, err)
	}
	return nil
}

func fail(format string, values ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-CV-ORACLE FAIL: "+format+"\n", values...)
	os.Exit(90)
}
