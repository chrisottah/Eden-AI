<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { createEventDispatcher, getContext, onMount } from 'svelte';

	import { flyAndScale } from '$lib/utils/transitions';
	import { goto } from '$app/navigation';
	import { fade, slide } from 'svelte/transition';
	import { toast } from 'svelte-sonner';

	import { getUsage } from '$lib/apis';
	import { userSignOut } from '$lib/apis/auths';

	import { showSettings, mobile, showSidebar, showShortcuts, user } from '$lib/stores';

	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import ArchiveBox from '$lib/components/icons/ArchiveBox.svelte';
	import QuestionMarkCircle from '$lib/components/icons/QuestionMarkCircle.svelte';
	import Map from '$lib/components/icons/Map.svelte';
	import Keyboard from '$lib/components/icons/Keyboard.svelte';
	import ShortcutsModal from '$lib/components/chat/ShortcutsModal.svelte';
	import Settings from '$lib/components/icons/Settings.svelte';
	import Code from '$lib/components/icons/Code.svelte';
	import UserGroup from '$lib/components/icons/UserGroup.svelte';
	import SignOut from '$lib/components/icons/SignOut.svelte';

	const i18n = getContext('i18n');

	export let show = false;
	export let role = '';
	export let help = false;
	export let className = 'max-w-[240px]';

	const dispatch = createEventDispatcher();

	let usage = null;
	const getUsageInfo = async () => {
		const res = await getUsage(localStorage.token).catch((error) => {
			console.error('Error fetching usage info:', error);
		});

		if (res) {
			usage = res;
		} else {
			usage = null;
		}
	};

	$: if (show) {
		getUsageInfo();
	}
</script>

<ShortcutsModal bind:show={$showShortcuts} />

<!-- svelte-ignore a11y-no-static-element-interactions -->
<DropdownMenu.Root
	bind:open={show}
	onOpenChange={(state) => {
		dispatch('change', state);
	}}
>
	<DropdownMenu.Trigger>
		<slot />
	</DropdownMenu.Trigger>

	<slot name="content">
		<DropdownMenu.Content
			class="w-full {className} text-sm rounded-xl px-1 py-1.5 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg font-primary"
			sideOffset={4}
			side="bottom"
			align="start"
			transition={(e) => fade(e, { duration: 100 })}
		>
			<!-- ==================== PREMIUM UPGRADE BUTTON ==================== -->
			<!-- 
			🎯 PREMIUM FEATURE STATUS:
			- Button: ✅ Added to user menu
			- Styling: ✅ Gold/premium theme
			- Current state: DISABLED (Coming Soon modal)

			TO ACTIVATE PAYMENT GATEWAY:
			1. Replace toast.info() with: goto('/premium') or window.location.href = 'PAYMENT_URL'
			2. Set up payment gateway backend route
			3. Implement subscription logic
			4. Update user model with premium status
			-->
			<DropdownMenu.Item
				class="flex rounded-md py-1.5 px-3 w-full hover:bg-gradient-to-r hover:from-yellow-50 hover:to-amber-50 dark:hover:from-yellow-900/20 dark:hover:to-amber-900/20 transition group"
				on:click={() => {
					// TEMPORARY: Shows "Coming Soon" message
					toast.info('🌟 Premium features coming soon! Unlock exclusive models and enhanced capabilities.');
					show = false;
					
					// TODO: When payment gateway is ready, replace above with:
					// goto('/premium'); // or your payment page route
					// OR
					// window.location.href = 'https://your-payment-gateway.com';
				}}
			>
				<div class="self-center mr-3">
					<!-- Crown Icon for Premium -->
					<svg 
						class="w-5 h-5 text-yellow-600 dark:text-yellow-400 group-hover:text-yellow-700 dark:group-hover:text-yellow-300 transition" 
						fill="currentColor" 
						viewBox="0 0 20 20"
					>
						<path fill-rule="evenodd" d="M10 2a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L10 14.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L2.818 8.374a.75.75 0 01.416-1.28l4.21-.611L9.327 2.42A.75.75 0 0110 2z" clip-rule="evenodd" />
					</svg>
				</div>
				<div class="self-center truncate font-medium text-yellow-700 dark:text-yellow-400">
					{$i18n.t('Upgrade to Premium')}
				</div>
				<div class="ml-auto">
					<!-- Optional badge -->
					<span class="text-[10px] px-1.5 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 font-semibold">
						NEW
					</span>
				</div>
			</DropdownMenu.Item>

			<hr class="border-gray-100 dark:border-gray-800 my-1 p-0" />
			<!-- ==================== END PREMIUM BUTTON ==================== -->

			<DropdownMenu.Item
				class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition"
				on:click={async () => {
					await showSettings.set(true);
					show = false;

					if ($mobile) {
						showSidebar.set(false);
					}
				}}
			>
				<div class=" self-center mr-3">
					<Settings className="w-5 h-5" strokeWidth="1.5" />
				</div>
				<div class=" self-center truncate">{$i18n.t('Settings')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition"
				on:click={() => {
					dispatch('show', 'archived-chat');
					show = false;

					if ($mobile) {
						showSidebar.set(false);
					}
				}}
			>
				<div class=" self-center mr-3">
					<ArchiveBox className="size-5" strokeWidth="1.5" />
				</div>
				<div class=" self-center truncate">{$i18n.t('Archived Chats')}</div>
			</DropdownMenu.Item>

			{#if role === 'admin'}
				<DropdownMenu.Item
					class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition select-none"
					on:click={() => {
						show = false;
						if ($mobile) {
							showSidebar.set(false);
						}
						goto('/playground');
					}}
				>
					<div class=" self-center mr-3">
						<Code className="size-5" strokeWidth="1.5" />
					</div>
					<div class=" self-center truncate">{$i18n.t('Playground')}</div>
				</DropdownMenu.Item>

				<DropdownMenu.Item
					class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition select-none"
					on:click={() => {
						show = false;
						if ($mobile) {
							showSidebar.set(false);
						}
						goto('/admin');
					}}
				>
					<div class=" self-center mr-3">
						<UserGroup className="w-5 h-5" strokeWidth="1.5" />
					</div>
					<div class=" self-center truncate">{$i18n.t('Admin Panel')}</div>
				</DropdownMenu.Item>
			{/if}

			{#if help}
				<hr class=" border-gray-100 dark:border-gray-800 my-1 p-0" />

				<!-- {$i18n.t('Help')} -->
				<DropdownMenu.Item
					class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
					id="chat-share-button"
					on:click={() => {
						window.open('https://edenhub.io', '_blank');
						show = false;
					}}
				>
					<QuestionMarkCircle className="size-5" />
					<div class="flex items-center">{$i18n.t('Documentation')}</div>
				</DropdownMenu.Item>

				<!-- Releases -->
				<DropdownMenu.Item
					class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
					id="menu-item-releases"
					on:click={() => {
						window.open('https://edenhub.io', '_blank');
						show = false;
					}}
				>
					<Map className="size-5" />
					<div class="flex items-center">{$i18n.t('Releases')}</div>
				</DropdownMenu.Item>

				<DropdownMenu.Item
					class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
					id="chat-share-button"
					on:click={() => {
						showShortcuts.set(!$showShortcuts);
						show = false;
					}}
				>
					<Keyboard className="size-5" />
					<div class="flex items-center">{$i18n.t('Keyboard shortcuts')}</div>
				</DropdownMenu.Item>
			{/if}

			<hr class=" border-gray-100 dark:border-gray-800 my-1 p-0" />

			<DropdownMenu.Item
				class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition"
				on:click={async () => {
					const res = await userSignOut();
					user.set(null);
					localStorage.removeItem('token');

					location.href = res?.redirect_url ?? '/auth';
					show = false;
				}}
			>
				<div class=" self-center mr-3">
					<SignOut className="w-5 h-5" strokeWidth="1.5" />
				</div>
				<div class=" self-center truncate">{$i18n.t('Sign Out')}</div>
			</DropdownMenu.Item>

			{#if usage}
				{#if usage?.user_ids?.length > 0}
					<hr class=" border-gray-100 dark:border-gray-800 my-1 p-0" />

					<Tooltip
						content={usage?.model_ids && usage?.model_ids.length > 0
							? `${$i18n.t('Running')}: ${usage.model_ids.join(', ')} ✨`
							: ''}
					>
						<div
							class="flex rounded-md py-1 px-3 text-xs gap-2.5 items-center"
							on:mouseenter={() => {
								getUsageInfo();
							}}
						>
							<div class=" flex items-center">
								<span class="relative flex size-2">
									<span
										class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"
									/>
									<span class="relative inline-flex rounded-full size-2 bg-green-500" />
								</span>
							</div>

							<div class=" ">
								<span class="">
									{$i18n.t('Active Users')}:
								</span>
								<span class=" font-semibold">
									{usage?.user_ids?.length}
								</span>
							</div>
						</div>
					</Tooltip>
				{/if}
			{/if}

			<!-- <DropdownMenu.Item class="flex items-center py-1.5 px-3 text-sm ">
				<div class="flex items-center">Profile</div>
			</DropdownMenu.Item> -->
		</DropdownMenu.Content>
	</slot>
</DropdownMenu.Root>