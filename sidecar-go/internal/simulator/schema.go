package simulator

import (
	"fmt"
	"slices"
)

// Field is one field of a message schema, Protocol Buffers style: readers
// match fields by tag number, not by name.
type Field struct {
	Tag      int    `json:"tag"`
	Name     string `json:"name"`
	Type     string `json:"type"` // int64, string, or bool
	Required bool   `json:"required,omitempty"`
}

// SchemaSpec is a lesson's fixed v1 schema; the learner edits v2 in the
// Schema Registry node.
type SchemaSpec struct {
	V1 []Field `json:"v1"`
	// NewFields must appear in v2: the feature the new version ships.
	NewFields []string `json:"new_fields,omitempty"`
}

var fieldTypes = []string{"int64", "string", "bool"}

func validateSchema(fields []Field) error {
	if len(fields) == 0 {
		return fmt.Errorf("a schema needs at least one field")
	}
	if len(fields) > 20 {
		return fmt.Errorf("a schema can have at most 20 fields")
	}
	tags, names := map[int]bool{}, map[string]bool{}
	for _, f := range fields {
		switch {
		case f.Tag < 1 || f.Tag > 99:
			return fmt.Errorf("field %q: tag must be between 1 and 99", f.Name)
		case f.Name == "" || len(f.Name) > 40:
			return fmt.Errorf("field with tag %d needs a name", f.Tag)
		case !slices.Contains(fieldTypes, f.Type):
			return fmt.Errorf("field %q: type must be int64, string, or bool", f.Name)
		case tags[f.Tag]:
			return fmt.Errorf("two fields use tag %d", f.Tag)
		case names[f.Name]:
			return fmt.Errorf("two fields are named %q", f.Name)
		}
		tags[f.Tag], names[f.Name] = true, true
	}
	return nil
}

// decode reports why a reader using one schema can't understand a message
// written with another, or "" if it can.
//
// Readers ignore fields they don't know (forward compatibility) and fill
// in defaults for optional fields that are missing (backward
// compatibility). A missing required field, or a tag whose type or
// meaning changed, breaks decoding.
func decode(writer, reader []Field, wv, rv string) string {
	for _, rf := range reader {
		i := slices.IndexFunc(writer, func(f Field) bool { return f.Tag == rf.Tag })
		if i < 0 {
			if rf.Required {
				return fmt.Sprintf("%s code requires field %q (tag %d), but %s messages don't have it.", rv, rf.Name, rf.Tag, wv)
			}
			continue
		}
		wf := writer[i]
		if wf.Type != rf.Type {
			return fmt.Sprintf("Tag %d is %s %q in %s but %s %q in %s: %s code can't parse %s messages.", rf.Tag, wf.Type, wf.Name, wv, rf.Type, rf.Name, rv, rv, wv)
		}
		if wf.Name != rf.Name {
			return fmt.Sprintf("Tag %d means %q in %s but %q in %s: %s code would silently read one as the other.", rf.Tag, wf.Name, wv, rf.Name, rv, rv)
		}
	}
	return ""
}
