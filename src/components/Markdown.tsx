import { openUrl } from "@tauri-apps/plugin-opener";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

/** Renders lesson markdown. Links open in the system browser, never in the app window. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm prose-invert max-w-none prose-pre:bg-zinc-900 prose-pre:border prose-pre:border-zinc-800 prose-code:before:content-none prose-code:after:content-none prose-code:text-indigo-200">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          a: ({ href, children }) => (
            <a
              href={href}
              title={href}
              onClick={(e) => {
                e.preventDefault();
                if (href && /^(https?|mailto):/i.test(href)) openUrl(href).catch(console.error);
              }}
            >
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
