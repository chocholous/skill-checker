import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";
import { api, type ScenarioSummary } from "../api/client";
import { CategoryTag } from "../components/CategoryTag";
import { YamlEditor } from "../components/YamlEditor";

const GroupSection = styled.div`
    margin-bottom: ${theme.space.space32};
`;

const GroupHeader = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space12};
    margin-bottom: ${theme.space.space12};
`;

const EditorWrapper = styled.div`
    margin-bottom: ${theme.space.space16};
`;

const ScenarioList = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    overflow: hidden;
`;

const ScenarioItem = styled(Link)`
    display: block;
    padding: ${theme.space.space12} ${theme.space.space16};
    text-decoration: none;
    border-bottom: 1px solid ${theme.color.neutral.separatorSubtle};

    &:last-child {
        border-bottom: none;
    }

    &:hover {
        background: ${theme.color.neutral.cardBackgroundHover};
    }
`;

const ScenarioItemHeader = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space12};
    margin-bottom: ${theme.space.space4};
`;

const ScenarioIdText = styled(Text)`
    color: ${theme.color.primary.text};
`;

const SkillLabel = styled(Text)`
    margin-left: auto;
    color: ${theme.color.neutral.textMuted};
`;

const TagsRow = styled.div`
    display: flex;
    flex-wrap: wrap;
    gap: ${theme.space.space4};
    margin-top: ${theme.space.space8};
`;

const PromptText = styled(Text)`
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
`;

export function Scenarios() {
	const { data: scenarios, isLoading } = useQuery({
		queryKey: ["scenarios"],
		queryFn: api.getScenarios,
	});
	const [editingFile, setEditingFile] = useState<string | null>(null);
	const queryClient = useQueryClient();

	if (isLoading) {
		return (
			<Text type="body" size="regular" color={theme.color.neutral.textMuted}>
				Loading...
			</Text>
		);
	}
	if (!scenarios) return null;

	const groups = new Map<string, ScenarioSummary[]>();
	for (const s of scenarios) {
		const list = groups.get(s.source_file) || [];
		list.push(s);
		groups.set(s.source_file, list);
	}

	return (
		<div>
			<Heading type="titleL" as="h1" mb="space8">
				Scenarios
			</Heading>
			<Text
				type="body"
				size="regular"
				color={theme.color.neutral.textMuted}
				mb="space24"
			>
				{scenarios.length} scenarios across {groups.size} files
			</Text>

			{Array.from(groups.entries()).map(([file, items]) => (
				<GroupSection key={file}>
					<GroupHeader>
						<Text type="code" size="small" weight="medium">
							{file}
						</Text>
						<Text
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							{items.length} scenarios
						</Text>
						<Button
							size="small"
							variant="secondary"
							onClick={() => setEditingFile(editingFile === file ? null : file)}
						>
							{editingFile === file ? "Close Editor" : "Edit YAML"}
						</Button>
					</GroupHeader>

					{editingFile === file && (
						<EditorWrapper>
							<YamlEditor
								sourceFile={file}
								onSaved={() =>
									queryClient.invalidateQueries({ queryKey: ["scenarios"] })
								}
							/>
						</EditorWrapper>
					)}

					<ScenarioList>
						{items.map((s) => (
							<ScenarioItem key={s.id} to={`/scenarios/${s.id}`}>
								<ScenarioItemHeader>
									<ScenarioIdText type="code" size="small" weight="bold">
										{s.id}
									</ScenarioIdText>
									<Text type="body" size="regular" weight="medium">
										{s.name}
									</Text>
									<SkillLabel type="body" size="small">
										{s.target_skill}
									</SkillLabel>
								</ScenarioItemHeader>
								<PromptText
									type="body"
									size="small"
									color={theme.color.neutral.textMuted}
								>
									{s.prompt}
								</PromptText>
								<TagsRow>
									{s.expected_complexities.map((c) => (
										<CategoryTag
											key={c.id}
											id={c.id}
											name={c.name}
											severity={c.severity}
											description={c.description}
										/>
									))}
								</TagsRow>
							</ScenarioItem>
						))}
					</ScenarioList>
				</GroupSection>
			))}
		</div>
	);
}
