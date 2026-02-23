import {
	cssColorsVariablesLight,
	cssColorsVariablesPaletteLight,
	UiDependencyProvider,
} from "@apify/ui-library";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { forwardRef } from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { createGlobalStyle } from "styled-components";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { ReportDetail } from "./pages/ReportDetail";
import { Reports } from "./pages/Reports";
import { Run } from "./pages/Run";
import { ScenarioDetail } from "./pages/ScenarioDetail";
import { Scenarios } from "./pages/Scenarios";

const GlobalStyle = createGlobalStyle`
    :root {
        ${cssColorsVariablesLight}
        ${cssColorsVariablesPaletteLight}
        --shadow-active: 0 0 0 3px var(--color-primary-shadow-active);
        --shadow-1: 0 1px 2px rgba(0, 0, 0, 0.06);
        --shadow-2: 0 2px 4px rgba(0, 0, 0, 0.08);
        --shadow-3: 0 4px 8px rgba(0, 0, 0, 0.1);
        --shadow-4: 0 8px 16px rgba(0, 0, 0, 0.12);
        --shadow-5: 0 16px 32px rgba(0, 0, 0, 0.16);
    }
    html { font-size: 62.5%; }
    body {
        font-family: 'Inter', sans-serif;
        font-size: 1.4rem;
        line-height: 1.5;
        color: var(--color-neutral-text);
        background: var(--color-neutral-background);
        margin: 0;
    }
    *, *::before, *::after { box-sizing: border-box; }
    code, pre { font-family: 'IBM Plex Mono', Consolas, 'Liberation Mono', Menlo, monospace; }
`;

const InternalLink = forwardRef<
	HTMLAnchorElement,
	React.AnchorHTMLAttributes<HTMLAnchorElement> & { href?: string }
>(({ href, ...props }, ref) => <Link ref={ref} to={href ?? "/"} {...props} />);
InternalLink.displayName = "InternalLink";

const InternalImage = forwardRef<
	HTMLImageElement,
	React.ImgHTMLAttributes<HTMLImageElement>
>((props, ref) => <img ref={ref} {...props} />);
InternalImage.displayName = "InternalImage";

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			staleTime: 30_000,
			retry: 1,
		},
	},
});

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<BrowserRouter>
				<GlobalStyle />
				<UiDependencyProvider
					dependencies={{
						InternalLink,
						InternalImage,
						windowLocationHost: window.location.host,
						isHrefTrusted: () => true,
						tooltipSafeHtml: (content) => content,
						uiTheme: "LIGHT",
					}}
				>
					<Routes>
						<Route element={<Layout />}>
							<Route index element={<Dashboard />} />
							<Route path="scenarios" element={<Scenarios />} />
							<Route path="scenarios/:id" element={<ScenarioDetail />} />
							<Route path="run" element={<Run />} />
							<Route path="reports" element={<Reports />} />
							<Route path="reports/:filename" element={<ReportDetail />} />
						</Route>
					</Routes>
				</UiDependencyProvider>
			</BrowserRouter>
		</QueryClientProvider>
	);
}

export default App;
