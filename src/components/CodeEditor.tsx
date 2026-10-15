import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";
import { monacoLanguage } from "../lib/monaco";

interface Props {
  /** Unique per lesson, so each keeps its own undo history. */
  path: string;
  language: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function CodeEditor({ path, language, value, onChange, onSubmit }: Props) {
  // Monaco binds commands once at mount; read the latest callback through a ref.
  const submitRef = useRef(onSubmit);
  submitRef.current = onSubmit;

  const handleMount: OnMount = (editor, monaco) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => submitRef.current());
    editor.focus();
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
        tabSize: language === "python" || language === "rust" ? 4 : 2,
        insertSpaces: language !== "go",
        padding: { top: 12 },
        renderLineHighlight: "line",
      }}
    />
  );
}
