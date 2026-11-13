<div class="appshell">
	<!-- Sidebar -->
	<aside class="sidebar">
		<div class="logo"><span>Stock</span><strong>Safe</strong></div>

		<nav class="side-nav">
			<a>▦ Overview</a>
			<a>▤ Catalogue</a>
			<a class="active">⚙ Settings</a>
		</nav>

		<div class="user">
			<div class="avatar">AM</div>
			<div>
				<strong>Ada Mensah</strong>
				<small>ada@example.com</small>
			</div>
		</div>
		<a class="logout">↪ Log out</a>
	</aside>

	<!-- Main content -->
	<main class="main">
		<header class="header">
			<div>
				<small>STOCKSAFE ACCOUNT</small>
				<h2>Settings</h2>
			</div>
			<div class="avatar">AM</div>
		</header>

		<div class="content">
			<section class="intro">
				<small class="eyebrow">YOUR PREFERENCES</small>
				<h1>Settings</h1>
				<p>Manage your profile, security, and the alerts you receive.</p>
			</section>

			<div class="layout">
				<!-- Settings navigation -->
				<nav class="settings-nav">
					<a class="selected">Profile</a>
					<a>Security</a>
					<a>Notifications</a>
					<a>Preferences</a>
				</nav>

				<div class="sections">
					<!-- Profile -->
					<section class="card">
						<div class="card-heading">
							<div>
								<h3>Profile details</h3>
								<p>Update how your name and contact information appear.</p>
							</div>
							<div class="avatar dark">AM</div>
						</div>

						<div class="fields">
							<label
								>Full name
								<input type="text" value="Ada Mensah" />
							</label>

							<label
								>Email address
								<input type="email" value="ada@example.com" />
							</label>

							<label
								>Phone number
								<input type="tel" value="+233 24 555 0198" />
							</label>

							<label
								>Country
								<select>
									<option>Ghana</option>
									<option>South Africa</option>
								</select>
							</label>
						</div>

						<button class="save">Save changes ✓</button>
					</section>

					<!-- Security -->
					<section class="card">
						<div class="card-heading">
							<div>
								<h3>Security</h3>
								<p>Keep your StockSafe account protected.</p>
							</div>
							<span class="secure">♧ Secure</span>
						</div>

						<div class="setting-row">
							<div>
								<strong>Two-factor authentication</strong>
								<p>Add an extra layer of protection when you sign in.</p>
							</div>
							<button class="outline">Configure</button>
						</div>

						<div class="setting-row">
							<div>
								<strong>Password</strong>
								<p>Last changed 42 days ago</p>
							</div>
							<button class="outline">Update</button>
						</div>
					</section>

					<!-- Notifications -->
					<section class="card">
						<div class="card-heading">
							<div>
								<h3>Notifications</h3>
								<p>Choose what StockSafe keeps you informed about.</p>
							</div>
						</div>

						<div class="setting-row">
							<div>
								<strong>Email notifications</strong>
								<p>Trade confirmations and account updates</p>
							</div>
							<input type="checkbox" class="toggle" checked />
						</div>

						<div class="setting-row">
							<div>
								<strong>Market alerts</strong>
								<p>Meaningful price and risk movements</p>
							</div>
							<input type="checkbox" class="toggle" checked />
						</div>

						<div class="setting-row">
							<div>
								<strong>Security alerts</strong>
								<p>New sign-ins and security changes</p>
							</div>
							<input type="checkbox" class="toggle" checked />
						</div>

						<div class="setting-row">
							<div>
								<strong>Weekly digest</strong>
								<p>A simple weekly portfolio summary</p>
							</div>
							<input type="checkbox" class="toggle" />
						</div>
					</section>
				</div>
			</div>
		</div>
	</main>
</div>

<style>
	* {
		box-sizing: border-box;
	}

	body {
		margin: 0;
		font-family: Manrope, Arial, sans-serif;
		color: #10231a;
		background: #f2f7f3;
	}

	.appshell {
		min-height: 100vh;
		display: flex;
	}

	/* Sidebar */
	.sidebar {
		width: 240px;
		min-height: 100vh;
		padding: 28px 20px;
		background: #102f20;
		color: white;
		display: flex;
		flex-direction: column;
	}

	.logo {
		font-size: 22px;
		font-weight: 800;
	}

	.logo strong {
		color: #16a34a;
	}

	.side-nav {
		display: flex;
		flex-direction: column;
		gap: 7px;
		margin-top: 55px;
	}

	.side-nav a,
	.settings-nav a {
		padding: 13px;
		border-radius: 10px;
		text-decoration: none;
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
	}

	.side-nav a {
		color: #a9beb2;
	}

	.side-nav .active {
		background: rgba(101, 220, 145, 0.12);
		color: #70dd96;
	}

	.user {
		display: flex;
		align-items: center;
		gap: 10px;
		margin-top: auto;
		padding-top: 20px;
		border-top: 1px solid #ffffff20;
	}

	.user strong,
	.user small {
		display: block;
	}

	.user strong {
		font-size: 11px;
		font-weight: 500;
	}

	.user small {
		margin-top: 4px;
		color: #8da69a;
		font-size: 9px;
	}

	.avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		background: #d9f2e2;
		color: #102f20;
		font-size: 10px;
		font-weight: 800;
		flex-shrink: 0;
	}

	.logout {
		padding: 15px;
		color: #a9beb2;
		font-size: 12px;
	}

	/* Main area */
	.main {
		flex: 1;
		min-width: 0;
	}

	.header {
		height: 82px;
		padding: 0 35px;
		background: rgba(247, 250, 247, 0.92);
		border-bottom: 1px solid #dfe8e3;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.header small,
	.eyebrow {
		color: #168844;
		font-family: 'DM Mono', monospace;
		font-size: 9px;
		letter-spacing: 1.5px;
	}

	.header h2 {
		margin: 3px 0 0;
		font-size: 17px;
	}

	.content {
		max-width: 1050px;
		padding: 38px;
	}

	.intro h1 {
		margin: 8px 0 4px;
		font-size: 38px;
		font-weight: 800;
	}

	p {
		color: #64786e;
		font-size: 11px;
		line-height: 1.6;
		margin: 5px 0 0;
	}

	.layout {
		display: grid;
		grid-template-columns: 150px minmax(0, 850px);
		gap: 25px;
		margin-top: 25px;
	}

	.settings-nav {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.settings-nav a {
		color: #64786e;
	}

	.settings-nav .selected {
		background: #dff1e5;
		color: #16a34a;
	}

	.sections {
		display: flex;
		flex-direction: column;
		gap: 17px;
	}

	/* Cards */
	.card {
		padding: 26px;
		background: white;
		border: 1px solid #dfe8e3;
		border-radius: 20px;
	}

	.card-heading {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-bottom: 18px;
		border-bottom: 1px solid #edf2ee;
	}

	.card-heading h3 {
		margin: 0;
		font-size: 18px;
		font-weight: 800;
	}

	.card-heading p,
	.setting-row p {
		font-size: 10px;
	}

	.avatar.dark {
		background: #102f20;
		color: #75df99;
		width: 45px;
		height: 45px;
	}

	.fields {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 15px;
		padding: 20px 0;
	}

	.fields label {
		display: flex;
		flex-direction: column;
		gap: 7px;
		font-size: 11px;
		font-weight: 700;
	}

	.fields input,
	.fields select {
		width: 100%;
		height: 45px;
		padding: 12px;
		border: none;
		border-radius: 12px;
		background: #f1f8f3;
		color: #10231a;
		font: inherit;
		font-weight: 500;
	}

	button {
		cursor: pointer;
		font-family: inherit;
		font-weight: 700;
	}

	.save {
		padding: 13px 21px;
		background: #16a34a;
		color: white;
		border: none;
		border-radius: 30px;
		font-size: 13px;
	}

	.secure {
		padding: 8px 12px;
		border-radius: 20px;
		background: #e9f6ed;
		color: #16a34a;
		font-size: 10px;
		font-weight: 700;
	}

	.setting-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 15px;
		padding: 17px 0;
		border-bottom: 1px solid #edf2ee;
	}

	.setting-row:last-child {
		border-bottom: none;
	}

	.setting-row strong {
		font-size: 11px;
	}

	.outline {
		padding: 8px 12px;
		background: white;
		color: #375044;
		border: 1px solid #dfe8e3;
		border-radius: 9px;
		font-size: 9px;
	}

	.toggle {
		width: 40px;
		height: 20px;
		accent-color: #16a34a;
		cursor: pointer;
		flex-shrink: 0;
	}

	/* Responsive */
	@media (max-width: 800px) {
		.sidebar {
			width: 190px;
		}

		.content {
			padding: 25px;
		}

		.layout {
			grid-template-columns: 1fr;
		}

		.settings-nav {
			flex-direction: row;
			flex-wrap: wrap;
		}
	}

	@media (max-width: 550px) {
		.sidebar {
			display: none;
		}

		.header {
			padding: 0 18px;
		}

		.content {
			padding: 20px 15px;
		}

		.intro h1 {
			font-size: 30px;
		}

		.card {
			padding: 18px;
		}

		.fields {
			grid-template-columns: 1fr;
		}
	}
</style>
