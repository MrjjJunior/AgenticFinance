<script>
	let showPassword = false;

	/**
	 * @param {{ preventDefault: () => void; }} event
	 */
	function handleSubmit(event) {
		event.preventDefault();
		// Authentication will be connected to your backend later.
	}
</script>

<div class="authpage">
	<!-- LEFT SECTION -->
	<section class="hero">
		<div class="logo">
			<div class="logo-icon">
				<span></span>
				<span></span>
			</div>
			<div class="brand">
				<span>Stock</span><span>Safe</span>
			</div>
		</div>

		<div class="hero-content">
			<p class="eyebrow">YOUR WEALTH, PROTECTED</p>

			<h1>Welcome back to calmer investing.</h1>

			<p class="description">
				Your portfolio, protection settings, and market insights are waiting for you.
			</p>
		</div>

		<div class="trust">
			<div class="avatars">
				<span>AM</span>
				<span>JL</span>
				<span>RK</span>
			</div>

			<div>
				<p>Trusted by 12,000+ investors</p>
				<small>Secure, simple and built around you.</small>
			</div>
		</div>
	</section>

	<!-- RIGHT SECTION -->
	<section class="form-section">
		<form class="login-form" onsubmit={handleSubmit}>
			<div class="logo form-logo">
				<div class="logo-icon">
					<span></span>
					<span></span>
				</div>
				<div class="brand">
					<span>Stock</span><span>Safe</span>
				</div>
			</div>

			<div class="form-heading">
				<p class="eyebrow">WELCOME BACK</p>
				<h2>Sign in to StockSafe</h2>
				<p>Enter your details to access your account.</p>
			</div>

			<!-- EMAIL INPUT -->
			<div class="field">
				<label for="email">Email address</label>

				<input
					id="email"
					name="email"
					type="email"
					placeholder="you@example.com"
					autocomplete="email"
					required
				/>
			</div>

			<!-- PASSWORD INPUT -->
			<div class="field password-field">
				<label for="password">Password</label>

				<div class="password-wrapper">
					<input
						id="password"
						name="password"
						type={showPassword ? 'text' : 'password'}
						placeholder="At least 6 characters"
						minlength="6"
						autocomplete="current-password"
						required
					/>

					<button
						type="button"
						class="eye"
						onclick={() => (showPassword = !showPassword)}
						aria-label={showPassword ? 'Hide password' : 'Show password'}
					>
						{showPassword ? 'Hide' : 'Show'}
					</button>
				</div>
			</div>

			<!-- REMEMBER ME AND FORGOT PASSWORD -->
			<div class="options">
				<label>
					<input type="checkbox" name="rememberMe" />
					Remember me
				</label>

				<a href="/forgot-password">Forgot password?</a>
			</div>

			<!-- SIGN IN BUTTON -->
			<button type="submit" class="sign-in">
				Sign in <span>→</span>
			</button>

			<!-- DIVIDER -->
			<div class="separator">
				<span>or continue with</span>
			</div>

			<!-- GOOGLE BUTTON -->
			<button type="button" class="google">
				<span>G</span> Google
			</button>

			<!-- CREATE ACCOUNT -->
			<p class="signup">
				New to StockSafe?
				<a href="/register">Create account</a>
			</p>
		</form>
	</section>

	<a href="/" class="back-home">← Back home</a>
</div>

<style>
	* {
		box-sizing: border-box;
	}

	.authpage {
		width: 1280px;
		min-height: 1080px;
		position: relative;
		background: #102f20;
		display: flex;
		flex-direction: column;
		font-family: Manrope, sans-serif;
	}

	/* LOGO */
	.logo {
		display: flex;
		align-items: center;
		gap: 9px;
	}

	.logo-icon {
		width: 34px;
		height: 34px;
		background: #16a34a;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.logo-icon span:first-child {
		width: 11px;
		height: 8px;
		border: 1.5px solid white;
	}

	.logo-icon span:last-child {
		width: 3px;
		height: 3px;
		border: 1px solid white;
		position: absolute;
		left: 12px;
		top: 6px;
	}

	.brand {
		font-size: 18px;
		font-weight: 800;
	}

	.brand span:first-child {
		color: #10231a;
	}

	.hero .brand span:first-child {
		color: white;
	}

	.brand span:last-child {
		color: #16a34a;
	}

	/* LEFT HERO SECTION */
	.hero {
		min-height: 1080px;
		padding: 80px 55px;

		background:
			radial-gradient(ellipse 96.15% 162.25% at 90% 80%, rgba(41, 184, 98, 0.25), transparent 35%),
			linear-gradient(135deg, #10231a, #103d28);

		display: flex;
		flex-direction: column;
		justify-content: space-between;
		align-items: flex-start;
	}

	.hero-content {
		width: 530px;
	}

	.eyebrow {
		color: #168844;
		font-family: 'DM Mono', monospace;
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 1.55px;
		line-height: 18px;
		text-transform: uppercase;
	}

	.hero h1 {
		width: 530px;
		margin-top: 20px;
		color: white;
		font-size: 64px;
		font-weight: 800;
		line-height: 1.02;
	}

	.description {
		width: 510px;
		margin-top: 20px;
		color: #b9d0c2;
		font-size: 16px;
		font-weight: 500;
		line-height: 27.2px;
	}

	.trust {
		display: flex;
		align-items: center;
		gap: 15px;
	}

	.avatars {
		display: flex;
	}

	.avatars span {
		width: 36px;
		height: 36px;
		margin-right: -7px;
		border: 2px solid #102f20;
		border-radius: 50%;
		background: #eaf7ee;
		color: #102f20;
		display: flex;
		justify-content: center;
		align-items: center;
		font-size: 9px;
		font-weight: 800;
	}

	.trust p {
		color: white;
		font-size: 12px;
		margin: 0;
	}

	.trust small {
		color: #98b4a5;
		font-size: 10px;
	}

	/* RIGHT FORM SECTION */
	.form-section {
		padding: 45px;
		background: #f7faf7;
		display: flex;
		align-items: flex-start;
	}

	.login-form {
		width: 480px;
		min-height: 669.9px;
		padding: 36px;
		background: white;
		border: 1px solid #dfe8e3;
		border-radius: 28px;
		box-shadow: 0 25px 65px rgba(5, 30, 17, 0.15);
		display: flex;
		flex-direction: column;
	}

	.form-heading {
		width: 100%;
		padding-top: 35px;
	}

	.form-heading .eyebrow {
		margin: 0;
	}

	.form-heading h2 {
		color: #10231a;
		font-size: 30px;
		font-weight: 800;
		line-height: 45px;
		margin: 7px 0 0;
	}

	.form-heading p:last-child {
		color: #64786e;
		font-size: 13px;
		font-weight: 500;
		margin: 7px 0 0;
	}

	/* INPUT FIELDS */
	.field {
		width: 100%;
		margin-top: 26px;
	}

	.field label {
		display: block;
		color: #10231a;
		font-size: 11px;
		font-weight: 700;
		margin-bottom: 7px;
	}

	.field input {
		width: 100%;
		height: 49.1px;
		padding: 14px 15px;
		background: #f1f8f3;
		border: none;
		border-radius: 12px;
		outline: none;
		color: #10231a;
		font-family: Manrope, sans-serif;
		font-size: 13px;
		font-weight: 500;
	}

	.field input::placeholder {
		color: rgba(16, 35, 26, 0.5);
	}

	.field input:focus {
		outline: 1px solid #16a34a;
	}

	.password-field {
		margin-top: 17px;
	}

	.password-wrapper {
		position: relative;
	}

	.password-wrapper input {
		padding-right: 65px;
	}

	.eye {
		position: absolute;
		right: 15px;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		color: #718379;
		cursor: pointer;
		font-size: 11px;
	}

	/* OPTIONS */
	.options {
		width: 100%;
		padding-top: 15px;
		display: flex;
		justify-content: space-between;
		align-items: center;
		color: #64786e;
		font-size: 11px;
	}

	.options label {
		display: flex;
		align-items: center;
		gap: 7px;
	}

	.options input {
		width: 13px;
		height: 13px;
		accent-color: #16a34a;
	}

	.options a,
	.signup a {
		color: #16a34a;
		font-weight: 700;
		text-decoration: none;
	}

	/* BUTTONS */
	.sign-in {
		width: 100%;
		height: 48px;
		margin-top: 22px;
		border: none;
		border-radius: 13px;
		background: #102f20;
		color: white;
		font-size: 12px;
		font-weight: 800;
		cursor: pointer;
	}

	.sign-in span {
		margin-left: 10px;
	}

	.separator {
		height: 36px;
		margin-top: 25px;
		border-bottom: 1px solid #dfe8e3;
		color: #87988f;
		text-align: center;
		font-size: 10px;
	}

	.separator span {
		background: white;
		padding: 0 10px;
	}

	.google {
		width: 100%;
		height: 43.6px;
		margin-top: 0;
		border: 1px solid #dfe8e3;
		border-radius: 12px;
		background: white;
		color: #10231a;
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
	}

	.google span {
		color: #4285f4;
		margin-right: 8px;
	}

	.signup {
		margin-top: 20px;
		color: #64786e;
		text-align: center;
		font-size: 11px;
	}

	/* BACK HOME */
	.back-home {
		position: absolute;
		top: 28px;
		left: 30px;
		padding: 9px 14px;
		border: none;
		border-radius: 99px;
		background: rgba(255, 255, 255, 0.08);
		color: #d1e1d7;
		font-size: 12px;
		text-decoration: none;
	}
</style>
