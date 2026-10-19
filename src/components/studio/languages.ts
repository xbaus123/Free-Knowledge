export const LANGUAGES = [
  { id: "python", name: "Python", ext: "py" },
  { id: "javascript", name: "JavaScript", ext: "js" },
  { id: "go", name: "Go", ext: "go" },
  { id: "c", name: "C", ext: "c" },
  { id: "rust", name: "Rust", ext: "rs" },
] as const;

export const extension = (language?: string) => LANGUAGES.find((l) => l.id === language)?.ext ?? "txt";

export const languageName = (language?: string) => LANGUAGES.find((l) => l.id === language)?.name ?? language ?? "";
