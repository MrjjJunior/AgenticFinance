<script>
	let search = '';
	let selectedSector = 'All';
	let sortBy = 'Featured';
	/**
	 * @type {any[]}
	 */
	let watchlist = [];

	const sectors = ['All', 'Technology', 'Finance', 'Automotive', 'Consumer'];

	const companies = [
		{
			symbol: 'AAPL',
			name: 'Apple Inc.',
			sector: 'Technology',
			risk: 'Low risk',
			price: 227.16,
			change: 1.84,
			initial: 'A',
			color: 'blue'
		},
		{
			symbol: 'MSFT',
			name: 'Microsoft',
			sector: 'Technology',
			risk: 'Low risk',
			price: 418.79,
			change: 0.92,
			initial: 'M',
			color: 'orange'
		},
		{
			symbol: 'NVDA',
			name: 'NVIDIA',
			sector: 'Technology',
			risk: 'Medium risk',
			price: 138.85,
			change: 3.21,
			initial: 'N',
			color: 'purple'
		},
		{
			symbol: 'JPM',
			name: 'JPMorgan Chase',
			sector: 'Finance',
			risk: 'Low risk',
			price: 243.13,
			change: -0.38,
			initial: 'J',
			color: 'teal'
		},
		{
			symbol: 'TSLA',
			name: 'Tesla',
			sector: 'Automotive',
			risk: 'High risk',
			price: 352.56,
			change: -1.16,
			initial: 'T',
			color: 'blue'
		},
		{
			symbol: 'COST',
			name: 'Costco',
			sector: 'Consumer',
			risk: 'Low risk',
			price: 932.38,
			change: 1.07,
			initial: 'C',
			color: 'blue'
		}
	];

	$: filteredCompanies = companies
		.filter((company) => selectedSector === 'All' || company.sector === selectedSector)
		.filter((company) =>
			`${company.name} ${company.symbol}`.toLowerCase().includes(search.toLowerCase())
		);

	$: displayedCompanies = [...filteredCompanies].sort((a, b) => {
		if (sortBy === 'Price: high to low') return b.price - a.price;
		if (sortBy === 'Price: low to high') return a.price - b.price;
		if (sortBy === 'Daily change') return b.change - a.change;
		return companies.indexOf(a) - companies.indexOf(b);
	});

	/**
	 * @param {string} symbol
	 */
	function toggleWatchlist(symbol) {
		watchlist = watchlist.includes(symbol)
			? watchlist.filter((item) => item !== symbol)
			: [...watchlist, symbol];
	}
</script>

<svelte:head>
	<title>StockSafe | Catalogue</title>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
</svelte:head>

<div class="app-shell">
	<aside class="sidebar">
		<a class="brand" href="/dashboard" aria-label="StockSafe home">
			<span class="brand-mark">S</span>
			<span>Stock<strong>Safe</strong></span>
		</a>

		<nav class="navigation" aria-label="Main navigation">
			<a href="/dashboard" class="nav-link">
				<span class="nav-icon">▦</span> Overview
			</a>
			<a href="/catalogue" class="nav-link active">
				<span class="nav-icon">▤</span> Catalogue
			</a>
			<a href="/settings" class="nav-link">
				<span class="nav-icon">⚙</span> Settings
			</a>
		</nav>

		<div class="profile">
			<div class="profile-info">
				<span class="avatar">AM</span>
				<div>
					<strong>Ada Mensah</strong>
					<small>ada@example.com</small>
				</div>
			</div>
			<button class="logout" type="button"><span>↪</span> Log out</button>
		</div>
	</aside>

	<main class="main">
		<header class="topbar">
			<div>
				<span class="eyebrow">STOCKSAFE ACCOUNT</span>
				<h1>Catalogue</h1>
			</div>
			<div class="topbar-actions">
				<button class="notification" aria-label="Notifications" type="button">♧</button>
				<span class="avatar">AM</span>
			</div>
		</header>

		<div class="page-content">
			<section class="hero">
				<div class="hero-copy">
					<span class="eyebrow green">DISCOVER OPPORTUNITIES</span>
					<h2>Find your next investment.</h2>
					<p>Explore quality companies with the context you need to invest confidently.</p>
				</div>

				<label class="search-box">
					<span aria-hidden="true">⌕</span>
					<input bind:value={search} placeholder="Search by company or symbol" />
					{#if search}
						<button
							type="button"
							class="clear-search"
							aria-label="Clear search"
							onclick={() => (search = '')}>×</button
						>
					{/if}
				</label>
			</section>

			<section class="filter-row" aria-label="Filter companies by sector">
				<span class="filter-label">Filter by sector</span>
				<div class="filter-options">
					{#each sectors as sector}
						<button
							type="button"
							class:chosen={selectedSector === sector}
							class="filter-chip"
							onclick={() => (selectedSector = sector)}>{sector}</button
						>
					{/each}
				</div>
			</section>

			<section class="results-heading">
				<p>
					{displayedCompanies.length}
					{displayedCompanies.length === 1 ? 'company' : 'companies'} matching your selection
				</p>
				<label class="sort-control">
					<span class="sr-only">Sort companies</span>
					<select bind:value={sortBy}>
						<option>Featured</option>
						<option>Price: high to low</option>
						<option>Price: low to high</option>
						<option>Daily change</option>
					</select>
					<span aria-hidden="true">⌄</span>
				</label>
			</section>

			<section class="company-grid" aria-label="Company catalogue">
				{#each displayedCompanies as company}
					<article class="company-card">
						<div class="card-top">
							<span class="company-mark {company.color}">{company.initial}</span>
							<button
								class="watchlist"
								class:saved={watchlist.includes(company.symbol)}
								type="button"
								aria-label={watchlist.includes(company.symbol)
									? `Remove ${company.name} from watchlist`
									: `Add ${company.name} to watchlist`}
								aria-pressed={watchlist.includes(company.symbol)}
								onclick={() => toggleWatchlist(company.symbol)}
								>{watchlist.includes(company.symbol) ? '★' : '☆'}</button
							>
						</div>

						<div class="company-info">
							<span class="symbol">{company.symbol}</span>
							<h3>{company.name}</h3>
							<p>{company.sector} <span>·</span> {company.risk}</p>
						</div>

						<div class="price-row">
							<strong>${company.price.toFixed(2)}</strong>
							<span class:negative={company.change < 0} class="change">
								{company.change >= 0 ? '↑' : '↓'}
								{Math.abs(company.change).toFixed(2)}%
							</span>
						</div>

						<div class="mini-chart" class:down={company.change < 0}>
							<svg viewBox="0 0 280 42" preserveAspectRatio="none" aria-hidden="true">
								{#if company.change < 0}
									<polyline
										points="0,9 28,15 55,12 82,24 110,19 138,29 166,23 194,33 222,27 250,36 280,31"
									/>
								{:else}
									<polyline
										points="0,31 28,26 55,30 82,17 110,23 138,11 166,18 194,8 222,13 250,4 280,7"
									/>
								{/if}
							</svg>
						</div>

						<a class="details-link" href={`/company/${company.symbol}`}>
							View details <span aria-hidden="true">→</span>
						</a>
					</article>
				{:else}
					<div class="empty-state">
						<span>⌕</span>
						<h3>No companies found</h3>
						<p>Try another search term or choose a different sector.</p>
						<button
							type="button"
							onclick={() => {
								search = '';
								selectedSector = 'All';
							}}>Clear filters</button
						>
					</div>
				{/each}
			</section>
		</div>
	</main>
</div>

<style>
	:global(*) {
		box-sizing: border-box;
	}
	:global(body) {
		margin: 0;
		background: #f7faf7;
		color: #10231a;
		font-family: 'Manrope', Arial, sans-serif;
	}
	:global(button),
	:global(input),
	:global(select) {
		font: inherit;
	}
	.app-shell {
		min-height: 100vh;
	}
	.sidebar {
		width: 240px;
		padding: 28px 20px;
		background: #102f20;
		color: white;
		position: fixed;
		inset: 0 auto 0 0;
		display: flex;
		flex-direction: column;
		z-index: 5;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 10px;
		color: white;
		text-decoration: none;
		font-size: 18px;
		font-weight: 800;
	}
	.brand strong {
		color: #16a34a;
	}
	.brand-mark {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		background: #16a34a;
		color: white;
		font-size: 16px;
	}
	.navigation {
		display: grid;
		gap: 7px;
		margin-top: 55px;
	}
	.nav-link {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 13px 14px;
		border-radius: 12px;
		color: #a9beb2;
		text-decoration: none;
		font-size: 12px;
		font-weight: 700;
	}
	.nav-link.active {
		background: rgba(101, 220, 145, 0.12);
		color: #70dd96;
	}
	.nav-icon {
		width: 20px;
		text-align: center;
		font-size: 17px;
	}
	.profile {
		margin-top: auto;
		padding-top: 18px;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}
	.profile-info {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.avatar {
		flex: 0 0 36px;
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		border-radius: 50%;
		background: #d9f2e2;
		color: #102f20;
		font-size: 10px;
		font-weight: 800;
	}
	.profile-info strong,
	.profile-info small {
		display: block;
	}
	.profile-info strong {
		font-size: 11px;
		font-weight: 600;
	}
	.profile-info small {
		margin-top: 3px;
		color: #8da69a;
		font-size: 8px;
	}
	.logout {
		display: flex;
		align-items: center;
		gap: 12px;
		width: 100%;
		margin-top: 12px;
		padding: 13px 14px;
		border: 0;
		border-radius: 12px;
		background: transparent;
		color: #a9beb2;
		text-align: left;
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
	}
	.main {
		min-height: 100vh;
		margin-left: 240px;
	}
	.topbar {
		height: 82px;
		padding: 0 35px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		position: sticky;
		top: 0;
		z-index: 3;
		background: rgba(247, 250, 247, 0.94);
		border-bottom: 1px solid #dfe8e3;
		backdrop-filter: blur(12px);
	}
	.eyebrow {
		color: #168844;
		font-family: 'DM Mono', monospace;
		font-size: 8px;
		font-weight: 500;
		letter-spacing: 1.55px;
	}
	.topbar h1 {
		margin: 4px 0 0;
		font-size: 17px;
		line-height: 1.5;
		font-weight: 800;
	}
	.topbar-actions {
		display: flex;
		align-items: center;
		gap: 13px;
	}
	.notification {
		width: 38px;
		height: 38px;
		border: 1px solid #dfe8e3;
		border-radius: 50%;
		background: white;
		color: #587064;
		font-size: 19px;
		cursor: pointer;
	}
	.page-content {
		width: min(100%, 1450px);
		padding: 38px;
		margin: 0 auto;
	}
	.hero {
		min-height: 190px;
		padding: 30px 34px;
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 28px;
		border-radius: 24px;
		background:
			radial-gradient(ellipse 444% 81% at 80% 20%, rgba(41, 184, 98, 0.25), transparent 35%),
			#102f20;
	}
	.hero-copy {
		max-width: 490px;
	}
	.hero h2 {
		margin: 8px 0 5px;
		color: white;
		font-size: clamp(26px, 3vw, 38px);
		line-height: 1.3;
		font-weight: 800;
	}
	.hero p {
		margin: 0;
		color: #acc3b6;
		font-size: 13px;
		line-height: 1.6;
	}
	.search-box {
		width: min(100%, 376px);
		min-height: 48px;
		padding: 0 15px;
		display: flex;
		align-items: center;
		gap: 11px;
		border-radius: 14px;
		background: white;
		color: #73867b;
	}
	.search-box > span {
		font-size: 24px;
		line-height: 1;
	}
	.search-box input {
		width: 100%;
		min-width: 0;
		border: 0;
		outline: 0;
		color: #10231a;
		font-size: 12px;
	}
	.search-box input::placeholder {
		color: rgba(115, 134, 123, 0.75);
	}
	.clear-search {
		border: 0;
		background: transparent;
		color: #73867b;
		font-size: 20px;
		cursor: pointer;
	}
	.filter-row {
		min-height: 72px;
		padding-top: 25px;
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 12px;
	}
	.filter-label {
		margin-right: 2px;
		color: #64786e;
		font-size: 10px;
	}
	.filter-options {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.filter-chip {
		padding: 8px 14px;
		border: 1px solid #dfe8e3;
		border-radius: 99px;
		background: white;
		color: #587064;
		font-size: 10px;
		cursor: pointer;
		transition:
			background 0.15s,
			color 0.15s;
	}
	.filter-chip.chosen {
		border-color: #102f20;
		background: #102f20;
		color: white;
	}
	.results-heading {
		min-height: 58px;
		padding-top: 20px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 15px;
	}
	.results-heading p {
		margin: 0;
		color: #64786e;
		font-size: 11px;
	}
	.sort-control {
		min-width: 130px;
		height: 34px;
		padding: 0 12px;
		display: flex;
		align-items: center;
		gap: 8px;
		border: 1px solid #dfe8e3;
		border-radius: 9px;
		background: white;
		color: #587064;
	}
	.sort-control select {
		width: 100%;
		border: 0;
		outline: 0;
		appearance: none;
		background: transparent;
		color: inherit;
		font-size: 10px;
		cursor: pointer;
	}
	.company-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 16px;
		padding-top: 15px;
	}
	.company-card {
		min-width: 0;
		padding: 20px;
		border: 1px solid #dfe8e3;
		border-radius: 18px;
		background: white;
	}
	.card-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.company-mark {
		width: 36px;
		height: 36px;
		display: grid;
		place-items: center;
		border-radius: 11px;
		font-size: 12px;
		font-weight: 800;
	}
	.company-mark.blue {
		background: #e8efff;
		color: #3456a1;
	}
	.company-mark.orange {
		background: #fff0df;
		color: #bd6516;
	}
	.company-mark.purple {
		background: #eee8ff;
		color: #704eb5;
	}
	.company-mark.teal {
		background: #e3f5ee;
		color: #157d50;
	}
	.watchlist {
		width: 32px;
		height: 32px;
		border: 0;
		border-radius: 50%;
		background: transparent;
		color: #91a097;
		font-size: 23px;
		cursor: pointer;
	}
	.watchlist.saved {
		color: #168844;
	}
	.company-info {
		padding-top: 17px;
	}
	.symbol {
		color: #16a34a;
		font-family: 'DM Mono', monospace;
		font-size: 9px;
	}
	.company-info h3 {
		margin: 4px 0;
		color: #10231a;
		font-size: 16px;
		line-height: 1.5;
		font-weight: 800;
	}
	.company-info p {
		margin: 0;
		color: #64786e;
		font-size: 9px;
	}
	.company-info p span {
		padding: 0 3px;
	}
	.price-row {
		margin-top: 18px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 8px;
	}
	.price-row strong {
		color: #10231a;
		font-size: 20px;
	}
	.change {
		color: #168844;
		font-size: 10px;
		white-space: nowrap;
	}
	.change.negative {
		color: #d05c52;
	}
	.mini-chart {
		height: 42px;
		margin-top: 13px;
		overflow: hidden;
	}
	.mini-chart svg {
		width: 100%;
		height: 100%;
		overflow: visible;
	}
	.mini-chart polyline {
		fill: none;
		stroke: #16a34a;
		stroke-width: 2;
		vector-effect: non-scaling-stroke;
	}
	.mini-chart.down polyline {
		stroke: #d05c52;
	}
	.details-link {
		margin-top: 13px;
		padding-top: 14px;
		display: flex;
		justify-content: space-between;
		border-top: 1px solid #edf2ee;
		color: #375044;
		text-decoration: none;
		font-size: 10px;
		font-weight: 700;
	}
	.details-link span {
		font-size: 14px;
		line-height: 10px;
	}
	.empty-state {
		grid-column: 1 / -1;
		padding: 55px 20px;
		text-align: center;
		border: 1px dashed #cbd9d0;
		border-radius: 18px;
		color: #64786e;
	}
	.empty-state > span {
		font-size: 28px;
	}
	.empty-state h3 {
		margin: 8px 0;
		color: #10231a;
	}
	.empty-state p {
		font-size: 12px;
	}
	.empty-state button {
		padding: 9px 15px;
		border: 0;
		border-radius: 20px;
		background: #102f20;
		color: white;
		cursor: pointer;
		font-size: 11px;
	}
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	@media (max-width: 1100px) {
		.company-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
		.hero {
			align-items: flex-start;
			flex-direction: column;
		}
		.search-box {
			width: 100%;
		}
	}
	@media (max-width: 700px) {
		.sidebar {
			position: static;
			width: 100%;
			padding: 16px 20px;
		}
		.navigation {
			margin-top: 16px;
			display: flex;
			gap: 5px;
		}
		.nav-link {
			flex: 1;
			justify-content: center;
			padding: 10px 8px;
		}
		.nav-icon {
			display: none;
		}
		.profile {
			display: none;
		}
		.main {
			margin-left: 0;
		}
		.topbar {
			height: 70px;
			padding: 0 20px;
		}
		.page-content {
			padding: 22px 18px;
		}
		.hero {
			min-height: 0;
			padding: 25px 22px;
			border-radius: 18px;
		}
		.hero h2 {
			font-size: 28px;
		}
		.filter-row {
			align-items: flex-start;
			flex-direction: column;
		}
		.results-heading {
			align-items: flex-start;
		}
	}
	@media (max-width: 480px) {
		.company-grid {
			grid-template-columns: 1fr;
		}
		.topbar-actions {
			gap: 8px;
		}
		.filter-options {
			gap: 6px;
		}
		.filter-chip {
			padding: 8px 11px;
		}
		.results-heading {
			flex-direction: column;
			align-items: stretch;
		}
		.sort-control {
			width: 100%;
		}
	}
</style>
