import { CrossIcon } from "@apify/ui-icons";
import { Button, Heading, Text, theme } from "@apify/ui-library";
import { useEffect } from "react";
import styled from "styled-components";
import { MarkdownViewer } from "./MarkdownViewer";
import { SeverityBadge } from "./SeverityBadge";

const Overlay = styled.div`
	position: fixed;
	inset: 0;
	background: ${theme.color.neutral.overlay};
	z-index: 200;
	display: flex;
	align-items: center;
	justify-content: center;
`;

const Modal = styled.div`
	position: relative;
	width: 80rem;
	max-width: 92vw;
	max-height: 90vh;
	background: ${theme.color.neutral.cardBackground};
	border-radius: ${theme.radius.radius12};
	box-shadow: ${theme.shadow.shadow4};
	display: flex;
	flex-direction: column;
	overflow: hidden;
`;

const ModalHeader = styled.div`
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: ${theme.space.space12};
	padding: ${theme.space.space16} ${theme.space.space24};
	border-bottom: 1px solid ${theme.color.neutral.border};
	background: ${theme.color.neutral.backgroundMuted};
	flex-shrink: 0;
`;

const HeaderLeft = styled.div`
	display: flex;
	align-items: center;
	gap: ${theme.space.space8};
	min-width: 0;
`;

const Breadcrumb = styled(Text)`
	color: ${theme.color.neutral.textMuted};
`;

const ModalBody = styled.div`
	flex: 1;
	overflow-y: auto;
	padding: ${theme.space.space24};

	/* Ensure markdown content renders at full width */
	& > * {
		max-width: 100%;
	}

	/* Improve markdown readability */
	line-height: 1.6;
`;

interface Props {
	checkId: string;
	checkName?: string;
	severity?: string;
	model: string;
	skillLabel: string;
	content: string;
	onClose: () => void;
}

export function AnalysisModal({
	checkId,
	checkName,
	severity,
	model,
	skillLabel,
	content,
	onClose,
}: Props) {
	// Close on Escape key
	useEffect(() => {
		const handler = (e: KeyboardEvent) => {
			if (e.key === "Escape") onClose();
		};
		document.addEventListener("keydown", handler);
		return () => document.removeEventListener("keydown", handler);
	}, [onClose]);

	return (
		<Overlay onClick={onClose}>
			<Modal onClick={(e) => e.stopPropagation()}>
				<ModalHeader>
					<HeaderLeft>
						<Breadcrumb type="code" size="small">
							{checkId}
						</Breadcrumb>
						{checkName && (
							<>
								<Breadcrumb type="body" size="small">
									/
								</Breadcrumb>
								<Text type="body" size="small" weight="bold">
									{checkName}
								</Text>
							</>
						)}
						{severity && <SeverityBadge severity={severity} />}
						<Breadcrumb type="body" size="small">
							/
						</Breadcrumb>
						<Text type="body" size="small" weight="medium">
							{model}
						</Text>
						<Breadcrumb type="body" size="small">
							/
						</Breadcrumb>
						<Heading type="titleXs" as="span">
							{skillLabel}
						</Heading>
					</HeaderLeft>
					<Button
						variant="tertiary"
						size="small"
						LeftIcon={CrossIcon}
						onClick={onClose}
					>
						Close
					</Button>
				</ModalHeader>
				<ModalBody>
					<MarkdownViewer content={content} />
				</ModalBody>
			</Modal>
		</Overlay>
	);
}
