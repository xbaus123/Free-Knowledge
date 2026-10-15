package studio

// Starting point for a new lesson in each language: a complete example where
// the reference passes and the starter fails, so "Check lesson" works
// immediately and authors can see the expected shape of each file.
type template struct {
	markdown  string // %s is the lesson title
	starter   string
	tests     string
	reference string
}

const markdownTemplate = "# %s\n\nExplain the idea here. Code examples in fenced blocks are syntax highlighted.\n\n## Your task\n\nWrite `answer` so that it returns `42`.\n"

var templates = map[string]template{
	"python": {
		markdown:  markdownTemplate,
		starter:   "def answer():\n    # Return the answer\n    pass\n",
		reference: "def answer():\n    return 42\n",
		tests: `import unittest

from solution import answer


class AnswerTest(unittest.TestCase):
    def test_returns_42(self):
        """returns 42"""
        self.assertEqual(answer(), 42)
`,
	},
	"javascript": {
		markdown:  markdownTemplate,
		starter:   "export function answer() {\n  // Return the answer\n}\n",
		reference: "export function answer() {\n  return 42;\n}\n",
		tests: `import { test } from "node:test";
import assert from "node:assert/strict";
import { answer } from "./solution.js";

test("returns 42", () => {
  assert.equal(answer(), 42);
});
`,
	},
	"go": {
		markdown:  "# %s\n\nExplain the idea here. Code examples in fenced blocks are syntax highlighted.\n\n## Your task\n\nWrite `Answer` so that it returns `42`.\n",
		starter:   "package lesson\n\nfunc Answer() int {\n\t// Return the answer\n\treturn 0\n}\n",
		reference: "package lesson\n\nfunc Answer() int {\n\treturn 42\n}\n",
		tests: `package lesson

import "testing"

func TestAnswer(t *testing.T) {
	if got := Answer(); got != 42 {
		t.Errorf("Answer() = %d, want 42", got)
	}
}
`,
	},
	"c": {
		markdown:  markdownTemplate,
		starter:   "int answer(void) {\n    /* Return the answer */\n    return 0;\n}\n",
		reference: "int answer(void) {\n    return 42;\n}\n",
		tests: `#include "fk_test.h"

int answer(void);

/* Available checks: EXPECT_TRUE, EXPECT_EQ_INT, EXPECT_EQ_DOUBLE, EXPECT_EQ_STR */
TEST(returns_42) {
    EXPECT_EQ_INT(answer(), 42);
}
`,
	},
	"rust": {
		markdown:  markdownTemplate,
		starter:   "pub fn answer() -> i32 {\n    // Return the answer\n    0\n}\n",
		reference: "pub fn answer() -> i32 {\n    42\n}\n",
		tests: `use super::*;

#[test]
fn returns_42() {
    assert_eq!(answer(), 42);
}
`,
	},
}

const articleTemplate = `# %s

Write your article here. Use headings to break up longer explanations, **bold** for key terms, and fenced code blocks for examples:

` + "```python\nprint(\"hello\")\n```" + `

Learners finish an article by clicking **Mark Complete** at the bottom.
`

const quizIntroTemplate = `# %s

Set the scene for the questions below. Learners see this text next to the quiz.
`

var quizTemplate = QuestionSource{
	Prompt:       "Which of these is a compiled language?",
	Options:      []string{"Go", "Python", "Bash"},
	CorrectIndex: 0,
	Explanation:  "Go is compiled to machine code ahead of time; Python and Bash are interpreted.",
}

const designMarkdownTemplate = `# %s

Describe the scenario: what traffic is arriving, and what's going wrong?

## Your task

Keep **p99 latency at or under 200 ms**. Then click **Simulate Traffic** to send 1,000 requests through your design.
`

const designStarterTemplate = `{"nodes":[` +
	`{"id":"client","type":"client","position":{"x":0,"y":120},"data":{"label":"Users"}},` +
	`{"id":"api-1","type":"server","position":{"x":300,"y":120},"data":{"label":"API Server"}},` +
	`{"id":"db","type":"database","position":{"x":600,"y":120},"data":{"label":"Database"}}],` +
	`"edges":[{"id":"client-api-1","source":"client","target":"api-1"},{"id":"api-1-db","source":"api-1","target":"db"}]}`

const designSolutionTemplate = `{"nodes":[` +
	`{"id":"client","type":"client","position":{"x":0,"y":120},"data":{"label":"Users"}},` +
	`{"id":"lb","type":"loadBalancer","position":{"x":220,"y":120},"data":{"label":"Load Balancer"}},` +
	`{"id":"api-1","type":"server","position":{"x":440,"y":40},"data":{"label":"API Server 1"}},` +
	`{"id":"api-2","type":"server","position":{"x":440,"y":200},"data":{"label":"API Server 2"}},` +
	`{"id":"db","type":"database","position":{"x":680,"y":120},"data":{"label":"Database"}}],` +
	`"edges":[{"id":"client-lb","source":"client","target":"lb"},{"id":"lb-api-1","source":"lb","target":"api-1"},` +
	`{"id":"lb-api-2","source":"lb","target":"api-2"},{"id":"api-1-db","source":"api-1","target":"db"},{"id":"api-2-db","source":"api-2","target":"db"}]}`
