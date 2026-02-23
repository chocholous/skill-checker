import { Text, theme } from "@apify/ui-library";
import { NavLink, Outlet } from "react-router-dom";
import styled from "styled-components";

const navItems = [
	{ to: "/", label: "Dashboard", end: true },
	{ to: "/heatmap", label: "Heatmap", end: false },
	{ to: "/scenarios", label: "Scenarios", end: false },
	{ to: "/reports", label: "Reports", end: false },
];

const PageWrapper = styled.div`
    min-height: 100vh;
    background: ${theme.color.neutral.background};
`;

const NavBar = styled.nav`
    background: ${theme.color.neutral.backgroundWhite};
    border-bottom: 1px solid ${theme.color.neutral.border};
    box-shadow: ${theme.shadow.shadow1};
`;

const NavInner = styled.div`
    max-width: 128rem;
    margin: 0 auto;
    padding: 0 ${theme.space.space16};
    display: flex;
    align-items: center;
    height: 5.6rem;
    gap: ${theme.space.space32};
`;

const LogoArea = styled.div`
    display: flex;
    align-items: center;
    gap: ${theme.space.space8};
    text-decoration: none;
    flex-shrink: 0;
`;

const ApifyLogo = styled.img`
    width: 2.4rem;
    height: 2.4rem;
`;

const NavLinks = styled.div`
    display: flex;
    gap: ${theme.space.space4};
`;

const StyledNavLink = styled(NavLink)`
    display: inline-flex;
    align-items: center;
    padding: ${theme.space.space6} ${theme.space.space12};
    border-radius: ${theme.radius.radius6};
    text-decoration: none;
    font-size: 1.4rem;
    font-weight: 500;
    color: ${theme.color.neutral.textMuted};
    transition: background ${theme.transition.fastEaseInOut},
        color ${theme.transition.fastEaseInOut};

    &:hover {
        background: ${theme.color.neutral.hover};
        color: ${theme.color.neutral.text};
    }

    &.active {
        background: ${theme.color.primary.backgroundSubtle};
        color: ${theme.color.primary.text};
    }
`;

const MainContent = styled.main`
    max-width: 128rem;
    margin: 0 auto;
    padding: ${theme.space.space24} ${theme.space.space16};
`;

export function Layout() {
	return (
		<PageWrapper>
			<NavBar>
				<NavInner>
					<LogoArea>
						<ApifyLogo src="/apify-symbol.svg" alt="Apify" />
						<Text
							type="body"
							size="regular"
							weight="bold"
							color={theme.color.neutral.text}
						>
							Skill Checker
						</Text>
					</LogoArea>
					<NavLinks>
						{navItems.map((item) => (
							<StyledNavLink key={item.to} to={item.to} end={item.end}>
								{item.label}
							</StyledNavLink>
						))}
					</NavLinks>
				</NavInner>
			</NavBar>
			<MainContent>
				<Outlet />
			</MainContent>
		</PageWrapper>
	);
}
