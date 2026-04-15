import { Bot } from "lucide-react";
import ReactMarkdown from "react-markdown";

interface Props {
  content: string;
}

export function StreamingBubble({ content }: Props) {
  return (
    <div className="flex gap-3 justify-start animate-fade-in">
      <div className="w-8 h-8 rounded-lg bg-sunday-accent/20 flex items-center justify-center flex-shrink-0 mt-1">
        <Bot size={16} className="text-sunday-accent" />
      </div>

      <div className="max-w-[80%] rounded-2xl rounded-bl-md px-4 py-3 bg-sunday-assistant border border-sunday-border message-content">
        <div className="text-sm leading-relaxed prose-invert">
          <ReactMarkdown>{content}</ReactMarkdown>
          <span className="inline-block w-2 h-4 bg-sunday-accent/60 animate-pulse ml-0.5 rounded-sm" />
        </div>
      </div>
    </div>
  );
}
