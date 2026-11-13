<script>
	import Logo from '#lib/components/Logo.svelte';
</script>

<header
	class="relative z-10 max-w-7xl w-full mx-auto px-6 md:px-12 pt-8 flex items-center justify-between"
>
	<!-- Logo -->
	<Logo href="/#top" darkText={true} />

	<!-- Navigation Links & Actions -->
	<nav class="flex items-center gap-6 md:gap-8 text-sm font-medium text-neutral-700">
		<a href="/#why-stocksafe" class="hover:text-neutral-950 transition-colors">Why StockSafe</a>
		<a href="/login" class="hover:text-neutral-950 transition-colors">Log in</a>
		<a
			href="/registration"
			class="inline-flex items-center gap-2 bg-[#141715] hover:bg-neutral-800 text-white px-5 py-2.5 rounded-full text-sm font-medium transition-all shadow-sm"
		>
			<span>Sign up</span>
			<span aria-hidden="true">&rarr;</span>
		</a>
	</nav>
</header>
