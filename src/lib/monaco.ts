// Bundles Monaco locally (no CDN) so the editor works offline. Only the editor
// core and syntax highlighting for the languages we teach are included.
import { loader } from "@monaco-editor/react";
import * as monaco from "monaco-esm/editor/editor.api";
import EditorWorker from "monaco-editor/editor/editor.worker?worker";
import "./monaco-features";
import "monaco-esm/languages/definitions/python/register";
import "monaco-esm/languages/definitions/javascript/register";
import "monaco-esm/languages/definitions/go/register";
import "monaco-esm/languages/definitions/cpp/register"; // registers "c" too
import "monaco-esm/languages/definitions/rust/register";
import "monaco-esm/languages/definitions/markdown/register"; // Creator Studio

self.MonacoEnvironment = { getWorker: () => new EditorWorker() };

loader.config({ monaco });

monaco.editor.defineTheme("freeknowledge", {
  base: "vs-dark",
  inherit: true,
  rules: [],
  colors: { "editor.background": "#0b0b0e", "editor.lineHighlightBackground": "#18181b" },
});

/** Maps engine language ids to Monaco language ids. */
export const monacoLanguage = (id: string) => ({ javascript: "javascript", c: "c" })[id] ?? id;
