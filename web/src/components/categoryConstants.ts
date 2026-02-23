type CategoryKey = "WF" | "DK" | "BP" | "APF" | "SEC";

export const CATEGORY_LABELS: Record<CategoryKey, string> = {
	WF: "Workflow Quality",
	DK: "Domain Knowledge",
	BP: "Best Practices",
	APF: "Apify Platform Awareness",
	SEC: "Security",
};

export const CATEGORY_ORDER: CategoryKey[] = ["WF", "DK", "BP", "APF", "SEC"];
