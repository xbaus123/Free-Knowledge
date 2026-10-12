//go:build windows

package runner

import "os/exec"

// configureProcessTree uses the default kill on Windows. Killing grandchildren
// needs a Job Object, which is left for later.
func configureProcessTree(cmd *exec.Cmd) {}
