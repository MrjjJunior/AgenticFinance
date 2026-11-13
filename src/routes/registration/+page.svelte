<script>
	import { goto } from '\$app/navigation';
	import Logo from '#lib/components/Logo.svelte';

	/** @type {'manufacturer' | 'buyer' | null} */
	let selectedRole = null;
	let name = '';
	let email = '';
	let password = '';
	let showPassword = false;
	let agreed = false;

	function selectRole(role) {
		selectedRole = role;
	}

	function resetRole() {
		selectedRole = null;
	}

	async function handleSubmit() {
		if (!selectedRole) return;

		// Persist user session info for /supplier or /manufacturer
		localStorage.setItem('stocksafe_user', JSON.stringify({ role: selectedRole, name, email }));

		if (selectedRole === 'buyer') {
			await goto('/supplier');
		} else if (selectedRole === 'manufacturer') {
			await goto('/manufacturer');
		}
	}
</script>

<svelte:head>
	<title>Create your account — StockSafe</title>
</svelte:head>

<div class="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-[#FAFAFA] text-[#1A1D1B]">
	<!-- LEFT PANEL -->
	<div
		class="hidden lg:flex flex-col justify-between left-panel-gradient text-white p-12 xl:p-16 relative overflow-hidden"
	>
		<div
			class="pointer-events-none absolute -bottom-24 -right-24 w-[480px] h-[480px] rounded-full bg-[#12A150]/10 blur-3xl"
		></div>

		<div class="relative z-10">
			<Logo href="/" darkText={false} />
		</div>

		<div class="relative z-10 max-w-md my-auto">
			<h1 class="text-4xl xl:text-[44px] font-bold tracking-tight leading-[1.15] text-white mb-5">
				A smarter supply network starts here.
			</h1>
			<p class="text-[15px] leading-relaxed text-neutral-300/90">
				Create your StockSafe account to connect manufacturers and buyers with full visibility and
				protection.
			</p>
		</div>

		<div class="relative z-10 flex items-center gap-3.5">
			<div class="flex -space-x-2.5">
				<div
					class="w-8 h-8 rounded-full bg-[#D9E8DF] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-[#0D2418]"
				>
					JD
				</div>
				<div
					class="w-8 h-8 rounded-full bg-[#A8D5BA] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-[#0D2418]"
				>
					AK
				</div>
				<div
					class="w-8 h-8 rounded-full bg-[#12A150] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-white"
				>
					SM
				</div>
			</div>
			<span class="text-xs font-medium text-neutral-300">
				Trusted by <strong class="text-white font-semibold">50,000+</strong> partners
			</span>
		</div>
	</div>

	<!-- RIGHT PANEL -->
	<div class="flex flex-col items-center justify-center px-6 py-12 sm:px-12 bg-[#F7F8F7]">
		<div
			class="w-full max-w-[440px] bg-white rounded-2xl border border-neutral-200/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 sm:p-10"
		>
			<div class="mb-6">
				<Logo href="/" darkText={true} size="sm" />
			</div>

			{#if !selectedRole}
				<!-- STEP 1: CHOOSE MANUFACTURER OR BUYER -->
				<div>
					<div class="mb-6">
						<span
							class="inline-block text-[11px] font-bold uppercase tracking-wider text-[#12A150] mb-1"
						>
							Step 1 of 2
						</span>
						<h2 class="text-2xl font-bold tracking-tight text-[#1A1D1B]">
							How will you use StockSafe?
						</h2>
						<p class="text-xs text-neutral-500 mt-1.5">
							Choose your account type to continue to registration.
						</p>
					</div>

					<div class="space-y-3.5">
						<!-- Manufacturer Option -->
						<button
							type="button"
							on:click={() => selectRole('manufacturer')}
							class="w-full text-left p-4 rounded-xl border border-neutral-200 hover:border-[#12A150] hover:bg-[#F3FBF6] transition-all group flex items-start gap-4 cursor-pointer"
						>
							<div
								class="w-10 h-10 rounded-xl bg-[#E8F7EE] text-[#12A150] group-hover:bg-[#12A150] group-hover:text-white flex items-center justify-center shrink-0 transition-colors"
							>
								<svg
									class="w-5 h-5"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<path
										d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"
									/>
									<path d="M17 18h1" /><path d="M12 18h1" /><path d="M7 18h1" />
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<span class="font-bold text-sm text-[#1A1D1B]">I am a Manufacturer</span>
									<span
										class="text-neutral-400 group-hover:text-[#12A150] group-hover:translate-x-0.5 transition-all text-sm"
										>&rarr;</span
									>
								</div>
								<p class="text-xs text-neutral-500 mt-1 leading-relaxed">
									List production capacity, manage inventory, and fulfill verified buyer orders.
								</p>
							</div>
						</button>

						<!-- Buyer Option -->
						<button
							type="button"
							on:click={() => selectRole('buyer')}
							class="w-full text-left p-4 rounded-xl border border-neutral-200 hover:border-[#12A150] hover:bg-[#F3FBF6] transition-all group flex items-start gap-4 cursor-pointer"
						>
							<div
								class="w-10 h-10 rounded-xl bg-[#E8F7EE] text-[#12A150] group-hover:bg-[#12A150] group-hover:text-white flex items-center justify-center shrink-0 transition-colors"
							>
								<svg
									class="w-5 h-5"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
									<path d="M3 6h18" />
									<path d="M16 10a4 4 0 0 1-8 0" />
								</svg>
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<span class="font-bold text-sm text-[#1A1D1B]">I am a Buyer</span>
									<span
										class="text-neutral-400 group-hover:text-[#12A150] group-hover:translate-x-0.5 transition-all text-sm"
										>&rarr;</span
									>
								</div>
								<p class="text-xs text-neutral-500 mt-1 leading-relaxed">
									Discover trusted suppliers, source stock securely, and track orders in one view.
								</p>
							</div>
						</button>
					</div>
				</div>
			{:else}
				<!-- STEP 2: REGISTRATION FORM -->
				<div>
					<!-- Selected Role Banner -->
					<div
						class="flex items-center justify-between bg-[#F3FBF6] border border-[#12A150]/20 rounded-xl px-3.5 py-2.5 mb-5"
					>
						<div class="flex items-center gap-2">
							<span class="w-2 h-2 rounded-full bg-[#12A150]"></span>
							<span class="text-xs text-neutral-600">
								Registering as
								<strong class="text-[#0D2418] font-semibold capitalize">{selectedRole}</strong>
							</span>
						</div>
						<button
							type="button"
							on:click={resetRole}
							class="text-xs font-semibold text-[#12A150] hover:text-[#0e8541] hover:underline cursor-pointer"
						>
							Change
						</button>
					</div>

					<div class="mb-6">
						<h2 class="text-2xl font-bold tracking-tight text-[#1A1D1B]">Create your account</h2>
						<p class="text-xs text-neutral-500 mt-1.5">Complete your details to get started.</p>
					</div>

					<form on:submit|preventDefault={handleSubmit} class="space-y-4">
						<div>
							<label for="name" class="block text-xs font-semibold text-neutral-700 mb-1.5">
								Full name or Company name
							</label>
							<input
								type="text"
								id="name"
								bind:value={name}
								required
								placeholder={selectedRole === 'manufacturer'
									? 'e.g. Apex Manufacturing Ltd.'
									: 'e.g. Divine Lubiku / Retail Co.'}
								class="w-full px-3.5 py-2.5 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
							/>
						</div>

						<div>
							<label for="email" class="block text-xs font-semibold text-neutral-700 mb-1.5">
								Email address
							</label>
							<input
								type="email"
								id="email"
								bind:value={email}
								required
								placeholder="name@example.com"
								class="w-full px-3.5 py-2.5 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
							/>
						</div>

						<div>
							<label for="password" class="block text-xs font-semibold text-neutral-700 mb-1.5">
								Password
							</label>
							<div class="relative">
								{#if showPassword}
									<input
										type="text"
										id="password"
										bind:value={password}
										required
										placeholder="Create a strong password"
										class="w-full px-3.5 py-2.5 pr-10 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
									/>
								{:else}
									<input
										type="password"
										id="password"
										bind:value={password}
										required
										placeholder="Create a strong password"
										class="w-full px-3.5 py-2.5 pr-10 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
									/>
								{/if}
								<button
									type="button"
									on:click={() => (showPassword = !showPassword)}
									aria-label="Toggle password visibility"
									class="absolute inset-y-0 right-3 flex items-center text-neutral-400 hover:text-neutral-600 transition-colors"
								>
									<svg
										class="w-4 h-4"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
										<circle cx="12" cy="12" r="3"></circle>
									</svg>
								</button>
							</div>
						</div>

						<div class="pt-1">
							<label class="inline-flex items-start gap-2.5 cursor-pointer select-none">
								<input
									type="checkbox"
									bind:checked={agreed}
									required
									class="mt-0.5 w-3.5 h-3.5 rounded border-neutral-300 text-[#12A150] focus:ring-[#12A150]/20"
								/>
								<span class="text-xs text-neutral-600 leading-relaxed">
									I agree to the <a href="/terms" class="text-[#12A150] font-medium hover:underline"
										>Terms of Service</a
									>
									and
									<a href="/privacy" class="text-[#12A150] font-medium hover:underline"
										>Privacy Policy</a
									>.
								</span>
							</label>
						</div>

						<button
							type="submit"
							class="w-full mt-2 bg-[#0D2418] hover:bg-[#143624] text-white font-medium text-sm py-3 px-4 rounded-xl inline-flex items-center justify-center gap-2 transition-all shadow-xs cursor-pointer"
						>
							<span>Create account</span>
							<span aria-hidden="true">&rarr;</span>
						</button>
					</form>
				</div>
			{/if}

			<p class="text-center text-xs text-neutral-500 mt-6">
				Already have an account?
				<a
					href="/login"
					class="font-semibold text-[#12A150] hover:text-[#0e8541] transition-colors ml-0.5"
				>
					Sign in
				</a>
			</p>
		</div>
	</div>
</div>

<style>
	.left-panel-gradient {
		background: radial-gradient(circle at 85% 65%, #16422b 0%, #0d2418 55%, #091a11 100%);
	}
</style>
