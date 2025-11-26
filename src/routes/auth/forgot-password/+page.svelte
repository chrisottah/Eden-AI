<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import Spinner from '$lib/components/common/Spinner.svelte';

	let email = '';
	let loading = false;
	let emailSent = false;

	const handleSubmit = async () => {
		if (!email) {
			toast.error('Please enter your email address');
			return;
		}

		loading = true;

		try {
			const response = await fetch(`${WEBUI_BASE_URL}/api/v1/auths/forgot-password`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ email })
			});

			const data = await response.json();

			if (response.ok) {
				emailSent = true;
				toast.success('Password reset link sent! Check your email.');
			} else {
				toast.error(data.detail || 'Failed to send reset link');
			}
		} catch (error) {
			toast.error('An error occurred. Please try again.');
		} finally {
			loading = false;
		}
	};
</script>

<svelte:head>
	<title>Forgot Password - Eden AI</title>
</svelte:head>

<div class="w-full h-screen max-h-[100dvh] flex items-center justify-center bg-gray-50 dark:bg-gray-900">
	<div class="w-full max-w-md px-6">
		<div class="bg-white dark:bg-gray-850 rounded-2xl shadow-lg p-8">
			<!-- Header -->
			<div class="text-center mb-6">
				<h1 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
					Forgot Password?
				</h1>
				<p class="text-sm text-gray-600 dark:text-gray-400">
					Enter your email and we'll send you a link to reset your password
				</p>
			</div>

			{#if !emailSent}
				<!-- Form -->
				<form on:submit|preventDefault={handleSubmit} class="space-y-4">
					<div>
						<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Email Address
						</label>
						<input
							type="email"
							id="email"
							bind:value={email}
							placeholder="your-email@example.com"
							required
							class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
						/>
					</div>

					<button
						type="submit"
						disabled={loading}
						class="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-3 rounded-lg transition flex items-center justify-center gap-2"
					>
						{#if loading}
							<Spinner className="size-4" />
							<span>Sending...</span>
						{:else}
							<span>Send Reset Link</span>
						{/if}
					</button>
				</form>

				<!-- Back to Login -->
				<div class="mt-6 text-center">
					<button
						on:click={() => goto('/auth')}
						class="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
					>
						← Back to Login
					</button>
				</div>
			{:else}
				<!-- Success Message -->
				<div class="text-center space-y-4">
					<div class="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
						<svg class="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5m0 0l-1.14.76a2 2 0 01-2.22 0l-1.14-.76" />
						</svg>
					</div>
					
					<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
						Check Your Email
					</h2>
					
					<p class="text-sm text-gray-600 dark:text-gray-400">
						If an account exists for <strong>{email}</strong>, you'll receive a password reset link shortly.
					</p>

					<div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 text-left">
						<p class="text-xs text-yellow-800 dark:text-yellow-300">
							<strong>⚠️ Important:</strong> The link expires in 1 hour. If you don't see the email, check your spam folder.
						</p>
					</div>

					<button
						on:click={() => goto('/auth')}
						class="w-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-medium py-3 rounded-lg transition"
					>
						Return to Login
					</button>
				</div>
			{/if}
		</div>
	</div>
</div>