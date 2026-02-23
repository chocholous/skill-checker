import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
	const env = loadEnv(mode, "..", "");
	const backendPort = env.BACKEND_PORT || "8420";

	return {
		plugins: [react()],
		server: {
			proxy: {
				"/api": {
					target: `http://127.0.0.1:${backendPort}`,
					changeOrigin: true,
				},
			},
		},
	};
});
