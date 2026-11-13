
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		sveltekit({
			config: {
				kit: {
					adapter: {
						name: 'auto'
					}
				}
			}
		})
	]
});
