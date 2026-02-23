import { Heading, Text, theme } from "@apify/ui-library";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import styled from "styled-components";
import { api } from "../api/client";

const PageTitle = styled(Heading)`
	margin-bottom: ${theme.space.space24};
`;

const EmptyState = styled.div`
	padding: ${theme.space.space40};
	text-align: center;
	background: ${theme.color.neutral.cardBackground};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
`;

const EmptyLink = styled(Link)`
	color: ${theme.color.primary.text};
	text-decoration: none;

	&:hover {
		text-decoration: underline;
	}
`;

const ReportList = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	overflow: hidden;
`;

const ReportItem = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: ${theme.space.space12} ${theme.space.space16};
	border-bottom: 1px solid ${theme.color.neutral.separatorSubtle};
	transition: background ${theme.transition.fastEaseInOut};

	&:last-child {
		border-bottom: none;
	}

	&:hover {
		background: ${theme.color.neutral.hover};
	}
`;

const ReportLink = styled(Link)`
	flex: 1;
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	text-decoration: none;
	min-width: 0;
`;

const ReportFilename = styled.span`
	font-family: "IBM Plex Mono", monospace;
	font-size: 1.3rem;
	font-weight: 500;
	color: ${theme.color.neutral.text};
`;

const ReportMeta = styled.span`
	font-size: 1.2rem;
	color: ${theme.color.neutral.textMuted};
	white-space: nowrap;
`;

const DeleteButton = styled.button`
	background: none;
	border: none;
	cursor: pointer;
	font-size: 1.2rem;
	color: ${theme.color.danger.text};
	padding: ${theme.space.space4} ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	transition: background ${theme.transition.fastEaseInOut},
		color ${theme.transition.fastEaseInOut};

	&:hover {
		background: ${theme.color.danger.backgroundSubtle};
		color: ${theme.color.danger.text};
	}

	&:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
`;

const LoadingText = styled(Text)`
	color: ${theme.color.neutral.textMuted};
`;

export function Reports() {
	const queryClient = useQueryClient();
	const { data: reports, isLoading } = useQuery({
		queryKey: ["reports"],
		queryFn: api.getReports,
	});

	const deleteMutation = useMutation({
		mutationFn: api.deleteReport,
		onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports"] }),
	});

	if (isLoading) return <LoadingText type="body">Loading...</LoadingText>;
	if (!reports) return null;

	return (
		<div>
			<PageTitle type="titleL" as="h1">
				Reports
			</PageTitle>

			{reports.length === 0 ? (
				<EmptyState>
					<Text type="body" color={theme.color.neutral.textMuted}>
						No reports yet. <EmptyLink to="/run">Run some scenarios</EmptyLink>{" "}
						to generate reports.
					</Text>
				</EmptyState>
			) : (
				<ReportList>
					{reports.map((r) => (
						<ReportItem key={r.filename}>
							<ReportLink to={`/reports/${r.filename}`}>
								<ReportFilename>{r.filename}</ReportFilename>
								<ReportMeta>
									{r.models?.join(", ")} — {r.scenario_count} scenarios
								</ReportMeta>
							</ReportLink>
							<DeleteButton
								onClick={(e) => {
									e.preventDefault();
									if (confirm(`Delete ${r.filename}?`)) {
										deleteMutation.mutate(r.filename);
									}
								}}
								disabled={deleteMutation.isPending}
							>
								Delete
							</DeleteButton>
						</ReportItem>
					))}
				</ReportList>
			)}
		</div>
	);
}
