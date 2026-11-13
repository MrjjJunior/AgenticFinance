<script>
	const holdings = [
		{
			symbol: 'AAPL',
			name: 'Apple Inc.',
			initial: 'A',
			value: '$12,904',
			change: '+1.84%',
			color: 'blue',
			width: '100%'
		},
		{
			symbol: 'MSFT',
			name: 'Microsoft',
			initial: 'M',
			value: '$9,780',
			change: '+0.92%',
			color: 'orange',
			width: '76%'
		},
		{
			symbol: 'NVDA',
			name: 'NVIDIA',
			initial: 'N',
			value: '$7,562',
			change: '+3.21%',
			color: 'purple',
			width: '55%'
		},
		{
			symbol: 'JPM',
			name: 'JPMorgan Chase',
			initial: 'J',
			value: '$5,421',
			change: '-0.38%',
			color: 'mint',
			width: '40%'
		}
	];

	const activities = [
		{
			icon: '↑',
			title: 'Bought · AAPL',
			detail: '2 shares · May 24',
			amount: '-$454.32',
			type: 'debit'
		},
		{
			icon: '↓',
			title: 'Dividend · MSFT',
			detail: 'Quarterly · May 23',
			amount: '+$18.75',
			type: 'credit blue'
		},
		{
			icon: '↑',
			title: 'Deposit · Bank transfer',
			detail: 'Completed · May 22',
			amount: '+$500.00',
			type: 'credit'
		}
	];
</script>

<svelte:head>
	<title>StockSafe | Dashboard</title>
	<meta name="viewport" content="width=device-width, initial-scale=1" />
</svelte:head>

<div class="app-shell">
	<aside class="sidebar">
		<a class="brand" href="/" aria-label="StockSafe home">
			<span class="brand-mark">⌂</span>
			<span>Stock<strong>Safe</strong></span>
		</a>

		<nav class="navigation" aria-label="Main navigation">
			<a class="nav-link active" href="/dashboard"><span>▦</span> Overview</a>
			<a class="nav-link" href="/catalogue"><span>▤</span> Catalogue</a>
			<a class="nav-link" href="/settings"><span>⚙</span> Settings</a>
		</nav>

		<div class="profile">
			<div class="avatar">AM</div>
			<div class="profile-info">
				<strong>Ada Mensah</strong>
				<small>ada@example.com</small>
			</div>
			<a class="logout" href="/login" aria-label="Log out">↪</a>
		</div>
	</aside>

	<main class="main">
		<header class="topbar">
			<div>
				<span class="eyebrow">STOCKSAFE ACCOUNT</span>
				<h1>Overview</h1>
			</div>
			<div class="top-actions">
				<button class="notification" aria-label="Notifications">♧</button>
				<div class="avatar">AM</div>
			</div>
		</header>

		<div class="dashboard">
			<section class="welcome">
				<div>
					<p class="eyebrow green">MONDAY, 26 MAY</p>
					<h2>Good morning, Ada.</h2>
					<p class="muted">Here’s how your money is doing today.</p>
				</div>
				<a class="primary-button" href="/catalogue">Explore stocks <span>↗</span></a>
			</section>

			<section class="summary-grid" aria-label="Account summary">
				<article class="card portfolio-card">
					<div class="card-label">
						<span>Total portfolio value</span>
						<button class="more" aria-label="More portfolio options">•••</button>
					</div>
					<p class="portfolio-value">$48,290.18</p>
					<div class="return-line">
						<strong>↑ $4,218.20 (9.57%)</strong><span>all time return</span>
					</div>
					<div class="sparkline" aria-hidden="true">
						<svg viewBox="0 0 360 48" preserveAspectRatio="none">
							<path
								d="M0 37 L25 32 L48 35 L72 24 L96 29 L120 19 L144 26 L168 13 L192 20 L216 10 L240 17 L264 8 L288 14 L312 5 L336 10 L360 2"
							/>
						</svg>
					</div>
				</article>

				<article class="card protection-card">
					<div class="protection-icon">✓</div>
					<div>
						<p class="card-label">Protection status</p>
						<h3>All systems active</h3>
						<p class="muted small-text">Your portfolio is within your risk limits.</p>
					</div>
					<span class="status">PROTECTED</span>
				</article>

				<article class="card goal-card">
					<p class="card-label">Monthly goal</p>
					<div class="goal-content">
						<div class="progress-ring"><span>74%</span></div>
						<div>
							<h3>$740 <small>/ $1,000</small></h3>
							<p class="muted small-text">Only $260 to go</p>
						</div>
					</div>
				</article>
			</section>

			<section class="content-grid">
				<article class="card content-card">
					<div class="section-heading">
						<div>
							<p class="eyebrow green">YOUR PORTFOLIO</p>
							<h2>Top holdings</h2>
						</div>
						<a href="/portfolio" class="text-link">View all <span>→</span></a>
					</div>

					<div class="holding-list">
						{#each holdings as holding}
							<div class="holding">
								<div class="holding-icon {holding.color}">{holding.initial}</div>
								<div class="holding-name">
									<strong>{holding.symbol}</strong>
									<small>{holding.name}</small>
								</div>
								<div class="holding-bar"><span style={`width: ${holding.width}`}></span></div>
								<div class="holding-value">
									<strong>{holding.value}</strong>
									<small class:negative={holding.change.startsWith('-')}>{holding.change}</small>
								</div>
							</div>
						{/each}
					</div>
				</article>

				<article class="card content-card">
					<div class="section-heading">
						<div>
							<p class="eyebrow green">RECENT</p>
							<h2>Activity</h2>
						</div>
						<a href="/activity" class="text-link">See history</a>
					</div>

					<div class="activity-list">
						{#each activities as activity}
							<div class="activity">
								<div class="activity-icon {activity.type}">{activity.icon}</div>
								<div class="activity-description">
									<strong>{activity.title}</strong>
									<small>{activity.detail}</small>
								</div>
								<strong class="activity-amount">{activity.amount}</strong>
							</div>
						{/each}
					</div>
				</article>
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
		background: #f2f7f3;
		color: #10231a;
		font-family: Manrope, Arial, sans-serif;
	}
	:global(a) {
		color: inherit;
		text-decoration: none;
	}
	:global(button) {
		font: inherit;
	}

	.app-shell {
		min-height: 100vh;
	}
	.sidebar {
		position: fixed;
		inset: 0 auto 0 0;
		z-index: 2;
		width: 240px;
		display: flex;
		flex-direction: column;
		padding: 28px 20px;
		color: white;
		background: #102f20;
	}
	.brand {
		display: flex;
		align-items: center;
		gap: 10px;
		font-size: 19px;
		font-weight: 800;
	}
	.brand strong {
		color: #16a34a;
	}
	.brand-mark {
		display: grid;
		place-items: center;
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: #16a34a;
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
		font-size: 12px;
		font-weight: 700;
	}
	.nav-link span {
		width: 20px;
		text-align: center;
		font-size: 17px;
	}
	.nav-link.active {
		color: #70dd96;
		background: #ffffff1f;
	}
	.profile {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-top: auto;
		padding-top: 18px;
		border-top: 1px solid #ffffff1a;
	}
	.avatar {
		display: grid;
		flex: 0 0 36px;
		place-items: center;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		color: #102f20;
		background: #d9f2e2;
		font-size: 10px;
		font-weight: 800;
	}
	.profile-info {
		display: grid;
		gap: 3px;
		min-width: 0;
	}
	.profile-info strong {
		font-size: 11px;
		font-weight: 600;
	}
	.profile-info small {
		color: #8da69a;
		font-size: 8px;
	}
	.logout {
		margin-left: auto;
		color: #a9beb2;
		font-size: 20px;
	}

	.main {
		min-height: 100vh;
		margin-left: 240px;
	}
	.topbar {
		position: sticky;
		top: 0;
		z-index: 1;
		display: flex;
		align-items: center;
		justify-content: space-between;
		min-height: 82px;
		padding: 14px 35px;
		border-bottom: 1px solid #dfe8e3;
		background: #f7faf7ed;
		backdrop-filter: blur(12px);
	}
	.eyebrow {
		margin: 0;
		color: #168844;
		font-family: 'DM Mono', monospace;
		font-size: 8px;
		font-weight: 500;
		letter-spacing: 1.5px;
	}
	.topbar h1 {
		margin: 5px 0 0;
		font-size: 17px;
		font-weight: 800;
	}
	.top-actions {
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
		cursor: pointer;
	}
	.dashboard {
		width: 100%;
		max-width: 1450px;
		margin: auto;
		padding: 38px;
	}
	.welcome {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		gap: 20px;
	}
	.welcome h2 {
		margin: 7px 0 2px;
		font-size: clamp(26px, 3vw, 38px);
		line-height: 1.35;
		font-weight: 800;
	}
	.muted {
		margin: 0;
		color: #64786e;
		font-size: 13px;
	}
	.primary-button {
		display: inline-flex;
		align-items: center;
		gap: 12px;
		padding: 13px 21px;
		border-radius: 99px;
		color: white;
		background: #16a34a;
		font-size: 13px;
		font-weight: 700;
		white-space: nowrap;
	}
	.summary-grid {
		display: grid;
		grid-template-columns: 1.35fr 1fr 0.9fr;
		gap: 18px;
		margin-top: 28px;
	}
	.card {
		min-width: 0;
		padding: 22px;
		border: 1px solid #dfe8e3;
		border-radius: 20px;
		background: white;
	}
	.portfolio-card {
		overflow: hidden;
		color: white;
		background: #102f20;
	}
	.card-label {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin: 0;
		color: #64786e;
		font-size: 10px;
	}
	.portfolio-card .card-label {
		color: #a9beb2;
		font-size: 11px;
	}
	.more {
		padding: 0;
		border: 0;
		color: #a9beb2;
		background: none;
		letter-spacing: 2px;
	}
	.portfolio-value {
		margin: 10px 0 2px;
		font-size: clamp(25px, 2.5vw, 32px);
		font-weight: 800;
	}
	.return-line {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 12px;
	}
	.return-line strong {
		color: #45d279;
		font-size: 13px;
		font-weight: 600;
	}
	.return-line span {
		color: #8fa89a;
		font-size: 9px;
	}
	.sparkline {
		height: 48px;
		margin: 15px -2px -5px;
	}
	.sparkline svg {
		width: 100%;
		height: 100%;
		overflow: visible;
	}
	.sparkline path {
		fill: none;
		stroke: #45d279;
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}
	.protection-card {
		position: relative;
		display: flex;
		align-items: flex-start;
		gap: 14px;
	}
	.protection-icon {
		display: grid;
		flex: 0 0 42px;
		place-items: center;
		width: 42px;
		height: 42px;
		border-radius: 13px;
		color: #16a34a;
		background: #e9f6ed;
		font-size: 20px;
		font-weight: 800;
	}
	.protection-card h3 {
		margin: 7px 0 4px;
		font-size: 15px;
	}
	.small-text {
		font-size: 10px;
		line-height: 1.5;
	}
	.status {
		position: absolute;
		right: 18px;
		bottom: 17px;
		padding: 5px 8px;
		border-radius: 99px;
		color: #16a34a;
		background: #e9f6ed;
		font-size: 7px;
		font-weight: 700;
		letter-spacing: 0.3px;
	}
	.goal-content {
		display: flex;
		align-items: center;
		gap: 16px;
		margin-top: 15px;
	}
	.progress-ring {
		display: grid;
		flex: 0 0 62px;
		place-items: center;
		width: 62px;
		height: 62px;
		border: 7px solid #e9f6ed;
		border-top-color: #16a34a;
		border-right-color: #16a34a;
		border-radius: 50%;
	}
	.progress-ring span {
		font-size: 10px;
		font-weight: 800;
	}
	.goal-content h3 {
		margin: 0 0 5px;
		font-size: 15px;
		white-space: nowrap;
	}
	.goal-content h3 small {
		font-size: 11px;
	}
	.content-grid {
		display: grid;
		grid-template-columns: 1.15fr 1fr;
		gap: 18px;
		margin-top: 18px;
	}
	.section-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}
	.section-heading h2 {
		margin: 5px 0 0;
		font-size: 20px;
		font-weight: 800;
	}
	.text-link {
		color: #16a34a;
		font-size: 10px;
		font-weight: 700;
		white-space: nowrap;
	}
	.holding-list,
	.activity-list {
		margin-top: 18px;
	}
	.holding {
		display: grid;
		grid-template-columns: 36px minmax(95px, 1fr) minmax(50px, 1fr) 78px;
		align-items: center;
		gap: 12px;
		padding: 13px 0;
		border-top: 1px solid #edf2ee;
	}
	.holding-icon {
		display: grid;
		place-items: center;
		width: 36px;
		height: 36px;
		border-radius: 11px;
		background: #e8efff;
		font-size: 12px;
		font-weight: 800;
	}
	.holding-icon.orange {
		color: #bd6516;
		background: #fff0df;
	}
	.holding-icon.purple {
		color: #704eb5;
		background: #eee8ff;
	}
	.holding-icon.mint {
		color: #157d50;
		background: #e3f5ee;
	}
	.holding-name,
	.holding-value,
	.activity-description {
		display: grid;
		gap: 3px;
		min-width: 0;
	}
	.holding-name strong,
	.holding-value strong,
	.activity strong {
		color: #10231a;
		font-size: 11px;
		font-weight: 600;
	}
	.holding-name small,
	.holding-value small,
	.activity small {
		color: #64786e;
		font-size: 9px;
	}
	.holding-bar {
		height: 4px;
		overflow: hidden;
		border-radius: 5px;
		background: #eaf0ec;
	}
	.holding-bar span {
		display: block;
		height: 100%;
		border-radius: inherit;
		background: #4ec679;
	}
	.holding-value {
		text-align: right;
	}
	.holding-value small {
		color: #168844;
	}
	.holding-value small.negative {
		color: #d05c52;
	}
	.activity {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 16px 0;
		border-top: 1px solid #edf2ee;
	}
	.activity-icon {
		display: grid;
		flex: 0 0 32px;
		place-items: center;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		color: #16a34a;
		background: #e6f7ec;
		font-size: 16px;
	}
	.activity-icon.blue {
		color: #476eb3;
		background: #e7efff;
	}
	.activity-description {
		flex: 1;
	}
	.activity-amount {
		white-space: nowrap;
	}

	@media (max-width: 1100px) {
		.dashboard {
			padding: 28px;
		}
		.summary-grid {
			grid-template-columns: 1fr 1fr;
		}
		.portfolio-card {
			grid-column: 1 / -1;
		}
		.content-grid {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 700px) {
		.sidebar {
			position: static;
			width: 100%;
			min-height: auto;
			padding: 14px 18px;
		}
		.brand {
			font-size: 17px;
		}
		.navigation {
			display: flex;
			gap: 5px;
			margin-top: 14px;
		}
		.nav-link {
			flex: 1;
			justify-content: center;
			padding: 10px 7px;
			font-size: 11px;
		}
		.nav-link span {
			width: auto;
		}
		.profile {
			display: none;
		}
		.main {
			margin-left: 0;
		}
		.topbar {
			min-height: 68px;
			padding: 12px 18px;
		}
		.top-actions .avatar {
			display: none;
		}
		.dashboard {
			padding: 24px 18px;
		}
		.welcome {
			align-items: flex-start;
			flex-direction: column;
		}
		.welcome h2 {
			font-size: 29px;
		}
		.summary-grid {
			grid-template-columns: 1fr;
			gap: 12px;
			margin-top: 22px;
		}
		.portfolio-card {
			grid-column: auto;
		}
		.content-grid {
			gap: 12px;
			margin-top: 12px;
		}
		.card {
			padding: 18px;
		}
	}
	@media (max-width: 420px) {
		.holding {
			grid-template-columns: 34px minmax(75px, 1fr) 65px;
			gap: 9px;
		}
		.holding-bar {
			display: none;
		}
		.holding-value strong {
			font-size: 10px;
		}
		.section-heading h2 {
			font-size: 18px;
		}
	}
</style>
