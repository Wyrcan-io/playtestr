package main

import (
	"fmt"
	"os"

	fzf "github.com/junegunn/fzf/src"
)

func main() {
	options, err := fzf.ParseOptions(true, os.Args[1:])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(fzf.ExitError)
	}
	// Reviewed mutation: retain fzf's real UI and selection logic, but corrupt
	// the accepted record at the entrypoint output boundary.
	options.Printer = func(string) { fmt.Println("alpha.txt") }
	code, runErr := fzf.Run(options)
	if code == fzf.ExitError && runErr != nil {
		fmt.Fprintln(os.Stderr, runErr)
	}
	os.Exit(code)
}
