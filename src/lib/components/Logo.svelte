<script>
	export let href = '/';
	export let darkText = true;
	export let size = 'md'; // 'sm' | 'md'
</script>

<a {href} class="inline-flex items-center gap-2.5 group">
	<span
		class="{size === 'sm'
			? 'w-6 h-6'
			: 'w-7 h-7'} rounded-full bg-[#12A150] flex items-center justify-center text-white shadow-xs group-hover:scale-105 transition-transform"
	>
		<svg
			class={size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4'}
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
		>
			<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
			<polyline points="16 7 22 7 22 13"></polyline>
		</svg>
	</span>
	<span
		class="font-bold {size === 'sm' ? 'text-[15px]' : 'text-[16px]'} tracking-tight {darkText
			? 'text-neutral-900'
			: 'text-white'}"
	>
		StockSafe
	</span>
</a>
