<script lang="ts">

  import { DropdownMenu } from 'bits-ui';
  import { createEventDispatcher, getContext, tick } from 'svelte';
  import { fade } from 'svelte/transition';
  import { goto } from '$app/navigation';

  import { getUsage } from '$lib/apis';
  import { userSignOut } from '$lib/apis/auths';

  import { showSettings, mobile, showSidebar, showShortcuts, user, config } from '$lib/stores';

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
  const dispatch = createEventDispatcher();

  export let show = false;
  export let role = '';
  export let help = false;
  export let className = 'max-w-[240px]';

  let usage = null;

  const getUsageInfo = async () => {
    try {
      const res = await getUsage(localStorage.token);
      usage = res ?? null;
    } catch (error) {
      console.error('Error fetching usage info:', error);
      usage = null;
    }
  };

  // Fetch usage info whenever dropdown opens
  $: if (show) getUsageInfo();
</script>

<ShortcutsModal bind:show={$showShortcuts} />

<DropdownMenu.Root
  bind:open={show}
  onOpenChange={(state) => dispatch('change', state)}
>
  <DropdownMenu.Trigger>
    <slot>
      <!-- fallback trigger if no slot content -->
      <button aria-label="User menu" class="btn-user-icon">
        <!-- You can put a default user icon SVG here -->
        👤
      </button>
    </slot>
  </DropdownMenu.Trigger>

<DropdownMenu.Root>
  <DropdownMenu.Content
    class="w-full {className} text-sm rounded-xl px-1 py-1.5 z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg font-primary"
    sideOffset={4}
    side="bottom"
    align="start"
  >
    <!-- Wrap content with a div for fade transition -->
    <div transition:fade={{ duration: 100 }}>
      <DropdownMenu.Item
        class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition cursor-pointer"
        on:click={async () => {
          await showSettings.set(true);
          show = false;
          if ($mobile) {
            await tick();
            showSidebar.set(false);
          }
        }}
      >
        <div class="self-center mr-3">
          <Settings className="w-5 h-5" strokeWidth="1.5" />
        </div>
        <div class="self-center truncate">{$i18n.t('Settings')}</div>
      </DropdownMenu.Item>

      <DropdownMenu.Item
        class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition cursor-pointer"
        on:click={() => {
          dispatch('show', 'archived-chat');
          show = false;
          if ($mobile) {
            showSidebar.set(false);
          }
        }}
      >
        <div class="self-center mr-3">
          <ArchiveBox className="size-5" strokeWidth="1.5" />
        </div>
        <div class="self-center truncate">{$i18n.t('Archived Chats')}</div>
      </DropdownMenu.Item>

      {#if role === 'admin'}
        <DropdownMenu.Item
          class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition select-none cursor-pointer"
          on:click={() => {
            show = false;
            if ($mobile) {
              showSidebar.set(false);
            }
            goto('/playground');
          }}
        >
          <div class="self-center mr-3">
            <Code className="size-5" strokeWidth="1.5" />
          </div>
          <div class="self-center truncate">{$i18n.t('Playground')}</div>
        </DropdownMenu.Item>

        <DropdownMenu.Item
          class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition select-none cursor-pointer"
          on:click={() => {
            show = false;
            if ($mobile) {
              showSidebar.set(false);
            }
            goto('/admin');
          }}
        >
          <div class="self-center mr-3">
            <UserGroup className="w-5 h-5" strokeWidth="1.5" />
          </div>
          <div class="self-center truncate">{$i18n.t('Admin Panel')}</div>
        </DropdownMenu.Item>
      {/if}

      {#if help}
        <hr class="border-gray-100 dark:border-gray-800 my-1 p-0" />

        {#if $user?.role === 'admin'}
          <DropdownMenu.Item
            class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
            on:click={() => {
              window.open('https://edenhub.io', '_blank');
              show = false;
            }}
          >
            <QuestionMarkCircle className="size-5" />
            <div class="flex items-center">{$i18n.t('Documentation')}</div>
          </DropdownMenu.Item>

          <DropdownMenu.Item
            class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
            on:click={() => {
              window.open('https://edenhub.io', '_blank');
              show = false;
            }}
          >
            <Map className="size-5" />
            <div class="flex items-center">{$i18n.t('Releases')}</div>
          </DropdownMenu.Item>
        {/if}

        <DropdownMenu.Item
          class="flex gap-2 items-center py-1.5 px-3 text-sm select-none w-full cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md transition"
          on:click={async () => {
            showShortcuts.set(!$showShortcuts);
            show = false;
            if ($mobile) {
              await tick();
              showSidebar.set(false);
            }
          }}
        >
          <Keyboard className="size-5" />
          <div class="flex items-center">{$i18n.t('Keyboard shortcuts')}</div>
        </DropdownMenu.Item>
      {/if}

      <hr class="border-gray-100 dark:border-gray-800 my-1 p-0" />

      <DropdownMenu.Item
        class="flex rounded-md py-1.5 px-3 w-full hover:bg-gray-50 dark:hover:bg-gray-800 transition cursor-pointer"
        on:click={async () => {
          const res = await userSignOut();
          user.set(null);
          localStorage.removeItem('token');
          location.href = res?.redirect_url ?? '/auth';
          show = false;
        }}
      >
        <div class="self-center mr-3">
          <SignOut className="w-5 h-5" strokeWidth="1.5" />
        </div>
        <div class="self-center truncate">{$i18n.t('Sign Out')}</div>
      </DropdownMenu.Item>

      {#if usage && usage?.user_ids?.length > 0}
        <hr class="border-gray-100 dark:border-gray-800 my-1 p-0" />

        <Tooltip
          content={
            usage?.model_ids && usage?.model_ids.length > 0
              ? `${$i18n.t('Running')}: ${usage.model_ids.join(', ')} ✨`
              : ''
          }
        >
          <div
            class="flex rounded-md py-1 px-3 text-xs gap-2.5 items-center"
            on:mouseenter={() => getUsageInfo()}
          >
            <div class="flex items-center">
              <span class="relative flex size-2">
                <span
                  class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"
                />
                <span class="relative inline-flex rounded-full size-2 bg-green-500" />
              </span>
            </div>

            <div>
              <span>{$i18n.t('Active Users')}:</span>
              <span class="font-semibold">{usage?.user_ids?.length}</span>
            </div>
          </div>
        </Tooltip>
      {/if}
    </div>
  </DropdownMenu.Content>
</DropdownMenu.Root>
