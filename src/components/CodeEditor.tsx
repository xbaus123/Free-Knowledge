import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";
import { monacoLanguage } from "../lib/monaco";

interface Props {
  /** Unique per lesson, so each keeps its own undo history. */
  path: string;
  language: string;
  value: string;
  onChange: (value: string) => void;
  /** ⌘/Ctrl+Enter */
  onSubmit?: () => void;
  /** ⌘/Ctrl+S */
  onSave?: () => void;
  autoFocus?: boolean;
}

export function CodeEditor({ path, language, value, onChange, onSubmit, onSave, autoFocus = true }: Props) {
  // Monaco binds commands once at mount; read the latest callbacks through refs.
  const submitRef = useRef(onSubmit);
  submitRef.current = onSubmit;
  const saveRef = useRef(onSave);
  saveRef.current = onSave;

  const handleMount: OnMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => submitRef.current?.());
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => saveRef.current?.());
    if (autoFocus) editor.focus();
  };

  return (
    <Editor
      path={path}
      language={monacoLanguage(language)}
      value={value}
      onChange={(v) => onChange(v ?? "")}
      onMount={handleMount}
      theme="freeknowledge"
      loading={<div className="p-4 text-sm text-zinc-500">Loading editor…</div>}
      options={{
        fontSize: 14,
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: language === "python" || language === "rust" || language === "c" ? 4 : 2,
        insertSpaces: language !== "go",
        wordWrap: language === "markdown" ? "on" : "off",
        padding: { top: 12 },
        renderLineHighlight: "line",
      }}
    />
  );
}
