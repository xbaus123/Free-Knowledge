package lesson

import "testing"

func TestReverse(t *testing.T) {
	cases := []struct{ name, in, want string }{
		{"ascii", "hello", "olleh"},
		{"empty", "", ""},
		{"unicode", "héllo", "olléh"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if got := Reverse(c.in); got != c.want {
				t.Errorf("Reverse(%q) = %q, want %q", c.in, got, c.want)
			}
		})
	}
}
