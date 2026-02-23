import { Badge, Text, theme } from "@apify/ui-library";
import { useEffect, useState } from "react";
import styled, { css, keyframes } from "styled-components";

interface Props {
	scenarioIds: string[];
	models: string[];
	progress: Record<string, Record<string, string>>;
	isRunning: boolean;
}

const pulseKeyframe = keyframes`
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
`;

const ProgressBarContainer = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space12};
    margin-bottom: ${theme.space.space12};
`;

const ProgressTrack = styled.div`
    flex: 1;
    height: 0.8rem;
    background: ${theme.color.neutral.backgroundMuted};
    border-radius: ${theme.radius.radiusFull};
    overflow: hidden;
`;

const ProgressFill = styled.div<{ $pct: number }>`
    height: 100%;
    background: ${theme.color.primary.action};
    border-radius: ${theme.radius.radiusFull};
    transition: width 0.3s ease-in-out;
    width: ${({ $pct }) => $pct}%;
`;

const HintText = styled.div`
    margin-bottom: ${theme.space.space8};
`;

const TableWrapper = styled.div`
    overflow-x: auto;
`;

const StyledTable = styled.table`
    border-collapse: collapse;
    font-size: 1.2rem;
`;

const Th = styled.th<{ $center?: boolean }>`
    padding: ${theme.space.space4} ${theme.space.space12};
    color: ${theme.color.neutral.textMuted};
    font-weight: 500;
    text-align: ${({ $center }) => ($center ? "center" : "left")};
    white-space: nowrap;
`;

const Td = styled.td<{ $center?: boolean }>`
    padding: ${theme.space.space4} ${theme.space.space12};
    text-align: ${({ $center }) => ($center ? "center" : "left")};
    white-space: nowrap;
`;

const MonoCell = styled(Td)`
    font-family: 'IBM Plex Mono', Consolas, 'Liberation Mono', Menlo, monospace;
    font-size: 1.2rem;
    color: ${theme.color.neutral.text};
`;

const PulsingBadgeWrapper = styled.span`
    display: inline-flex;
    animation: ${css`${pulseKeyframe}`} 1.5s ease-in-out infinite;
`;

type StatusVariant = "neutral" | "primary_blue" | "success" | "danger";

const statusVariantMap: Record<string, StatusVariant> = {
	pending: "neutral",
	running: "primary_blue",
	ok: "success",
	error: "danger",
};

function StatusBadge({ status }: { status: string }) {
	const variant = statusVariantMap[status] ?? "neutral";
	if (status === "running") {
		return (
			<PulsingBadgeWrapper>
				<Badge size="small" variant={variant}>
					{status}
				</Badge>
			</PulsingBadgeWrapper>
		);
	}
	return (
		<Badge size="small" variant={variant}>
			{status}
		</Badge>
	);
}

function ElapsedTimer({ running }: { running: boolean }) {
	const [seconds, setSeconds] = useState<number | null>(null);

	useEffect(() => {
		if (!running) {
			return;
		}
		const interval = setInterval(() => setSeconds((s) => (s ?? 0) + 1), 1000);
		return () => clearInterval(interval);
	}, [running]);

	if (seconds === null) return null;
	const m = Math.floor(seconds / 60);
	const s = seconds % 60;
	return (
		<Text type="body" size="small" color={theme.color.neutral.textMuted}>
			{m}:{s.toString().padStart(2, "0")}
		</Text>
	);
}

export function RunProgress({
	scenarioIds,
	models,
	progress,
	isRunning,
}: Props) {
	const total = scenarioIds.length * models.length;
	const completed = Object.values(progress)
		.flatMap((m) => Object.values(m))
		.filter((s) => s === "ok" || s === "error").length;
	const running = Object.values(progress)
		.flatMap((m) => Object.values(m))
		.filter((s) => s === "running").length;
	const pct = total ? (completed / total) * 100 : 0;

	return (
		<div>
			<ProgressBarContainer>
				<ProgressTrack>
					<ProgressFill $pct={pct} />
				</ProgressTrack>
				<Text type="body" size="small" color={theme.color.neutral.textMuted}>
					{completed}/{total}
					{running > 0 && (
						<Text
							as="span"
							type="body"
							size="small"
							color={theme.color.primary.text}
						>
							{" "}
							({running} running)
						</Text>
					)}
				</Text>
				<ElapsedTimer running={isRunning} />
			</ProgressBarContainer>

			{isRunning && completed === 0 && (
				<HintText>
					<Text type="body" size="small" color={theme.color.neutral.textMuted}>
						claude -p calls can take 1-3 min each (especially opus). Be patient.
					</Text>
				</HintText>
			)}

			<TableWrapper>
				<StyledTable>
					<thead>
						<tr>
							<Th>Scenario</Th>
							{models.map((m) => (
								<Th key={m} $center>
									{m}
								</Th>
							))}
						</tr>
					</thead>
					<tbody>
						{scenarioIds.map((sid) => (
							<tr key={sid}>
								<MonoCell>{sid}</MonoCell>
								{models.map((m) => {
									const status = progress[sid]?.[m] || "pending";
									return (
										<Td key={m} $center>
											<StatusBadge status={status} />
										</Td>
									);
								})}
							</tr>
						))}
					</tbody>
				</StyledTable>
			</TableWrapper>
		</div>
	);
}
