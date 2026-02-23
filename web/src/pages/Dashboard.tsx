import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import styled from "styled-components";
import { api } from "../api/client";
import { SeverityBadge } from "../components/SeverityBadge";

const StatsGrid = styled.div`
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: ${theme.space.space16};
    margin-bottom: ${theme.space.space32};

    @media ${theme.device.tablet} {
        grid-template-columns: repeat(4, 1fr);
    }
`;

const StatCardWrapper = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    padding: ${theme.space.space16};
    display: block;
`;

const StatCardLink = styled(Link)`
    text-decoration: none;
    display: block;
`;

const StatValue = styled(Heading)`
    color: ${theme.color.primary.text};
`;

const QuickRunSection = styled.div`
    margin-bottom: ${theme.space.space32};
    padding: ${theme.space.space16};
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
`;

const ButtonRow = styled.div`
    display: flex;
    gap: ${theme.space.space8};
    margin-top: ${theme.space.space8};
`;

const RecentReportsSection = styled.div`
    margin-bottom: ${theme.space.space32};
`;

const ReportsList = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    overflow: hidden;
`;

const ReportItem = styled(Link)`
    display: flex;
    align-items: center;
    justify-content: space-between;
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

const CategoriesGrid = styled.div`
    display: grid;
    gap: ${theme.space.space16};

    @media ${theme.device.tablet} {
        grid-template-columns: repeat(2, 1fr);
    }
`;

const CategoryCard = styled.div`
    background: ${theme.color.neutral.cardBackground};
    border-radius: ${theme.radius.radius8};
    box-shadow: ${theme.shadow.shadow1};
    padding: ${theme.space.space16};
`;

const CategoryRow = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space8};
    margin-bottom: ${theme.space.space4};

    &:last-child {
        margin-bottom: 0;
    }
`;

const SectionHeading = styled.div`
    margin-bottom: ${theme.space.space12};
`;

export function Dashboard() {
	const scenarios = useQuery({
		queryKey: ["scenarios"],
		queryFn: api.getScenarios,
	});
	const categories = useQuery({
		queryKey: ["categories"],
		queryFn: api.getCategories,
	});
	const skills = useQuery({ queryKey: ["skills"], queryFn: api.getSkills });
	const reports = useQuery({ queryKey: ["reports"], queryFn: api.getReports });

	return (
		<div>
			<Heading type="titleL" as="h1" mb="space24">
				Dashboard
			</Heading>

			<StatsGrid>
				<StatCard
					label="Scenarios"
					value={scenarios.data?.length}
					href="/scenarios"
				/>
				<StatCard
					label="Skills"
					value={skills.data ? Object.keys(skills.data).length : undefined}
				/>
				<StatCard label="Categories" value={categories.data?.total} />
				<StatCard
					label="Reports"
					value={reports.data?.length}
					href="/reports"
				/>
			</StatsGrid>

			<QuickRunSection>
				<Heading type="titleS" as="h2">
					Quick Run
				</Heading>
				<ButtonRow>
					<Button to="/run" variant="primary" size="medium">
						Run All Scenarios
					</Button>
					<Button to="/run?model=haiku" variant="secondary" size="medium">
						Quick Test (Haiku)
					</Button>
				</ButtonRow>
			</QuickRunSection>

			{reports.data && reports.data.length > 0 && (
				<RecentReportsSection>
					<SectionHeading>
						<Heading type="titleS" as="h2">
							Recent Reports
						</Heading>
					</SectionHeading>
					<ReportsList>
						{reports.data.slice(0, 5).map((r) => (
							<ReportItem key={r.filename} to={`/reports/${r.filename}`}>
								<Text type="code" size="small" weight="medium">
									{r.filename}
								</Text>
								<Text
									type="body"
									size="small"
									color={theme.color.neutral.textMuted}
								>
									{r.models?.join(", ")} — {r.scenario_count} scenarios
								</Text>
							</ReportItem>
						))}
					</ReportsList>
				</RecentReportsSection>
			)}

			{categories.data && (
				<div>
					<SectionHeading>
						<Heading type="titleS" as="h2">
							Category Taxonomy
						</Heading>
					</SectionHeading>
					<CategoriesGrid>
						<CategoryCard>
							<Text
								type="body"
								size="small"
								weight="medium"
								color={theme.color.neutral.textMuted}
								as="h3"
								mb="space8"
							>
								GEN — General Quality ({Object.keys(categories.data.gen).length}
								)
							</Text>
							{Object.values(categories.data.gen).map((c) => (
								<CategoryRow key={c.id}>
									<SeverityBadge severity={c.severity} />
									<Text type="code" size="small">
										{c.id}
									</Text>
									<Text type="body" size="small">
										{c.name}
									</Text>
								</CategoryRow>
							))}
						</CategoryCard>
						<CategoryCard>
							<Text
								type="body"
								size="small"
								weight="medium"
								color={theme.color.neutral.textMuted}
								as="h3"
								mb="space8"
							>
								APF — Platform Pitfalls (
								{Object.keys(categories.data.apf).length})
							</Text>
							{Object.values(categories.data.apf).map((c) => (
								<CategoryRow key={c.id}>
									<SeverityBadge severity={c.severity} />
									<Text type="code" size="small">
										{c.id}
									</Text>
									<Text type="body" size="small">
										{c.name}
									</Text>
								</CategoryRow>
							))}
						</CategoryCard>
					</CategoriesGrid>
				</div>
			)}
		</div>
	);
}

interface StatCardProps {
	label: string;
	value?: number;
	href?: string;
}

function StatCard({ label, value, href }: StatCardProps) {
	const content = (
		<StatCardWrapper>
			<StatValue type="titleL">{value ?? "—"}</StatValue>
			<Text type="body" size="small" color={theme.color.neutral.textMuted}>
				{label}
			</Text>
		</StatCardWrapper>
	);
	if (href) {
		return <StatCardLink to={href}>{content}</StatCardLink>;
	}
	return content;
}
