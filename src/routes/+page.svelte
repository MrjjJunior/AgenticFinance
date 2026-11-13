<!DOCTYPE html>
<html lang="en">
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
		class="bg-white text-neutral-900 antialiased selection:bg-emerald-100 selection:text-emerald-900"
	>
		<!-- Main Hero Section -->
		<section
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
				<!-- Original Logo -->
				<a href="/" class="flex items-center gap-2 group">
					<span
						class="w-6 h-6 rounded-full bg-[#12A150] flex items-center justify-center text-white shadow-xs group-hover:scale-105 transition-transform"
					>
						<!-- Minimalist Shield Outline -->
						<svg
							class="w-3.5 h-3.5"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2.2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
						</svg>
					</span>
					<span class="font-semibold text-[15px] tracking-tight text-neutral-900">StockSafe</span>
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
			<footer class="relative z-10 max-w-7xl w-full mx-auto px-6 md:px-12 pb-16">
				<p class="max-w-sm text-sm md:text-[15px] leading-relaxed text-neutral-600">
					Smart investing meets serious protection. Build a portfolio that performs—with guardrails
					that help you sleep at night.
				</p>
			</footer>
		</section>
	</body>
</html>
