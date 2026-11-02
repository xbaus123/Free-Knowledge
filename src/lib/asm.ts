// Syntax highlighting for the Assembly course: GNU as x86-64 in Intel
// syntax. The editor (monaco.ts) and lesson code blocks (Markdown.tsx) use
// the same rules: comments, directives, labels, registers, and numbers.
import type { LanguageFn } from "lowlight";

/** General-purpose, segment, and SSE/AVX register names at every width. */
export const X86_REGISTERS =
  /\b(?:[re]?(?:ax|bx|cx|dx|si|di|sp|bp|ip)|[abcd][lh]|(?:si|di|sp|bp)l|r(?:[89]|1[0-5])[dwb]?|[xy]mm(?:[0-9]|1[0-5])|[cdefgs]s)\b/;

/** highlight.js grammar, registered for ```asm and ```s code blocks. */
export const asm: LanguageFn = (hljs) => ({
  name: "x86-64 Assembly",
  case_insensitive: true,
  contains: [
    hljs.HASH_COMMENT_MODE,
    hljs.C_LINE_COMMENT_MODE,
    hljs.C_BLOCK_COMMENT_MODE,
    { scope: "title.function", match: /^\s*[A-Za-z_.$][\w.$]*:/ },
    { scope: "keyword", match: /\.[A-Za-z_]\w*/ },
    { scope: "variable", match: X86_REGISTERS },
    { scope: "keyword", match: /\b(?:byte|word|dword|qword)\s+ptr\b/ },
    { scope: "number", match: /\b(?:0x[0-9a-f]+|0b[01]+|\d+)\b/ },
    hljs.QUOTE_STRING_MODE,
  ],
});
