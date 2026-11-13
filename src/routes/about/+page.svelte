<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
	<head>
		<meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width, initial-scale=1.0" />
		<title>StockSafe — Grow your wealth. Keep it safe.</title>
		<script src="https://cdn.tailwindcss.com"></script>
		<link
			href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"
			rel="stylesheet"
		/>
		<style>
			body {
				font-family: 'Plus Jakarta Sans', sans-serif;
			}
			.hero-gradient {
				background: radial-gradient(
					circle at 15% 55%,
					rgba(209, 244, 224, 0.65) 0%,
					rgba(242, 250, 245, 0.4) 45%,
					#ffffff 100%
				);
			}
		</style>
	</head>
	<body
		class="bg-white text-[#1A1D1B] antialiased selection:bg-emerald-100 selection:text-emerald-900"
	>
		<!-- =========================================================
       SECTION 1: HERO SECTION
  ========================================================= -->
		<section
			id="top"
			class="relative min-h-screen overflow-hidden hero-gradient flex flex-col justify-between"
		>
			<!-- Subtle Concentric Circles on the Right -->
			<div
				class="pointer-events-none absolute -right-24 top-1/2 -translate-y-1/2 w-[520px] h-[520px] rounded-full border border-emerald-900/[0.04]"
			></div>
			<div
				class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 w-[340px] h-[340px] rounded-full border border-emerald-900/[0.04]"
			></div>

			<!-- Navigation Bar -->
			<header
				class="relative z-10 max-w-7xl w-full mx-auto px-6 md:px-12 pt-8 flex items-center justify-between"
			>
				<!-- Original StockSafe Logo (Green circle + upward trend arrow) -->
				<a href="#top" class="flex items-center gap-2.5 group">
					<span
						class="w-7 h-7 rounded-full bg-[#12A150] flex items-center justify-center text-white shadow-xs group-hover:scale-105 transition-transform"
					>
						<svg
							class="w-4 h-4"
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
					<span class="font-bold text-[16px] tracking-tight text-neutral-900">StockSafe</span>
				</a>

				<!-- Navigation Links -->
				<nav class="flex items-center gap-6 md:gap-8 text-sm font-medium text-neutral-700">
					<a href="#why-stocksafe" class="hover:text-neutral-950 transition-colors">Why StockSafe</a
					>
					<a href="/login" class="hover:text-neutral-950 transition-colors">Log in</a>
					<a
						href="/signup"
						class="inline-flex items-center gap-2 bg-[#141715] hover:bg-neutral-800 text-white px-5 py-2.5 rounded-full text-sm font-medium transition-all shadow-sm"
					>
						<span>Sign up</span>
						<span aria-hidden="true">&rarr;</span>
					</a>
				</nav>
			</header>

			<!-- Center Headline with Yellow Accent Lines -->
			<main class="relative z-10 w-full my-auto py-16">
				<div class="relative flex flex-col items-center justify-center text-center px-4">
					<h1
						class="text-4xl sm:text-6xl md:text-[64px] font-bold tracking-tight leading-[1.1] text-[#1A1D1B]"
					>
						Grow your wealth.
					</h1>

					<!-- Second Line + Flanking Horizontal Gold/Yellow Lines -->
					<div class="relative w-full flex items-center justify-center mt-1">
						<!-- Left Yellow Lines -->
						<div class="hidden sm:flex flex-col gap-1.5 flex-1 max-w-[34%] mr-4">
							<div class="h-[2px] w-full bg-[#F5C542] rounded-full"></div>
							<div class="h-[1.5px] w-4/5 ml-auto bg-[#F5C542]/70 rounded-full"></div>
						</div>

						<span
							class="text-4xl sm:text-6xl md:text-[64px] font-bold tracking-tight leading-[1.1] text-[#12A150] shrink-0"
						>
							Keep it safe.
						</span>

						<!-- Right Yellow Line -->
						<div class="hidden sm:flex flex-1 max-w-[34%] ml-4">
							<div class="h-[2px] w-full bg-[#F5C542] rounded-full"></div>
						</div>
					</div>
				</div>
			</main>

			<!-- Bottom Left Subcopy -->
			<div class="relative z-10 max-w-7xl w-full mx-auto px-6 md:px-12 pb-16">
				<p class="max-w-sm text-sm md:text-[15px] leading-relaxed text-neutral-600">
					Smart investing meets serious protection. Build a portfolio that performs—with guardrails
					that help you sleep at night.
				</p>
			</div>
		</section>

		<!-- =========================================================
       SECTION 2: WHY STOCKSAFE (/about)
  ========================================================= -->
		<section id="why-stocksafe" class="bg-[#FAFAFA] py-24 md:py-32 border-t border-neutral-100">
			<div class="max-w-7xl mx-auto px-6 md:px-12">
				<!-- Eyebrow Label -->
				<span class="block text-xs font-bold uppercase tracking-[0.12em] text-[#12A150] mb-4">
					WHY STOCKSAFE
				</span>

				<!-- Two-Column Header -->
				<div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-end mb-16">
					<div class="lg:col-span-6">
						<h2
							class="text-3xl sm:text-4xl md:text-[42px] font-bold tracking-tight leading-[1.15] text-[#1A1D1B]"
						>
							Built for growth.<br />
							Designed for peace of mind.
						</h2>
					</div>
					<div class="lg:col-span-5 lg:col-start-8">
						<p class="text-[15px] leading-relaxed text-neutral-500">
							Markets move fast. Your strategy shouldn't depend on watching every tick. StockSafe
							helps you invest with clarity, confidence, and intelligent protection.
						</p>
					</div>
				</div>

				<!-- 3 Feature Cards Grid -->
				<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
					<!-- Card 1: Light -->
					<div
						class="bg-white rounded-2xl p-8 md:p-9 border border-neutral-200/70 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow"
					>
						<div>
							<!-- Icon Badge -->
							<div
								class="w-10 h-10 rounded-xl bg-[#E8F7EE] text-[#12A150] flex items-center justify-center mb-10"
							>
								<svg
									class="w-5 h-5"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2.2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
									<polyline points="16 7 22 7 22 13"></polyline>
								</svg>
							</div>
							<h3 class="text-lg font-bold text-[#1A1D1B] mb-3">Invest with intelligence</h3>
							<p class="text-sm leading-relaxed text-neutral-500 mb-8">
								Personalized insights turn noisy market data into clear, actionable opportunities.
							</p>
						</div>
						<a
							href="#security"
							class="inline-flex items-center gap-1.5 text-sm font-semibold text-[#12A150] hover:text-[#0e8541] transition-colors group"
						>
							<span>Learn more</span>
							<span class="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
						</a>
					</div>

					<!-- Card 2: Dark Highlighted Center Card -->
					<div
						class="bg-[#0D2418] rounded-2xl p-8 md:p-9 text-white shadow-lg flex flex-col justify-between"
					>
						<div>
							<!-- Icon Badge -->
							<div
								class="w-10 h-10 rounded-xl bg-[#12A150] text-white flex items-center justify-center mb-10"
							>
								<svg
									class="w-5 h-5"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2.2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
									<polyline points="9 12 11 14 15 10"></polyline>
								</svg>
							</div>
							<h3 class="text-lg font-bold text-white mb-3">Protection that works</h3>
							<p class="text-sm leading-relaxed text-neutral-300 mb-8">
								Automated guardrails monitor risk and alert you before small shifts become big
								surprises.
							</p>
						</div>
						<a
							href="#security"
							class="inline-flex items-center gap-1.5 text-sm font-semibold text-[#1CD16A] hover:text-[#3ee385] transition-colors group"
						>
							<span>Learn more</span>
							<span class="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
						</a>
					</div>

					<!-- Card 3: Light -->
					<div
						class="bg-white rounded-2xl p-8 md:p-9 border border-neutral-200/70 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow"
					>
						<div>
							<!-- Icon Badge -->
							<div
								class="w-10 h-10 rounded-xl bg-[#E8F7EE] text-[#12A150] flex items-center justify-center mb-10"
							>
								<svg
									class="w-5 h-5"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2.2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path>
									<path d="M22 12A10 10 0 0 0 12 2v10z"></path>
								</svg>
							</div>
							<h3 class="text-lg font-bold text-[#1A1D1B] mb-3">Everything in one view</h3>
							<p class="text-sm leading-relaxed text-neutral-500 mb-8">
								Track every holding, goal, and market move from one beautifully simple dashboard.
							</p>
						</div>
						<a
							href="#security"
							class="inline-flex items-center gap-1.5 text-sm font-semibold text-[#12A150] hover:text-[#0e8541] transition-colors group"
						>
							<span>Learn more</span>
							<span class="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
						</a>
					</div>
				</div>
			</div>
		</section>

		<!-- =========================================================
       SECTION 3: SECURITY & INTEGRATED FOOTER
  ========================================================= -->
		<footer id="security" class="bg-[#0D2418] text-white">
			<div class="max-w-7xl mx-auto px-6 md:px-12 py-24 md:py-28">
				<div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
					<!-- Left Content -->
					<div class="lg:col-span-6">
						<!-- Security First Pill Badge -->
						<div
							class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/[0.06] border border-white/10 text-[11px] font-semibold uppercase tracking-wider text-[#22D36E] mb-6"
						>
							<svg
								class="w-3.5 h-3.5"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2.2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
								<path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
							</svg>
							<span>SECURITY FIRST</span>
						</div>

						<h2
							class="text-3xl sm:text-4xl md:text-[40px] font-bold tracking-tight leading-[1.15] text-white mb-5"
						>
							Your money deserves more than a password.
						</h2>

						<p class="text-sm md:text-[15px] leading-relaxed text-neutral-300/90 max-w-md">
							From bank-level encryption to independent asset custody, every layer of StockSafe is
							engineered to protect what you've built.
						</p>
					</div>

					<!-- Right 2x2 Security Feature Grid -->
					<div class="lg:col-span-6">
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
							<!-- Badge 1 -->
							<div
								class="flex items-center gap-3.5 bg-[#142F21] border border-white/[0.08] rounded-xl px-5 py-4"
							>
								<span
									class="w-6 h-6 rounded-full bg-[#12A150] text-white flex items-center justify-center shrink-0"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<polyline points="20 6 9 17 4 12"></polyline>
									</svg>
								</span>
								<span class="text-sm font-medium text-neutral-100">SIPC protection up to $500K</span
								>
							</div>

							<!-- Badge 2 -->
							<div
								class="flex items-center gap-3.5 bg-[#142F21] border border-white/[0.08] rounded-xl px-5 py-4"
							>
								<span
									class="w-6 h-6 rounded-full bg-[#12A150] text-white flex items-center justify-center shrink-0"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<polyline points="20 6 9 17 4 12"></polyline>
									</svg>
								</span>
								<span class="text-sm font-medium text-neutral-100">Independent asset custody</span>
							</div>

							<!-- Badge 3 -->
							<div
								class="flex items-center gap-3.5 bg-[#142F21] border border-white/[0.08] rounded-xl px-5 py-4"
							>
								<span
									class="w-6 h-6 rounded-full bg-[#12A150] text-white flex items-center justify-center shrink-0"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<polyline points="20 6 9 17 4 12"></polyline>
									</svg>
								</span>
								<span class="text-sm font-medium text-neutral-100">24/7 fraud monitoring</span>
							</div>

							<!-- Badge 4 -->
							<div
								class="flex items-center gap-3.5 bg-[#142F21] border border-white/[0.08] rounded-xl px-5 py-4"
							>
								<span
									class="w-6 h-6 rounded-full bg-[#12A150] text-white flex items-center justify-center shrink-0"
								>
									<svg
										class="w-3.5 h-3.5"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<polyline points="20 6 9 17 4 12"></polyline>
									</svg>
								</span>
								<span class="text-sm font-medium text-neutral-100">Multi-factor authentication</span
								>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Bottom Copyright & Legal Bar -->
			<div class="border-t border-white/10">
				<div
					class="max-w-7xl mx-auto px-6 md:px-12 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-neutral-400"
				>
					<div class="flex items-center gap-2.5">
						<span
							class="w-5 h-5 rounded-full bg-[#12A150] flex items-center justify-center text-white"
						>
							<svg
								class="w-3 h-3"
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
						<span class="font-semibold text-white text-sm">StockSafe</span>
						<span class="text-neutral-500 ml-2"
							>&copy; 2026 StockSafe Inc. All rights reserved.</span
						>
					</div>

					<div class="flex items-center gap-6">
						<a href="#why-stocksafe" class="hover:text-white transition-colors">Why StockSafe</a>
						<a href="#security" class="hover:text-white transition-colors">Security</a>
						<a href="/privacy" class="hover:text-white transition-colors">Privacy</a>
						<a href="/terms" class="hover:text-white transition-colors">Terms</a>
					</div>
				</div>
			</div>
		</footer>
	</body>
</html>
