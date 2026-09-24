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
	Name            string `json:"name"`
	Theme           bool   `json:"theme"`
	ThemeAppearance string `json:"themeAppearance"`
}

func main() {
	if len(os.Args) != 2 {
		fail("usage: ipm-oracle PROFILE")
	}
	profile := os.Args[1]
	exe, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	runtimeDir := "ipm-runtime"
	if override := os.Getenv("PLAYTESTR_IPM_RUNTIME"); override != "" {
		if filepath.Base(override) != override {
			fail("unsafe runtime directory %q", override)
		}
		runtimeDir = override
	}
	node, err := exec.LookPath("node")
	if err != nil {
		fail("locate node: %v", err)
	}
	target := filepath.Join(filepath.Dir(exe), runtimeDir, "node_modules", "@inkdropapp", "ipm-cli", "bin", "cli.js")
	command := exec.Command(node, target, "init")
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := command.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fail("run ipm: %v", err)
	}
	if err := verify(profile); err != nil {
		fail("profile %s: %v", profile, err)
	}
	fmt.Printf("PLAYTESTR-IPM-ORACLE %s OK\n", profile)
}

func verify(profile string) error {
	if profile == "cancel" {
		entries, err := os.ReadDir(".")
		if err != nil {
			return err
		}
		for _, entry := range entries {
			if entry.Name() != "occupied" && entry.Name() != "neighbor.txt" {
				return fmt.Errorf("cancel created %s", entry.Name())
			}
		}
		return nil
	}
	if profile == "existing" {
		data, err := os.ReadFile(filepath.Join("occupied", "sentinel.txt"))
		if err != nil || strings.TrimSpace(string(data)) != "PLAYTESTR-IPM-SENTINEL" {
			return fmt.Errorf("sentinel changed: %v", err)
		}
		return verifyTheme("occupied", "dark")
	}
	appearance := "dark"
	name := "ipm-" + profile
	if profile == "light" {
		appearance = "light"
	}
	return verifyTheme(name, appearance)
}

func verifyTheme(name, appearance string) error {
	data, err := os.ReadFile(filepath.Join(name, "package.json"))
	if err != nil {
		return err
	}
	var pkg packageJSON
	if err := json.Unmarshal(data, &pkg); err != nil {
		return err
	}
	if pkg.Name != name || !pkg.Theme || pkg.ThemeAppearance != appearance {
		return fmt.Errorf("package fields name=%q theme=%v appearance=%q", pkg.Name, pkg.Theme, pkg.ThemeAppearance)
	}
	for _, path := range []string{"styles/ui.css", "styles/syntax.css", "styles/preview.css"} {
		if info, err := os.Stat(filepath.Join(name, filepath.FromSlash(path))); err != nil || info.IsDir() {
			return fmt.Errorf("required %s: %v", path, err)
		}
	}
	return nil
}

func fail(format string, values ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-IPM-ORACLE FAIL: "+format+"\n", values...)
	os.Exit(90)
}
