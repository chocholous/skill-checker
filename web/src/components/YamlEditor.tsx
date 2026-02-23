import { Button, Text, theme } from "@apify/ui-library";
import { yaml } from "@codemirror/lang-yaml";
import CodeMirror from "@uiw/react-codemirror";
import { useCallback, useEffect, useState } from "react";
import styled from "styled-components";

import { api } from "../api/client";

interface Props {
	sourceFile: string;
	/** If provided, the editor uses this as initial content instead of fetching from the API. */
	initialContent?: string;
	onSaved?: () => void;
}

const EditorCard = styled.div`
    border: 1px solid ${theme.color.neutral.border};
    border-radius: ${theme.radius.radius8};
    overflow: hidden;
`;

const EditorHeader = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: ${theme.space.space8} ${theme.space.space12};
    background: ${theme.color.neutral.backgroundMuted};
    border-bottom: 1px solid ${theme.color.neutral.border};
`;

const HeaderActions = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space8};
`;

const ErrorBanner = styled.div`
    padding: ${theme.space.space8} ${theme.space.space12};
    background: ${theme.color.danger.backgroundSubtle};
    color: ${theme.color.danger.text};
    border-bottom: 1px solid ${theme.color.danger.borderSubtle};
    font-size: 1.2rem;
`;

const LoadingState = styled.div`
    padding: ${theme.space.space16};
`;

function getInsertSnippet(currentContent: string): string {
	const isDomain = /^domain:/m.test(currentContent);
	// Find existing ids to auto-increment
	const idMatches = [...currentContent.matchAll(/- id: (?:new-)?(\d+)/g)];
	const maxNum = idMatches.reduce(
		(max, m) => Math.max(max, Number.parseInt(m[1], 10) || 0),
		0,
	);
	const nextId = `new-${maxNum + 1}`;

	if (isDomain) {
		return ["", `  - id: ${nextId}`, '    name: ""', '    prompt: ""', ""].join(
			"\n",
		);
	}
	return [
		"",
		`  - id: ${nextId}`,
		'    name: ""',
		'    target_skill: ""',
		'    prompt: ""',
		"",
	].join("\n");
}

export function YamlEditor({ sourceFile, initialContent, onSaved }: Props) {
	const [content, setContent] = useState(initialContent ?? "");
	const [original, setOriginal] = useState(initialContent ?? "");
	const [loading, setLoading] = useState(!initialContent);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [success, setSuccess] = useState(false);

	useEffect(() => {
		if (initialContent !== undefined) return;
		setLoading(true);
		api
			.getRawYaml(sourceFile)
			.then((data) => {
				setContent(data.content);
				setOriginal(data.content);
				setLoading(false);
			})
			.catch((e) => {
				setError(String(e));
				setLoading(false);
			});
	}, [sourceFile, initialContent]);

	const handleSave = useCallback(async () => {
		setSaving(true);
		setError(null);
		setSuccess(false);
		try {
			await api.updateYaml(sourceFile, content);
			setOriginal(content);
			setSuccess(true);
			onSaved?.();
			setTimeout(() => setSuccess(false), 2000);
		} catch (e: unknown) {
			setError(String(e));
		} finally {
			setSaving(false);
		}
	}, [sourceFile, content, onSaved]);

	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if ((e.metaKey || e.ctrlKey) && e.key === "s") {
				e.preventDefault();
				handleSave();
			}
		};
		window.addEventListener("keydown", handler);
		return () => window.removeEventListener("keydown", handler);
	}, [handleSave]);

	const handleInsertTemplate = useCallback(() => {
		const snippet = getInsertSnippet(content);
		const trimmed = content.endsWith("\n") ? content : `${content}\n`;
		setContent(trimmed + snippet);
	}, [content]);

	if (loading) {
		return (
			<LoadingState>
				<Text type="body" size="regular" color={theme.color.neutral.textMuted}>
					Loading...
				</Text>
			</LoadingState>
		);
	}

	const isDirty = content !== original;

	return (
		<EditorCard>
			<EditorHeader>
				<Text type="code" size="small" color={theme.color.neutral.textMuted}>
					{sourceFile}
				</Text>
				<HeaderActions>
					<Button
						size="small"
						variant="secondary"
						onClick={handleInsertTemplate}
					>
						Insert Template
					</Button>
					{isDirty && (
						<Text type="body" size="small" color={theme.color.warning.text}>
							Unsaved changes
						</Text>
					)}
					{success && (
						<Text type="body" size="small" color={theme.color.success.text}>
							Saved!
						</Text>
					)}
					<Button
						size="small"
						variant="primary"
						onClick={handleSave}
						disabled={saving || !isDirty}
					>
						{saving ? "Saving..." : "Save"}
					</Button>
				</HeaderActions>
			</EditorHeader>
			{error && <ErrorBanner>{error}</ErrorBanner>}
			<CodeMirror
				value={content}
				onChange={setContent}
				extensions={[yaml()]}
				height="400px"
				basicSetup={{ lineNumbers: true, foldGutter: true }}
			/>
		</EditorCard>
	);
}
