//go:build windows

package runner

import (
	"errors"
	"fmt"
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

func configureProcess(cmd *exec.Cmd) {
	if cmd.SysProcAttr == nil {
		cmd.SysProcAttr = &syscall.SysProcAttr{}
	}
	// No target code may run until its Job Object membership is established.
	cmd.SysProcAttr.CreationFlags |= windows.CREATE_SUSPENDED
}

func activateProcess(cmd *exec.Cmd) error {
	// ConPTY's Spawn closes the initial thread handle. A process created
	// suspended has exactly one initial thread; recover that handle by owner
	// PID before allowing any target instructions to execute.
	snapshot, err := windows.CreateToolhelp32Snapshot(windows.TH32CS_SNAPTHREAD, 0)
	if err != nil {
		return fmt.Errorf("snapshot suspended target thread: %w", err)
	}
	defer windows.CloseHandle(snapshot)
	entry := windows.ThreadEntry32{Size: uint32(unsafe.Sizeof(windows.ThreadEntry32{}))}
	var threadID uint32
	for err = windows.Thread32First(snapshot, &entry); err == nil; err = windows.Thread32Next(snapshot, &entry) {
		if entry.OwnerProcessID == uint32(cmd.Process.Pid) {
			if threadID != 0 {
				return errors.New("suspended target unexpectedly has multiple threads")
			}
			threadID = entry.ThreadID
		}
		entry.Size = uint32(unsafe.Sizeof(entry))
	}
	if !errors.Is(err, windows.ERROR_NO_MORE_FILES) {
		return fmt.Errorf("enumerate suspended target thread: %w", err)
	}
	if threadID == 0 {
		return errors.New("suspended target initial thread not found")
	}
	thread, err := windows.OpenThread(windows.THREAD_SUSPEND_RESUME, false, threadID)
	if err != nil {
		return fmt.Errorf("open suspended target thread: %w", err)
	}
	defer windows.CloseHandle(thread)
	previous, err := windows.ResumeThread(thread)
	if err != nil {
		return fmt.Errorf("resume attached target thread: %w", err)
	}
	if previous != 1 {
		return fmt.Errorf("unexpected initial target suspend count %d", previous)
	}
	return nil
}

func reapStartupProcess(cmd *exec.Cmd) error {
	handle, err := windows.OpenProcess(windows.SYNCHRONIZE, false, uint32(cmd.Process.Pid))
	if err != nil {
		return fmt.Errorf("open startup target for exit confirmation: %w", err)
	}
	defer windows.CloseHandle(handle)
	state, err := windows.WaitForSingleObject(handle, 3000)
	if err != nil {
		return fmt.Errorf("wait for startup target exit: %w", err)
	}
	if state != windows.WAIT_OBJECT_0 {
		return fmt.Errorf("startup target exit unconfirmed: wait status %d", state)
	}
	cmd.ProcessState, err = cmd.Process.Wait()
	return err
}

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
