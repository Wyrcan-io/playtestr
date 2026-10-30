// Command nativecapture redirects a trusted sibling CLI's selected stdout into
// one bounded workspace file while leaving its real terminal input/UI attached.
package main

import (
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
)

const outputLimit = 1024 * 1024

var errOutputLimit = errors.New("selected stdout exceeds 1 MiB")

type boundedOutput struct {
	writer    io.Writer
	remaining int
	err       error
}

func (w *boundedOutput) Write(body []byte) (int, error) {
	allowed := len(body)
	if allowed > w.remaining {
		allowed = w.remaining
	}
	n, err := w.writer.Write(body[:allowed])
	w.remaining -= n
	if err != nil {
		w.err = err
		return n, err
	}
	if n != len(body) {
		w.err = errOutputLimit
		return n, w.err
	}
	return n, nil
}

func run(args []string, siblingDirectory string, stdin io.Reader, stderr io.Writer) int {
	flags := flag.NewFlagSet("nativecapture", flag.ContinueOnError)
	flags.SetOutput(stderr)
	app := flags.String("app", "", "trusted sibling CLI basename")
	output := flags.String("output", "", "new workspace output filename")
	if err := flags.Parse(args); err != nil {
		return 125
	}
	if !regexp.MustCompile(`^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,100}$`).MatchString(*app) ||
		!regexp.MustCompile(`^[A-Za-z0-9_-]+\.txt$`).MatchString(*output) {
		fmt.Fprintln(stderr, "nativecapture: invalid app/output basename")
		return 125
	}
	file, err := os.OpenFile(*output, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		fmt.Fprintln(stderr, "nativecapture: create selected output:", err)
		return 125
	}
	writer := &boundedOutput{writer: file, remaining: outputLimit}
	command := exec.Command(filepath.Join(siblingDirectory, *app), flags.Args()...)
	command.Stdin, command.Stdout, command.Stderr = stdin, writer, stderr
	waitErr := command.Run()
	closeErr := file.Close()
	if writer.err != nil || closeErr != nil {
		fmt.Fprintln(stderr, "nativecapture: selected output:", errors.Join(writer.err, closeErr))
		return 125
	}
	if waitErr != nil {
		var exited *exec.ExitError
		if errors.As(waitErr, &exited) && exited.ExitCode() >= 0 {
			return exited.ExitCode()
		}
		fmt.Fprintln(stderr, "nativecapture: trusted target:", waitErr)
		return 125
	}
	return 0
}

func main() {
	self, err := os.Executable()
	if err != nil {
		fmt.Fprintln(os.Stderr, "nativecapture: executable:", err)
		os.Exit(125)
	}
	os.Exit(run(os.Args[1:], filepath.Dir(self), os.Stdin, os.Stderr))
}
