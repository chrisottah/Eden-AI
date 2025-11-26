<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';

	let token = '';
	let newPassword = '';
	let confirmPassword = '';
	let loading = false;
	let verifying = true;
	let tokenValid = false;
	let resetSuccess = false;

	onMount(async () => {
		token = $page.url.searchParams.get('token') || '';
		
		if (!token) {
			toast.error('Invalid reset link');
			goto('/auth');
			return;
		}

		// Verify token is valid
		try {
			const response = await fetch(`${WEBUI_BASE_URL}/api/v1/auths/reset-password/verify/${token}`);
			const data = await response.json();
			
			tokenValid = data.valid;
			if (!tokenValid) {
				toast.error(data.message || 'Invalid or expired reset link');
			}
		} catch (error) {
			toast.error('Error verifying reset link');
			tokenValid = false;
		} finally {
			verifying = false;
		}
	});

	const handleSubmit = async () => {
		if (newPassword.length < 8) {
			toast.error('Password must be at least 8 characters long');
			return;
		}

		if (newPassword !== confirmPassword) {
			toast.error('Passwords do not match');
			return;
		}

		loading = true;

		try {
			const response = await fetch(`${WEBUI_BASE_URL}/api/v1/auths/reset-password`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					token,
					new_password: newPassword
				})
			});

			const data = await response.json();

			if (response.ok) {
				resetSuccess = true;
				toast.success('Password reset successful!');
				setTimeout(() => goto('/auth'), 3000);
			} else {
				toast.error(data.detail || 'Failed to reset password');
			}
		} catch (error) {
			toast.error('An error occurred. Please try again.');
		} finally {
			loading = false;
		}
	};
</script>

<svelte:head>
	<title>Reset Password - Eden AI</title>
</svelte:head>

<div class="w-full h-screen max-h-[100dvh] flex items-center justify-center bg-gray-50 dark:bg-gray-900">
	<div class="w-full max-w-md px-6">
		<div class="bg-white dark:bg-gray-850 rounded-2xl shadow-lg p-8">
			{#if verifying}
				<!-- Verifying Token -->
				<div class="text-center space-y-4">
					<Spinner className="size-8 mx-auto" />
					<p class="text-gray-600 dark:text-gray-400">Verifying reset link...</p>
				</div>
			{:else if !tokenValid}
				<!-- Invalid Token -->
				<div class="text-center space-y-4">
					<div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto">
						<svg class="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</div>
					
					<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
						Invalid Reset Link
					</h2>
					
					<p class="text-sm text-gray-600 dark:text-gray-400">
						This password reset link is invalid or has expired. Please request a new one.
					</p>

					<div class="space-y-2">
						<button
							on:click={() => goto('/auth/forgot-password')}
							class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition"
						>
							Request New Reset Link
						</button>
						
						<button
							on:click={() => goto('/auth')}
							class="w-full bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-900 dark:text-white font-medium py-3 rounded-lg transition"
						>
							Back to Login
						</button>
					</div>
				</div>
			{:else if resetSuccess}
				<!-- Success Message -->
				<div class="text-center space-y-4">
					<div class="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto">
						<svg class="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					
					<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
						Password Reset Successful!
					</h2>
					
					<p class="text-sm text-gray-600 dark:text-gray-400">
						Your password has been updated. Redirecting to login...
					</p>

					<button
						on:click={() => goto('/auth')}
						class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg transition"
					>
						Go to Login Now
					</button>
				</div>
			{:else}
				<!-- Reset Password Form -->
				<div class="space-y-6">
					<!-- Header -->
					<div class="text-center">
						<h1 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
							Create New Password
						</h1>
						<p class="text-sm text-gray-600 dark:text-gray-400">
							Enter your new password below
						</p>
					</div>

					<!-- Form -->
					<form on:submit|preventDefault={handleSubmit} class="space-y-4">
						<div>
							<label for="new-password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								New Password
							</label>
							<SensitiveInput
								bind:value={newPassword}
								type="password"
								id="new-password"
								placeholder="Enter new password"
								autocomplete="new-password"
								required
								class="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
							/>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Minimum 8 characters
							</p>
						</div>

						<div>
							<label for="confirm-password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Confirm Password
							</label>
							<SensitiveInput
								bind:value={confirmPassword}
								type="password"
								id="confirm-password"
								placeholder="Confirm new password"
								autocomplete="new-password"
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
								<span>Resetting Password...</span>
							{:else}
								<span>Reset Password</span>
							{/if}
						</button>
					</form>

					<!-- Security Notice -->
					<div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
						<p class="text-xs text-blue-800 dark:text-blue-300">
							<strong>🔒 Security Tip:</strong> Choose a strong password that you don't use on other sites.
						</p>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>