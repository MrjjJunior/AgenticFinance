<div class="app">
	<aside class="sidebar">
		<div class="logo">
			<div class="logo-icon">S</div>
			<h2>Stock<span>Safe</span></h2>
		</div>

		<nav>
			<a class="active">▦ Overview</a>
			<a>▤ Catalogue</a>
			<a>⚙ Settings</a>
		</nav>

		<div class="profile">
			<div class="avatar">AM</div>
			<div>
				<strong>Ada Mensah</strong>
				<small>ada@example.com</small>
			</div>
		</div>
		<a class="logout">↪ Log out</a>
	</aside>

	<main>
		<header>
			<div>
				<small class="green mono">STOCKSAFE ACCOUNT</small>
				<h3>Overview</h3>
			</div>
			<div class="avatar">AM</div>
		</header>

		<div class="dashboard">
			<section class="welcome">
				<div>
					<small class="green mono">MONDAY, 26 MAY</small>
					<h1>Good morning, Ada.</h1>
					<p>Here's how your money is doing today.</p>
				</div>
				<button>Explore stocks ↗</button>
			</section>

			<section class="stats">
				<article class="portfolio">
					<small>Total portfolio value <span>•••</span></small>
					<h1>$48,290.18</h1>
					<p class="green">↑ $4,218.20 (9.57%)</p>
					<small>all time return</small>
					<div class="chart"></div>
				</article>

				<article class="protection">
					<div class="status-icon">✓</div>
					<small>Protection status</small>
					<h3>All systems active</h3>
					<p>Your portfolio is within your risk limits.</p>
					<span class="protected">PROTECTED</span>
				</article>

				<article class="goal">
					<small>Monthly goal</small>
					<div class="progress"><span>74%</span></div>
					<h3>$740 <small>/ $1,000</small></h3>
					<p>Only $260 to go</p>
				</article>
			</section>

			<section class="content">
				<article class="card">
					<div class="card-heading">
						<div>
							<small class="green mono">YOUR PORTFOLIO</small>
							<h2>Top holdings</h2>
						</div>
						<a>View all →</a>
					</div>

					<div class="holding">
						<div class="stock-icon apple">A</div>
						<div class="stock-name"><strong>AAPL</strong><small>Apple Inc.</small></div>
						<div class="bar"><span style="width:100%"></span></div>
						<div class="amount"><strong>$12,904</strong><small>+1.84%</small></div>
					</div>

					<div class="holding">
						<div class="stock-icon microsoft">M</div>
						<div class="stock-name"><strong>MSFT</strong><small>Microsoft</small></div>
						<div class="bar"><span style="width:83%"></span></div>
						<div class="amount"><strong>$9,780</strong><small>+0.92%</small></div>
					</div>

					<div class="holding">
						<div class="stock-icon nvidia">N</div>
						<div class="stock-name"><strong>NVDA</strong><small>NVIDIA</small></div>
						<div class="bar"><span style="width:66%"></span></div>
						<div class="amount"><strong>$7,562</strong><small>+3.21%</small></div>
					</div>

					<div class="holding">
						<div class="stock-icon jpm">J</div>
						<div class="stock-name"><strong>JPM</strong><small>JPMorgan Chase</small></div>
						<div class="bar"><span style="width:50%"></span></div>
						<div class="amount"><strong>$5,421</strong><small class="negative">-0.38%</small></div>
					</div>
				</article>

				<article class="card">
					<div class="card-heading">
						<div>
							<small class="green mono">RECENT</small>
							<h2>Activity</h2>
						</div>
						<a>See history</a>
					</div>

					<div class="activity">
						<span class="activity-icon">↑</span>
						<div><strong>Bought · AAPL</strong><small>2 shares · May 24</small></div>
						<strong>-$454.32</strong>
					</div>

					<div class="activity">
						<span class="activity-icon blue">↓</span>
						<div><strong>Dividend · MSFT</strong><small>Quarterly · May 23</small></div>
						<strong class="green">+$18.75</strong>
					</div>

					<div class="activity">
						<span class="activity-icon">↑</span>
						<div><strong>Deposit · Bank transfer</strong><small>Completed · May 22</small></div>
						<strong class="green">+$500.00</strong>
					</div>
				</article>
			</section>
		</div>
	</main>
</div>

<style>
	* {
		box-sizing: border-box;
		margin: 0;
	}

	body {
		font-family: Manrope, sans-serif;
		background: #f7faf7;
		color: #10231a;
	}

	.app {
		display: flex;
		min-height: 100vh;
	}

	.sidebar {
		width: 240px;
		background: #102f20;
		color: white;
		padding: 28px 20px;
		display: flex;
		flex-direction: column;
		flex-shrink: 0;
	}

	.logo,
	.profile,
	.holding,
	.activity,
	header,
	.welcome,
	.card-heading {
		display: flex;
		align-items: center;
	}

	.logo {
		gap: 10px;
	}
	.logo h2 {
		font-size: 18px;
	}
	.logo h2 span {
		color: #16a34a;
	}

	.logo-icon {
		background: #16a34a;
		border-radius: 50%;
		padding: 7px 11px;
		font-weight: bold;
	}

	nav {
		display: flex;
		flex-direction: column;
		gap: 7px;
		margin-top: 55px;
	}

	nav a,
	.logout {
		padding: 13px 14px;
		color: #a9beb2;
		font-size: 12px;
		font-weight: 700;
		border-radius: 12px;
		text-decoration: none;
	}

	nav .active {
		background: #214633;
		color: #70dd96;
	}

	.profile {
		gap: 10px;
		margin-top: auto;
		padding-top: 18px;
		border-top: 1px solid #ffffff20;
	}

	.avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: #d9f2e2;
		color: #102f20;
		display: grid;
		place-items: center;
		font-size: 10px;
		font-weight: 800;
		flex-shrink: 0;
	}

	.profile strong,
	.profile small,
	.stock-name small,
	.amount small,
	.activity small {
		display: block;
	}

	.profile strong {
		font-size: 11px;
	}
	.profile small {
		color: #8da69a;
		font-size: 8px;
	}

	.logout {
		margin-top: 12px;
	}

	main {
		flex: 1;
		min-width: 0;
	}

	header {
		height: 82px;
		padding: 0 35px;
		justify-content: space-between;
		border-bottom: 1px solid #dfe8e3;
		background: #f7faf7;
	}

	header h3 {
		font-size: 17px;
	}

	.dashboard {
		max-width: 1450px;
		margin: auto;
		padding: 38px;
	}

	.green {
		color: #168844;
	}
	.mono {
		font-family: 'DM Mono', monospace;
		letter-spacing: 1.2px;
		font-size: 9px;
	}

	.welcome {
		justify-content: space-between;
		gap: 20px;
	}

	.welcome h1 {
		font-size: 38px;
		font-weight: 800;
		margin: 7px 0;
	}

	p {
		color: #64786e;
		font-size: 12px;
	}

	button {
		background: #16a34a;
		color: white;
		border: 0;
		border-radius: 30px;
		padding: 14px 22px;
		font-weight: 700;
		cursor: pointer;
	}

	.stats {
		display: grid;
		grid-template-columns: 1.5fr 1fr 1fr;
		gap: 18px;
		margin-top: 28px;
	}

	article {
		padding: 22px;
		background: white;
		border: 1px solid #dfe8e3;
		border-radius: 20px;
		min-width: 0;
	}

	.portfolio {
		background: #102f20;
		color: white;
	}

	.portfolio h1 {
		font-size: 32px;
		margin: 10px 0;
	}

	.portfolio small {
		color: #a9beb2;
	}
	.portfolio p {
		display: inline-block;
		margin-right: 10px;
	}

	.chart {
		height: 40px;
		margin-top: 18px;
		border-bottom: 2px solid #45d279;
	}

	.protection {
		position: relative;
	}

	.status-icon {
		background: #e9f6ed;
		color: #16a34a;
		padding: 10px;
		border-radius: 12px;
		margin-bottom: 12px;
		width: fit-content;
	}

	.protection h3,
	.goal h3 {
		margin: 7px 0;
		font-size: 15px;
	}

	.protected {
		display: inline-block;
		color: #16a34a;
		background: #e9f6ed;
		padding: 5px 8px;
		border-radius: 20px;
		font-size: 8px;
		margin-top: 12px;
	}

	.progress {
		width: 62px;
		height: 62px;
		border: 6px solid #16a34a;
		border-radius: 50%;
		display: grid;
		place-items: center;
		margin: 12px 0;
		font-size: 10px;
		font-weight: 800;
	}

	.goal h3 small {
		font-size: 12px;
	}

	.content {
		display: grid;
		grid-template-columns: 1.2fr 1fr;
		gap: 18px;
		margin-top: 18px;
	}

	.card-heading {
		justify-content: space-between;
		margin-bottom: 18px;
	}

	.card-heading h2 {
		font-size: 20px;
		margin-top: 4px;
	}

	.card-heading a {
		color: #16a34a;
		font-size: 10px;
		font-weight: 700;
		cursor: pointer;
	}

	.holding {
		gap: 12px;
		padding: 13px 0;
		border-top: 1px solid #edf2ee;
	}

	.stock-icon {
		width: 36px;
		height: 36px;
		border-radius: 11px;
		display: grid;
		place-items: center;
		font-weight: 800;
		flex-shrink: 0;
	}

	.apple {
		background: #e8efff;
		color: #3456a1;
	}
	.microsoft {
		background: #fff0df;
		color: #bd6516;
	}
	.nvidia {
		background: #eee8ff;
		color: #704eb5;
	}
	.jpm {
		background: #e3f5ee;
		color: #157d50;
	}

	.stock-name {
		min-width: 110px;
	}
	.stock-name strong,
	.amount strong,
	.activity strong {
		font-size: 10px;
	}

	.stock-name small,
	.amount small,
	.activity small {
		font-size: 9px;
		color: #64786e;
		margin-top: 3px;
	}

	.bar {
		flex: 1;
		height: 4px;
		background: #eaf0ec;
		border-radius: 5px;
		min-width: 20px;
	}

	.bar span {
		display: block;
		height: 100%;
		background: #4ec679;
		border-radius: 5px;
	}

	.amount {
		text-align: right;
		min-width: 65px;
	}

	.amount small {
		color: #168844;
	}
	.amount .negative {
		color: #d05c52;
	}

	.activity {
		gap: 12px;
		padding: 16px 0;
		border-top: 1px solid #edf2ee;
	}

	.activity > div {
		flex: 1;
	}

	.activity-icon {
		width: 32px;
		height: 32px;
		background: #e6f7ec;
		color: #16a34a;
		border-radius: 50%;
		display: grid;
		place-items: center;
	}

	.activity-icon.blue {
		background: #e7efff;
		color: #476eb3;
	}

	.negative {
		color: #d05c52;
	}

	@media (max-width: 1000px) {
		.stats {
			grid-template-columns: 1fr 1fr;
		}
		.portfolio {
			grid-column: span 2;
		}
		.content {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 650px) {
		.sidebar {
			width: 65px;
			padding: 20px 10px;
		}
		.logo h2,
		nav a:not(.active),
		.profile > div:not(.avatar),
		.logout {
			display: none;
		}
		nav a {
			font-size: 0;
			padding: 13px;
		}
		.dashboard {
			padding: 20px 12px;
		}
		header {
			padding: 0 15px;
		}
		.welcome {
			align-items: flex-start;
			flex-direction: column;
		}
		.welcome h1 {
			font-size: 27px;
		}
		.stats {
			grid-template-columns: 1fr;
		}
		.portfolio {
			grid-column: auto;
		}
		.holding {
			gap: 7px;
		}
		.stock-name {
			min-width: 75px;
		}
	}
</style>
