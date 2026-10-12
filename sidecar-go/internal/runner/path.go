package runner

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

// ExtendPath appends common toolchain locations to PATH. Apps launched from
// the macOS Finder inherit a minimal PATH (/usr/bin:/bin:...), which would
// hide Homebrew, Go, and rustup installs.
func ExtendPath() {
	if runtime.GOOS == "windows" {
		return
	}
	home, _ := os.UserHomeDir()
	extra := []string{
		"/opt/homebrew/bin",
		"/usr/local/bin",
		"/usr/local/go/bin",
		filepath.Join(home, ".cargo", "bin"),
		filepath.Join(home, "go", "bin"),
		filepath.Join(home, ".local", "bin"),
	}
	current := filepath.SplitList(os.Getenv("PATH"))
	seen := make(map[string]bool, len(current))
	for _, p := range current {
		seen[p] = true
	}
	for _, p := range extra {
		if !seen[p] {
			current = append(current, p)
		}
	}
	os.Setenv("PATH", strings.Join(current, string(os.PathListSeparator)))
}
