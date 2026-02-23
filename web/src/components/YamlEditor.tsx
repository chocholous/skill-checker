import { Button, Text, theme } from "@apify/ui-library";
import { yaml } from "@codemirror/lang-yaml";
import CodeMirror from "@uiw/react-codemirror";
import { useCallback, useEffect, useState } from "react";
import styled from "styled-components";

import { api } from "../api/client";

interface Props {
	sourceFile: string;
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

export function YamlEditor({ sourceFile, onSaved }: Props) {
	const [content, setContent] = useState("");
	const [original, setOriginal] = useState("");
	const [loading, setLoading] = useState(true);
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [success, setSuccess] = useState(false);

	useEffect(() => {
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
	}, [sourceFile]);

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
