//go:build windows

package runner

import (
	"errors"
	"os/exec"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

type processTree struct {
	job windows.Handle
}

type jobAccounting struct {
	TotalUserTime             int64
	TotalKernelTime           int64
	ThisPeriodTotalUserTime   int64
	ThisPeriodTotalKernelTime int64
	TotalPageFaultCount       uint32
	TotalProcesses            uint32
	ActiveProcesses           uint32
	TotalTerminatedProcesses  uint32
}

func configureProcess(_ *exec.Cmd) {}

func attachProcessTree(pid int) (*processTree, error) {
	job, err := windows.CreateJobObject(nil, nil)
	if err != nil {
		return nil, err
	}
	tree := &processTree{job: job}
	var limits windows.JOBOBJECT_EXTENDED_LIMIT_INFORMATION
	limits.BasicLimitInformation.LimitFlags = windows.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
	if _, err = windows.SetInformationJobObject(
		job,
		windows.JobObjectExtendedLimitInformation,
		uintptr(unsafe.Pointer(&limits)),
		uint32(unsafe.Sizeof(limits)),
	); err != nil {
		_ = windows.CloseHandle(job)
		return nil, err
	}
	process, err := windows.OpenProcess(
		windows.PROCESS_SET_QUOTA|windows.PROCESS_TERMINATE|windows.PROCESS_QUERY_LIMITED_INFORMATION,
		false,
		uint32(pid),
	)
	if err != nil {
		_ = windows.CloseHandle(job)
		return nil, err
	}
	defer windows.CloseHandle(process)
	if err = windows.AssignProcessToJobObject(job, process); err != nil {
		_ = windows.CloseHandle(job)
		return nil, err
	}
	return tree, nil
}

func (t *processTree) active() (bool, error) {
	var accounting jobAccounting
	err := windows.QueryInformationJobObject(
		t.job,
		windows.JobObjectBasicAccountingInformation,
		uintptr(unsafe.Pointer(&accounting)),
		uint32(unsafe.Sizeof(accounting)),
		nil,
	)
	return accounting.ActiveProcesses > 0, err
}

func (t *processTree) terminate() error {
	err := windows.TerminateJobObject(t.job, 1)
	if errors.Is(err, syscall.ERROR_ACCESS_DENIED) {
		active, queryErr := t.active()
		if queryErr == nil && !active {
			return nil
		}
	}
	return err
}

func (t *processTree) close() error {
	return windows.CloseHandle(t.job)
}

func (t *processTree) mechanism() string { return "windows-job-object" }

func processExists(pid int) bool {
	process, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, uint32(pid))
	if err != nil {
		return false
	}
	defer windows.CloseHandle(process)
	var code uint32
	const stillActive = 259
	return windows.GetExitCodeProcess(process, &code) == nil && code == stillActive
}
