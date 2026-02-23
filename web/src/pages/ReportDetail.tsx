import { ArrowLeftIcon } from "@apify/ui-icons";
import { Heading, Text, theme } from "@apify/ui-library";
import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import styled from "styled-components";
import { api } from "../api/client";
import { MarkdownViewer } from "../components/MarkdownViewer";

const BackLink = styled(Link)`
	display: inline-flex;
	align-items: center;
	gap: ${theme.space.space4};
	color: ${theme.color.primary.text};
	text-decoration: none;
	font-size: 1.3rem;
	margin-bottom: ${theme.space.space16};
	transition: color ${theme.transition.fastEaseInOut};

	&:hover {
		color: ${theme.color.primary.textInteractive};
	}
`;

const ContentCard = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space24};
`;

const FilenameHeading = styled(Heading)`
	font-family: "IBM Plex Mono", monospace;
	margin-bottom: ${theme.space.space16};
`;

const ErrorBox = styled.div`
	color: ${theme.color.danger.text};
	background: ${theme.color.danger.backgroundSubtle};
	border: 1px solid ${theme.color.danger.borderSubtle};
	border-radius: ${theme.radius.radius8};
	padding: ${theme.space.space16};
	font-size: 1.3rem;
`;

const JsonPre = styled.pre`
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.2rem;
	overflow: auto;
	padding: ${theme.space.space16};
	background: ${theme.color.neutral.backgroundMuted};
	border-radius: ${theme.radius.radius8};
	color: ${theme.color.neutral.text};
`;

const LoadingText = styled(Text)`
	color: ${theme.color.neutral.textMuted};
`;

export function ReportDetail() {
	const { filename } = useParams<{ filename: string }>();

	const {
		data: report,
		isLoading,
		error,
	} = useQuery({
		queryKey: ["report", filename],
		queryFn: () => api.getReport(filename!),
		enabled: !!filename,
	});

	if (isLoading) return <LoadingText type="body">Loading...</LoadingText>;
	if (error) return <ErrorBox>Error: {String(error)}</ErrorBox>;
	if (!report) return null;

	return (
		<div>
			<BackLink to="/reports">
				<ArrowLeftIcon size="16" />
				Back to Reports
			</BackLink>

			<ContentCard>
				<FilenameHeading type="titleM" as="h1">
					{filename}
				</FilenameHeading>
				{"content" in report ? (
					<MarkdownViewer content={report.content} />
				) : (
					<JsonPre>{JSON.stringify(report, null, 2)}</JsonPre>
				)}
			</ContentCard>
		</div>
	);
}
