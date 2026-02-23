import { ArrowLeftIcon, PlayIcon } from "@apify/ui-icons";
import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import styled from "styled-components";
import { api } from "../api/client";
import { CategoryTag } from "../components/CategoryTag";
import { MarkdownViewer } from "../components/MarkdownViewer";

const BackLink = styled(Link)`
    display: inline-flex;
    align-items: center;
    gap: ${theme.space.space4};
    text-decoration: none;
    color: ${theme.color.primary.text};
    margin-bottom: ${theme.space.space16};

    &:hover {
        color: ${theme.color.primary.actionHover};
        text-decoration: underline;
    }
`;

const DetailCard = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    padding: ${theme.space.space24};
    margin-bottom: ${theme.space.space24};
`;

const ScenarioHeader = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space12};
    margin-bottom: ${theme.space.space8};
`;

const ScenarioIdText = styled(Text)`
    color: ${theme.color.primary.text};
`;

const MetaRow = styled.div`
    margin-bottom: ${theme.space.space16};
`;

const FieldLabel = styled(Text)`
    color: ${theme.color.neutral.textMuted};
    margin-bottom: ${theme.space.space4};
`;

const PromptBox = styled.div`
    padding: ${theme.space.space12};
    background: ${theme.color.neutral.backgroundSubtle};
    border-radius: ${theme.radius.radius6};
    border: 1px solid ${theme.color.neutral.border};
`;

const TagsRow = styled.div`
    display: flex;
    flex-wrap: wrap;
    gap: ${theme.space.space4};
    margin-top: ${theme.space.space4};
`;

const FieldSection = styled.div`
    margin-bottom: ${theme.space.space16};
`;

const SkillCard = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    padding: ${theme.space.space24};
`;

const SkillContentWrapper = styled.div`
    max-height: 60rem;
    overflow-y: auto;
    border: 1px solid ${theme.color.neutral.border};
    border-radius: ${theme.radius.radius6};
    padding: ${theme.space.space16};
    background: ${theme.color.neutral.backgroundSubtle};
    margin-top: ${theme.space.space16};
`;

export function ScenarioDetail() {
	const { id } = useParams<{ id: string }>();
	const { data: scenario, isLoading } = useQuery({
		queryKey: ["scenario", id],
		queryFn: () => api.getScenario(id!),
		enabled: !!id,
	});
	const { data: skillContent } = useQuery({
		queryKey: ["skill-content", scenario?.target_skill],
		queryFn: () => api.getSkillContent(scenario!.target_skill),
		enabled: !!scenario,
	});

	if (isLoading) {
		return (
			<Text type="body" size="regular" color={theme.color.neutral.textMuted}>
				Loading...
			</Text>
		);
	}
	if (!scenario) {
		return (
			<Text type="body" size="regular" color={theme.color.danger.text}>
				Scenario not found
			</Text>
		);
	}

	return (
		<div>
			<BackLink to="/scenarios">
				<ArrowLeftIcon size="16" />
				<Text type="body" size="small" weight="medium">
					Back to Scenarios
				</Text>
			</BackLink>

			<DetailCard>
				<ScenarioHeader>
					<ScenarioIdText type="code" size="big" weight="bold">
						{scenario.id}
					</ScenarioIdText>
					<Heading type="titleM" as="h1">
						{scenario.name}
					</Heading>
				</ScenarioHeader>

				<MetaRow>
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						Skill:{" "}
						<Text as="span" type="code" size="small">
							{scenario.target_skill}
						</Text>
						{" | "}
						File:{" "}
						<Text as="span" type="code" size="small">
							{scenario.source_file}
						</Text>
					</Text>
				</MetaRow>

				<FieldSection>
					<FieldLabel type="body" size="small" weight="medium">
						User Prompt
					</FieldLabel>
					<PromptBox>
						<Text type="body" size="small" italic>
							{scenario.prompt}
						</Text>
					</PromptBox>
				</FieldSection>

				<FieldSection>
					<FieldLabel type="body" size="small" weight="medium">
						Expected Complexities
					</FieldLabel>
					<TagsRow>
						{scenario.expected_complexities.map((c) => (
							<CategoryTag
								key={c.id}
								id={c.id}
								name={c.name}
								severity={c.severity}
								description={c.description}
							/>
						))}
					</TagsRow>
				</FieldSection>

				<Button
					to={`/run?scenario=${scenario.id}`}
					LeftIcon={PlayIcon}
					variant="primary"
					size="medium"
				>
					Run This Scenario
				</Button>
			</DetailCard>

			{skillContent && (
				<SkillCard>
					<Heading type="titleS" as="h2">
						SKILL.md Content
					</Heading>
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						{skillContent.path} ({skillContent.lines} lines)
					</Text>
					<SkillContentWrapper>
						<MarkdownViewer content={skillContent.content} />
					</SkillContentWrapper>
				</SkillCard>
			)}
		</div>
	);
}
