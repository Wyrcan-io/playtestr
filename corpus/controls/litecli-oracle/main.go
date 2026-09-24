package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

const databaseScript = `import sqlite3,sys
p,profile,phase=sys.argv[1:]
c=sqlite3.connect(p)
if phase=='init':
 c.executescript("create table results(id text primary key,value text);insert into results values('alpha','one'),('beta','two');create table empty_results(id text);")
 c.commit();sys.exit(0)
rows=c.execute('select id,value from results order by id').fetchall()
want=[('alpha','one'),('beta','two')]
if profile=='insert': want.append(('gamma','three'))
if rows!=want: print('rows',rows,'want',want,file=sys.stderr);sys.exit(90)
print('PLAYTESTR-LITE-ORACLE '+profile+' OK')`

func main() {
	if len(os.Args) != 2 {
		fail("usage: litecli-oracle PROFILE")
	}
	profile := os.Args[1]
	python, err := exec.LookPath("python")
	if err != nil {
		fail("locate python: %v", err)
	}
	database := "trial.db"
	if out, err := exec.Command(python, "-c", databaseScript, database, profile, "init").CombinedOutput(); err != nil {
		fail("initialize database: %v: %s", err, out)
	}
	exe, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	target := filepath.Clean(filepath.Join(filepath.Dir(exe), "..", "r3c", "windows", "py-02-litecli", "venv", "Scripts", "litecli.exe"))
	sessions := 1
	if profile == "reopen" {
		sessions = 2
	}
	for range sessions {
		command := exec.Command(target, "--liteclirc", "liteclirc", "--no-warn", "--prompt", "trial> ", database)
		command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
		if os.Getenv("PLAYTESTR_LITECLI_MUTATION") == "1" {
			command.Env = append(os.Environ(), "PYTHONPATH="+filepath.Join(filepath.Dir(exe), "litecli-mutated"))
		}
		if err := command.Run(); err != nil {
			if exitErr, ok := err.(*exec.ExitError); ok {
				os.Exit(exitErr.ExitCode())
			}
			fail("run litecli: %v", err)
		}
	}
	check := exec.Command(python, "-c", databaseScript, database, profile, "check")
	check.Stdout, check.Stderr = os.Stdout, os.Stderr
	if err := check.Run(); err != nil {
		fail("database postcondition: %v", err)
	}
}

func fail(format string, values ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-LITE-ORACLE FAIL: "+format+"\n", values...)
	os.Exit(90)
}
