<script>
	let showPassword = false;
</script>

<div class="auth-page">
	
	<section class="hero">
		<a href="/" class="logo">
			<span class="logo-icon">S</span>
			<span>Stock<strong>Safe</strong></span>
		</a>

		<div class="hero-content">
			<p class="eyebrow">YOUR WEALTH, PROTECTED</p>
			<h1>A smarter portfolio starts here.</h1>
			<p class="description">
				Create your StockSafe account and take control of your financial future in minutes.
			</p>
		</div>

		<div class="trust">
			<div class="avatars">
				<span>AM</span>
				<span>JL</span>
				<span>RK</span>
			</div>
			<div>
				<strong>Trusted by 12,000+ investors</strong>
				<small>Secure, simple and built around you.</small>
			</div>
		</div>
	</section>

	<section class="form-section">
		<form class="form">
			<a href="/" class="logo dark">
				<span class="logo-icon">S</span>
				<span>Stock<strong>Safe</strong></span>
			</a>

			<div class="form-heading">
				<p class="eyebrow">GET STARTED</p>
				<h2>Create your account</h2>
				<p>Join StockSafe — it only takes a minute.</p>
			</div>

			<label>
				Full name
				<input type="text" placeholder="e.g. Ada Mensah" />
			</label>

			<label>
				Email address
				<input type="email" placeholder="you@example.com" />
			</label>

			<label>
				Password
				<div class="password-field">
					<input type={showPassword ? 'text' : 'password'} placeholder="At least 6 characters" />
					<button type="button" onclick={() => (showPassword = !showPassword)}>
						{showPassword ? 'Hide' : 'Show'}
					</button>
				</div>
			</label>

			<div class="password-strength">
				<div></div>
				<div></div>
				<div></div>
			</div>
			<small class="hint">Use 8+ characters for a strong password</small>

			<button type="submit" class="submit-btn"> Create account → </button>

			<div class="divider">or continue with</div>

			<button type="button" class="google-btn">
				<strong>G</strong> Google
			</button>

			<p class="signin">
				Already have an account?
				<a href="/login">Sign in</a>
			</p>
		</form>
	</section>

	<a href="/" class="back-home">← Back home</a>
</div>

<style>
	* {
		box-sizing: border-box;
	}

	.auth-page {
		min-height: 100vh;
		display: grid;
		grid-template-columns: 1fr 1fr;
		font-family: Manrope, sans-serif;
		color: #10231a;
	}

	.hero {
		background:
			radial-gradient(ellipse at 90% 80%, #29b86240, transparent 45%),
			linear-gradient(135deg, #10231a, #103d28);
		color: white;
		padding: 80px 55px;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 9px;
		color: white;
		text-decoration: none;
		font-size: 18px;
		font-weight: 800;
	}

	.logo strong {
		color: #16a34a;
	}

	.logo-icon {
		width: 34px;
		height: 34px;
		display: grid;
		place-items: center;
		background: #16a34a;
		border-radius: 50%;
	}

	.hero-content {
		max-width: 530px;
	}

	.eyebrow {
		color: #168844;
		font-family: monospace;
		font-size: 11px;
		letter-spacing: 1.55px;
	}

	h1 {
		font-size: clamp(42px, 5vw, 64px);
		line-height: 1.05;
		margin: 20px 0;
	}

	.description {
		color: #b9d0c2;
		line-height: 1.7;
	}

	.trust,
	.avatars {
		display: flex;
		align-items: center;
	}

	.trust {
		gap: 15px;
	}

	.avatars span {
		width: 36px;
		height: 36px;
		margin-right: -7px;
		border-radius: 50%;
		background: #eaf7ee;
		color: #102f20;
		border: 2px solid #102f20;
		display: grid;
		place-items: center;
		font-size: 9px;
		font-weight: 800;
	}

	.trust strong,
	.trust small {
		display: block;
		font-size: 12px;
	}

	.trust small {
		color: #98b4a5;
		margin-top: 4px;
		font-size: 10px;
	}

	.form-section {
		background: #f7faf7;
		padding: 45px;
		display: grid;
		place-items: center;
	}

	.form {
		width: 100%;
		max-width: 480px;
		padding: 36px;
		background: white;
		border: 1px solid #dfe8e3;
		border-radius: 28px;
		box-shadow: 0 25px 65px #051e111a;
	}

	.dark {
		color: #10231a;
	}

	.form-heading {
		margin: 35px 0 25px;
	}

	.form-heading h2 {
		font-size: 30px;
		margin: 8px 0;
	}

	.form-heading p:last-child {
		color: #64786e;
		font-size: 13px;
	}

	label {
		display: block;
		font-size: 11px;
		font-weight: 700;
		margin-bottom: 17px;
	}

	input {
		width: 100%;
		padding: 15px;
		margin-top: 8px;
		border: none;
		border-radius: 12px;
		background: #f1f8f3;
		font: inherit;
		font-size: 13px;
		outline-color: #16a34a;
	}

	.password-field {
		position: relative;
	}

	.password-field button {
		position: absolute;
		right: 12px;
		top: 50%;
		transform: translateY(-35%);
		border: none;
		background: none;
		color: #64786e;
		cursor: pointer;
	}

	.password-strength {
		display: flex;
		gap: 5px;
		margin-top: -7px;
	}

	.password-strength div {
		flex: 1;
		height: 3px;
		background: #dfe8e3;
		border-radius: 5px;
	}

	.hint {
		display: block;
		color: #819086;
		font-size: 9px;
		margin-top: 7px;
	}

	.submit-btn,
	.google-btn {
		width: 100%;
		padding: 14px;
		border-radius: 12px;
		font-weight: 800;
		cursor: pointer;
	}

	.submit-btn {
		margin-top: 22px;
		color: white;
		background: #102f20;
		border: none;
	}

	.divider {
		text-align: center;
		color: #87988f;
		font-size: 10px;
		margin: 25px 0;
	}

	.google-btn {
		background: white;
		border: 1px solid #dfe8e3;
	}

	.google-btn strong {
		color: #4285f4;
		margin-right: 8px;
	}

	.signin {
		text-align: center;
		font-size: 11px;
		color: #64786e;
		margin-top: 25px;
	}

	a {
		color: #16a34a;
		font-weight: 800;
	}

	.back-home {
		position: absolute;
		top: 28px;
		left: 30px;
		color: white;
		text-decoration: none;
		font-size: 12px;
	}

	@media (max-width: 800px) {
		.auth-page {
			grid-template-columns: 1fr;
		}

		.hero {
			min-height: 450px;
			padding: 40px 25px;
		}

		.form-section {
			padding: 30px 15px;
		}

		.form {
			padding: 25px;
		}

		.back-home {
			display: none;
		}
	}
</style>
