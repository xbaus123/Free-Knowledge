//go:build !windows

package runner

import (
	"os/exec"
	"syscall"
)

// configureProcessTree puts the child in its own process group so a timeout
// kills everything it spawned, not just the direct child.
func configureProcessTree(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
	cmd.Cancel = func() error {
		return syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)
	}
}
