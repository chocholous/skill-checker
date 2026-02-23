import { Button, Chip, Heading, Tabs, Text, theme } from "@apify/ui-library";
import { yaml } from "@codemirror/lang-yaml";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import CodeMirror from "@uiw/react-codemirror";
import { useCallback, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import styled from "styled-components";
import {
	api,
	type CategoriesResponse,
	type ScenarioSummary,
} from "../api/client";
import { CategoryBadge } from "../components/CategoryBadge";
import {
	CATEGORY_LABELS,
	CATEGORY_ORDER,
} from "../components/categoryConstants";
import { YamlEditor } from "../components/YamlEditor";

/* ── styled components ── */

const PageHeader = styled.div`
	margin-bottom: ${theme.space.space24};
`;

const SubtitleText = styled(Text)`
	max-width: 720px;
`;

const StatsText = styled(Text)`
	font-style: italic;
`;

const TabsWrapper = styled.div`
	margin-bottom: ${theme.space.space24};
`;

/* ── Category legend ── */

const LegendRow = styled.div`
	display: flex;
	gap: ${theme.space.space12};
	flex-wrap: wrap;
	margin-bottom: ${theme.space.space24};
`;

const LegendCard = styled.div<{ $active?: boolean }>`
	flex: 1 1 180px;
	max-width: 260px;
	padding: ${theme.space.space12};
	background: ${({ $active }) =>
		$active
			? theme.color.primary.backgroundSubtle
			: theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	cursor: pointer;
	border-left: 3px solid
		${({ $active }) => ($active ? theme.color.primary.borderSubtle : "transparent")};
	transition:
		background ${theme.transition.fastEaseInOut},
		border-color ${theme.transition.fastEaseInOut};

	&:hover {
		background: ${({ $active }) =>
			$active
				? theme.color.primary.backgroundSubtle
				: theme.color.neutral.cardBackgroundHover};
	}
`;

const LegendCardHeader = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	margin-bottom: ${theme.space.space4};
`;

/* ── Filter bar ── */

const FilterBar = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
	flex-wrap: wrap;
	margin-bottom: ${theme.space.space16};
`;

const SearchInput = styled.input`
	padding: ${theme.space.space4} ${theme.space.space8};
	border: 1px solid ${theme.color.neutral.fieldBorder};
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.neutral.fieldBackground};
	color: ${theme.color.neutral.text};
	font-size: 1.3rem;
	flex: 1;
	min-width: 200px;
	max-width: 320px;

	&:focus {
		outline: none;
		border-color: ${theme.color.primary.fieldBorderActive};
		box-shadow: ${theme.shadow.shadowActive};
	}
`;

const NativeSelect = styled.select`
	font-size: 1.3rem;
	padding: ${theme.space.space4} ${theme.space.space8};
	border-radius: ${theme.radius.radius4};
	border: 1px solid ${theme.color.neutral.fieldBorder};
	background: ${theme.color.neutral.fieldBackground};
	color: ${theme.color.neutral.text};
	cursor: pointer;

	&:focus {
		outline: none;
		border-color: ${theme.color.primary.fieldBorderActive};
		box-shadow: ${theme.shadow.shadowActive};
	}
`;

const ResultCount = styled(Text)`
	margin-bottom: ${theme.space.space16};
`;

/* ── Category group section ── */

const GroupSection = styled.div`
	margin-bottom: ${theme.space.space32};
`;

const GroupHeader = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
	margin-bottom: ${theme.space.space4};
`;

const GroupDescription = styled(Text)`
	margin-bottom: ${theme.space.space12};
`;

/* ── Scenario card ── */

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

const CardRow1 = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	margin-bottom: ${theme.space.space4};
	flex-wrap: wrap;
`;

const CardRow2 = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	flex-wrap: wrap;
`;

const PromptToggle = styled.button`
	background: none;
	border: none;
	padding: ${theme.space.space4} 0;
	font-size: 1.2rem;
	color: ${theme.color.primary.text};
	cursor: pointer;
	margin-top: ${theme.space.space4};

	&:hover {
		text-decoration: underline;
	}
`;

const PromptText = styled(Text)`
	margin-top: ${theme.space.space4};
	white-space: pre-wrap;
`;

const Separator = styled.span`
	color: ${theme.color.neutral.textMuted};
`;

/* ── Empty state ── */

const EmptyState = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space32};
	text-align: center;
`;

/* ── Manage files view (reused from original) ── */

const ManageGroupSection = styled.div`
	margin-bottom: ${theme.space.space32};
`;

const ManageGroupHeader = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
	margin-bottom: ${theme.space.space12};
`;

const EditorWrapper = styled.div`
	margin-bottom: ${theme.space.space16};
`;

const NewFileSection = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	padding: ${theme.space.space16};
	margin-bottom: ${theme.space.space32};
`;

const NewFileControls = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
	margin-bottom: ${theme.space.space12};
`;

const StyledSelect = styled.select`
	padding: ${theme.space.space4} ${theme.space.space8};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.neutral.background};
	font-size: 1.3rem;
`;

const StyledInput = styled.input`
	padding: ${theme.space.space4} ${theme.space.space8};
	border: 1px solid ${theme.color.neutral.border};
	border-radius: ${theme.radius.radius4};
	background: ${theme.color.neutral.background};
	font-size: 1.3rem;
	flex: 1;
	max-width: 300px;
`;

const NewFileActions = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	margin-top: ${theme.space.space12};
`;

const ErrorBanner = styled.div`
	padding: ${theme.space.space8} ${theme.space.space12};
	background: ${theme.color.danger.backgroundSubtle};
	color: ${theme.color.danger.text};
	border-radius: ${theme.radius.radius4};
	font-size: 1.2rem;
	margin-top: ${theme.space.space8};
`;

const ManageScenarioList = styled.div`
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius8};
	box-shadow: ${theme.shadow.shadow1};
	overflow: hidden;
`;

const ManageScenarioItem = styled(Link)`
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

const ManageScenarioItemHeader = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space12};
	margin-bottom: ${theme.space.space4};
`;

const ManageScenarioIdText = styled(Text)`
	color: ${theme.color.primary.text};
`;

const ManageSkillLabel = styled(Text)`
	margin-left: auto;
	color: ${theme.color.neutral.textMuted};
`;

/* ── NewScenarioFile (inline, unchanged from original) ── */

function NewScenarioFile({ onCreated }: { onCreated: () => void }) {
	const { data: templates } = useQuery({
		queryKey: ["scenario-templates"],
		queryFn: api.getScenarioTemplates,
	});

	const [format, setFormat] = useState<"domain" | "category">("domain");
	const [filename, setFilename] = useState("");
	const [content, setContent] = useState("");
	const [saving, setSaving] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const handleFormatChange = useCallback(
		(newFormat: "domain" | "category") => {
			setFormat(newFormat);
			if (templates) {
				setContent(
					newFormat === "domain" ? templates.domain : templates.category,
				);
			}
		},
		[templates],
	);

	if (templates && !content) {
		setContent(format === "domain" ? templates.domain : templates.category);
	}

	const handleSave = async () => {
		const fname = filename.endsWith(".yaml") ? filename : `${filename}.yaml`;
		setSaving(true);
		setError(null);
		try {
			await api.createScenarioFile(fname, content);
			onCreated();
		} catch (e: unknown) {
			setError(String(e));
		} finally {
			setSaving(false);
		}
	};

	return (
		<NewFileSection>
			<Text type="body" size="regular" weight="bold" mb="space8">
				New Scenario File
			</Text>
			<NewFileControls>
				<StyledSelect
					value={format}
					onChange={(e) =>
						handleFormatChange(e.target.value as "domain" | "category")
					}
				>
					<option value="domain">Domain-based</option>
					<option value="category">Category-based</option>
				</StyledSelect>
				<StyledInput
					placeholder="filename (e.g. my-scenarios)"
					value={filename}
					onChange={(e) => setFilename(e.target.value)}
				/>
				<Text type="code" size="small" color={theme.color.neutral.textMuted}>
					.yaml
				</Text>
			</NewFileControls>

			<CodeMirror
				value={content}
				onChange={setContent}
				extensions={[yaml()]}
				height="300px"
				basicSetup={{ lineNumbers: true, foldGutter: true }}
			/>

			<NewFileActions>
				<Button
					size="small"
					variant="primary"
					onClick={handleSave}
					disabled={saving || !filename.trim() || !content.trim()}
				>
					{saving ? "Creating..." : "Create File"}
				</Button>
				{templates && format === "domain" && (
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						Valid domains: {templates.domains.join(", ")}
					</Text>
				)}
				{templates && format === "category" && (
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						Valid categories: {templates.categories.join(", ")}
					</Text>
				)}
			</NewFileActions>
			{error && <ErrorBanner>{error}</ErrorBanner>}
		</NewFileSection>
	);
}

/* ── Browse view components ── */

function CategoryLegend({
	categories,
	activeCategory,
	onSelect,
}: {
	categories: CategoriesResponse | undefined;
	activeCategory: string;
	onSelect: (cat: string) => void;
}) {
	if (!categories) return null;

	return (
		<LegendRow>
			{CATEGORY_ORDER.map((key) => {
				const group = categories.groups[key.toLowerCase()];
				if (!group) return null;
				const checkCount = Object.keys(group.categories).length;
				const isActive = activeCategory === key;
				return (
					<LegendCard
						key={key}
						$active={isActive}
						onClick={() => onSelect(isActive ? "" : key)}
					>
						<LegendCardHeader>
							<CategoryBadge category={key} />
							<Text type="body" size="small" weight="medium">
								{CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS]} —{" "}
								{checkCount} checks
							</Text>
						</LegendCardHeader>
						<Text
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							{group.name}
						</Text>
					</LegendCard>
				);
			})}
		</LegendRow>
	);
}

function ScenarioCard({ scenario }: { scenario: ScenarioSummary }) {
	const [showPrompt, setShowPrompt] = useState(false);

	return (
		<ScenarioItem to={`/scenarios/${scenario.id}`}>
			<CardRow1>
				<CategoryBadge category={scenario.category} />
				<Text type="code" size="small">
					{scenario.id}
				</Text>
				<Separator>&middot;</Separator>
				<Text type="body" size="regular" weight="medium">
					{scenario.name}
				</Text>
			</CardRow1>
			<CardRow2>
				<Chip type="DEFAULT" size="S">
					{scenario.target_skill}
				</Chip>
			</CardRow2>
			<PromptToggle
				onClick={(e) => {
					e.preventDefault();
					e.stopPropagation();
					setShowPrompt(!showPrompt);
				}}
			>
				{showPrompt ? "Hide prompt \u25B4" : "Show prompt \u25BE"}
			</PromptToggle>
			{showPrompt && (
				<PromptText
					type="body"
					size="small"
					color={theme.color.neutral.textMuted}
				>
					{scenario.prompt}
				</PromptText>
			)}
		</ScenarioItem>
	);
}

/* ── Main page ── */

const TABS = [
	{ id: "browse", title: "Browse Scenarios", to: "#browse" },
	{ id: "manage", title: "Manage YAML Files", to: "#manage" },
];

export function Scenarios() {
	const { data: scenarios, isLoading } = useQuery({
		queryKey: ["scenarios"],
		queryFn: api.getScenarios,
	});
	const { data: categories } = useQuery({
		queryKey: ["categories"],
		queryFn: api.getCategories,
	});

	const [activeTab, setActiveTab] = useState("browse");

	// Browse filters
	const [search, setSearch] = useState("");
	const [categoryFilter, setCategoryFilter] = useState("");
	const [skillFilter, setSkillFilter] = useState("");

	// Manage files state
	const [editingFile, setEditingFile] = useState<string | null>(null);
	const [showNewFile, setShowNewFile] = useState(false);
	const [deleting, setDeleting] = useState<string | null>(null);
	const queryClient = useQueryClient();

	const invalidateScenarios = useCallback(() => {
		queryClient.invalidateQueries({ queryKey: ["scenarios"] });
	}, [queryClient]);

	const handleDelete = useCallback(
		async (file: string) => {
			if (
				!window.confirm(`Delete file "${file}"? A .bak backup will be created.`)
			)
				return;
			setDeleting(file);
			try {
				await api.deleteScenarioFile(file);
				invalidateScenarios();
			} catch (e: unknown) {
				alert(`Failed to delete: ${e}`);
			} finally {
				setDeleting(null);
			}
		},
		[invalidateScenarios],
	);

	// Unique skills
	const uniqueSkills = useMemo(() => {
		if (!scenarios) return [];
		return [...new Set(scenarios.map((s) => s.target_skill))].sort();
	}, [scenarios]);

	// Unique category keys from scenarios
	const uniqueCategories = useMemo(() => {
		if (!scenarios) return [];
		return [...new Set(scenarios.map((s) => s.category.toUpperCase()))].sort();
	}, [scenarios]);

	const hasActiveFilters = search || categoryFilter || skillFilter;

	// Filtered scenarios
	const filteredScenarios = useMemo(() => {
		if (!scenarios) return [];
		return scenarios.filter((s) => {
			if (search) {
				const q = search.toLowerCase();
				if (
					!s.name.toLowerCase().includes(q) &&
					!s.prompt.toLowerCase().includes(q)
				)
					return false;
			}
			if (categoryFilter && s.category.toUpperCase() !== categoryFilter)
				return false;
			if (skillFilter && s.target_skill !== skillFilter) return false;
			return true;
		});
	}, [scenarios, search, categoryFilter, skillFilter]);

	// Group by category in fixed order
	const groupedByCategory = useMemo(() => {
		const groups: Array<{
			key: string;
			label: string;
			description: string;
			items: ScenarioSummary[];
		}> = [];
		for (const key of CATEGORY_ORDER) {
			const items = filteredScenarios.filter(
				(s) => s.category.toUpperCase() === key,
			);
			if (items.length === 0) continue;
			const group = categories?.groups[key.toLowerCase()];
			groups.push({
				key,
				label: CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS] ?? key,
				description: group?.name ?? "",
				items,
			});
		}
		return groups;
	}, [filteredScenarios, categories]);

	// File groups for Manage tab
	const fileGroups = useMemo(() => {
		if (!scenarios) return new Map<string, ScenarioSummary[]>();
		const groups = new Map<string, ScenarioSummary[]>();
		for (const s of scenarios) {
			const list = groups.get(s.source_file) || [];
			list.push(s);
			groups.set(s.source_file, list);
		}
		return groups;
	}, [scenarios]);

	const clearFilters = () => {
		setSearch("");
		setCategoryFilter("");
		setSkillFilter("");
	};

	if (isLoading) {
		return (
			<Text type="body" size="regular" color={theme.color.neutral.textMuted}>
				Loading...
			</Text>
		);
	}
	if (!scenarios) return null;

	return (
		<div>
			{/* Page header */}
			<PageHeader>
				<Heading type="titleL" as="h1" mb="space8">
					Scenarios
				</Heading>
				<SubtitleText
					type="body"
					size="regular"
					color={theme.color.neutral.textMuted}
					mb="space4"
				>
					Test prompts that verify how well SKILL.md files prepare an AI agent
					for real user requests. Each scenario targets a specific skill and
					checks for known failure patterns across quality categories.
				</SubtitleText>
				<StatsText
					type="body"
					size="small"
					color={theme.color.neutral.textMuted}
				>
					{scenarios.length} scenarios &middot; {uniqueSkills.length} skills
					&middot; {uniqueCategories.length} categories
				</StatsText>
			</PageHeader>

			{/* Tabs */}
			<TabsWrapper>
				<Tabs
					tabs={TABS}
					variant="default"
					activeTab={activeTab}
					onSelect={({ id }) => setActiveTab(id)}
				/>
			</TabsWrapper>

			{/* Browse view */}
			{activeTab === "browse" && (
				<>
					{/* Category legend */}
					<CategoryLegend
						categories={categories}
						activeCategory={categoryFilter}
						onSelect={(cat) => setCategoryFilter(cat)}
					/>

					{/* Filter bar */}
					<FilterBar>
						<SearchInput
							placeholder="Search by name or prompt..."
							value={search}
							onChange={(e) => setSearch(e.target.value)}
						/>
						<NativeSelect
							value={categoryFilter}
							onChange={(e) => setCategoryFilter(e.target.value)}
						>
							<option value="">All categories</option>
							{CATEGORY_ORDER.map((key) => (
								<option key={key} value={key}>
									{key} — {CATEGORY_LABELS[key as keyof typeof CATEGORY_LABELS]}
								</option>
							))}
						</NativeSelect>
						<NativeSelect
							value={skillFilter}
							onChange={(e) => setSkillFilter(e.target.value)}
						>
							<option value="">All skills</option>
							{uniqueSkills.map((skill) => (
								<option key={skill} value={skill}>
									{skill}
								</option>
							))}
						</NativeSelect>
						{hasActiveFilters && (
							<Button variant="tertiary" size="small" onClick={clearFilters}>
								Clear filters
							</Button>
						)}
					</FilterBar>

					{/* Result count */}
					{hasActiveFilters && (
						<ResultCount
							type="body"
							size="small"
							color={theme.color.neutral.textMuted}
						>
							Showing {filteredScenarios.length} of {scenarios.length} scenarios
						</ResultCount>
					)}

					{/* Category-grouped list */}
					{groupedByCategory.length > 0 ? (
						groupedByCategory.map((group) => (
							<GroupSection key={group.key}>
								<GroupHeader>
									<CategoryBadge category={group.key} />
									<Heading type="titleS" as="h2">
										{group.label}
									</Heading>
									<Text
										type="body"
										size="small"
										color={theme.color.neutral.textMuted}
									>
										&middot; {group.items.length} scenarios
									</Text>
								</GroupHeader>
								{group.description && (
									<GroupDescription
										type="body"
										size="small"
										color={theme.color.neutral.textMuted}
									>
										{group.description}
									</GroupDescription>
								)}
								<ScenarioList>
									{group.items.map((s) => (
										<ScenarioCard key={s.id} scenario={s} />
									))}
								</ScenarioList>
							</GroupSection>
						))
					) : (
						<EmptyState>
							<Heading type="titleS" as="h3" mb="space8">
								No matching scenarios
							</Heading>
							<Text
								type="body"
								size="regular"
								color={theme.color.neutral.textMuted}
								mb="space16"
							>
								Try adjusting your filters or search query.
							</Text>
							<Button variant="secondary" size="small" onClick={clearFilters}>
								Clear filters
							</Button>
						</EmptyState>
					)}
				</>
			)}

			{/* Manage Files view */}
			{activeTab === "manage" && (
				<>
					<div
						style={{
							display: "flex",
							justifyContent: "flex-end",
							marginBottom: theme.space.space16,
						}}
					>
						<Button
							size="small"
							variant={showNewFile ? "secondary" : "primary"}
							onClick={() => setShowNewFile(!showNewFile)}
						>
							{showNewFile ? "Cancel" : "New Scenario File"}
						</Button>
					</div>

					{showNewFile && (
						<NewScenarioFile
							onCreated={() => {
								setShowNewFile(false);
								invalidateScenarios();
							}}
						/>
					)}

					{Array.from(fileGroups.entries()).map(([file, items]) => (
						<ManageGroupSection key={file}>
							<ManageGroupHeader>
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
									onClick={() =>
										setEditingFile(editingFile === file ? null : file)
									}
								>
									{editingFile === file ? "Close Editor" : "Edit YAML"}
								</Button>
								<Button
									size="small"
									variant="secondary"
									color="danger"
									onClick={() => handleDelete(file)}
									disabled={deleting === file}
								>
									{deleting === file ? "Deleting..." : "Delete"}
								</Button>
							</ManageGroupHeader>

							{editingFile === file && (
								<EditorWrapper>
									<YamlEditor sourceFile={file} onSaved={invalidateScenarios} />
								</EditorWrapper>
							)}

							<ManageScenarioList>
								{items.map((s) => (
									<ManageScenarioItem key={s.id} to={`/scenarios/${s.id}`}>
										<ManageScenarioItemHeader>
											<ManageScenarioIdText
												type="code"
												size="small"
												weight="bold"
											>
												{s.id}
											</ManageScenarioIdText>
											<Text type="body" size="regular" weight="medium">
												{s.name}
											</Text>
											<ManageSkillLabel type="body" size="small">
												{s.target_skill}
											</ManageSkillLabel>
										</ManageScenarioItemHeader>
									</ManageScenarioItem>
								))}
							</ManageScenarioList>
						</ManageGroupSection>
					))}
				</>
			)}
		</div>
	);
}
