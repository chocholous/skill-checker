import { SimpleMarkdown } from "@apify/ui-library";

export function MarkdownViewer({ content }: { content: string }) {
	return <SimpleMarkdown size="regular">{content}</SimpleMarkdown>;
}
