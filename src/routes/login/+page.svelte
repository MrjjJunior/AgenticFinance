<script>
  import { goto } from '$app/navigation';
  import Logo from '#lib/components/Logo.svelte';

  let email = '';
  let password = '';
  let remember = false;
  let showPassword = false;

  async function handleLogin() {
    const saved = localStorage.getItem('stocksafe_user');
    const user = saved ? JSON.parse(saved) : null;

    if (user?.role === 'manufacturer') {
      await goto('/manufacturer');
    } else {
      await goto('/supplier');
    }
  }
</script>

<svelte:head>
  <title>Sign in — StockSafe</title>
</svelte:head>

<div class="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-[#FAFAFA] text-[#1A1D1B]">
  <!-- LEFT PANEL -->
  <div class="hidden lg:flex flex-col justify-between left-panel-gradient text-white p-12 xl:p-16 relative overflow-hidden">
    <div class="pointer-events-none absolute -bottom-24 -right-24 w-[480px] h-[480px] rounded-full bg-[#12A150]/10 blur-3xl"></div>

    <div class="relative z-10">
      <Logo href="/" darkText={false} />
    </div>

    <div class="relative z-10 max-w-md my-auto">
      <h1 class="text-4xl xl:text-[44px] font-bold tracking-tight leading-[1.15] text-white mb-5">
        Welcome back to calmer investing.
      </h1>
      <p class="text-[15px] leading-relaxed text-neutral-300/90">
        Your portfolio, protection settings, and market insights are waiting for you.
      </p>
    </div>

    <div class="relative z-10 flex items-center gap-3.5">
      <div class="flex -space-x-2.5">
        <div class="w-8 h-8 rounded-full bg-[#D9E8DF] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-[#0D2418]">JD</div>
        <div class="w-8 h-8 rounded-full bg-[#A8D5BA] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-[#0D2418]">AK</div>
        <div class="w-8 h-8 rounded-full bg-[#12A150] border-2 border-[#0D2418] flex items-center justify-center text-[11px] font-bold text-white">SM</div>
      </div>
      <span class="text-xs font-medium text-neutral-300">
        Trusted by <strong class="text-white font-semibold">50,000+</strong> investors
      </span>
    </div>
  </div>

  <!-- RIGHT PANEL -->
  <div class="flex flex-col items-center justify-center px-6 py-12 sm:px-12 bg-[#F7F8F7]">
    <div class="w-full max-w-[420px] bg-white rounded-2xl border border-neutral-200/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-8 sm:p-10">
      <div class="mb-6">
        <Logo href="/" darkText={true} size="sm" />
      </div>

      <div class="mb-7">
        <h2 class="text-2xl font-bold tracking-tight text-[#1A1D1B]">Sign in to StockSafe</h2>
        <p class="text-xs text-neutral-500 mt-1.5">Enter your credentials to access your workspace.</p>
      </div>

      <form on:submit|preventDefault={handleLogin} class="space-y-4">
        <div>
          <label for="email" class="block text-xs font-semibold text-neutral-700 mb-1.5">Email address</label>
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
          <label for="password" class="block text-xs font-semibold text-neutral-700 mb-1.5">Password</label>
          <div class="relative">
            {#if showPassword}
              <input
                type="text"
                id="password"
                bind:value={password}
                required
                placeholder="••••••••"
                class="w-full px-3.5 py-2.5 pr-10 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
              />
            {:else}
              <input
                type="password"
                id="password"
                bind:value={password}
                required
                placeholder="••••••••"
                class="w-full px-3.5 py-2.5 pr-10 text-sm bg-white border border-neutral-200 rounded-xl text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:border-[#12A150] focus:ring-2 focus:ring-[#12A150]/15 transition-all"
              />
            {/if}
            <button
              type="button"
              on:click={() => (showPassword = !showPassword)}
              aria-label="Toggle password visibility"
              class="absolute inset-y-0 right-3 flex items-center text-neutral-400 hover:text-neutral-600 transition-colors"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            </button>
          </div>
        </div>

        <div class="flex items-center justify-between pt-1">
          <label class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              bind:checked={remember}
              class="w-3.5 h-3.5 rounded border-neutral-300 text-[#12A150] focus:ring-[#12A150]/20"
            />
            <span class="text-xs text-neutral-600">Remember me</span>
          </label>
          <a href="/forgot-password" class="text-xs font-medium text-[#12A150] hover:text-[#0e8541] transition-colors">
            Forgot password?
          </a>
        </div>

        <button
          type="submit"
          class="w-full mt-2 bg-[#0D2418] hover:bg-[#143624] text-white font-medium text-sm py-3 px-4 rounded-xl inline-flex items-center justify-center gap-2 transition-all shadow-xs cursor-pointer"
        >
          <span>Sign in</span>
          <span aria-hidden="true">&rarr;</span>
        </button>
      </form>

      <p class="text-center text-xs text-neutral-500 mt-6">
        Don't have an account?
        <a href="/registration" class="font-semibold text-[#12A150] hover:text-[#0e8541] transition-colors ml-0.5">
          Sign up
        </a>
      </p>
    </div>
  </div>
</div>

<style>
  .left-panel-gradient {
    background: radial-gradient(circle at 85% 65%, #16422B 0%, #0D2418 55%, #091A11 100%);
  }
</style>