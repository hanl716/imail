<template>
  <div class="im-view-wrapper">
    <button @click="openComposeModal(null)" class="compose-new-button">Compose New</button>
    <div class="im-view">
      <ConversationList
        :conversations="threadStore.threads"
        :loading="threadStore.loadingThreads"
        :error="threadStore.error"
        @conversationSelected="handleConversationSelected"
      />
      <ConversationPanel
        :messages="threadStore.activeThreadMessages"
        :conversationInfo="activeThreadInfo"
        :loading="threadStore.loadingMessages"
        :error="threadStore.error"
        @replyToMessage="handleReplyToMessage"
        @useSuggestion="handleUseSuggestion" <!-- Added event handler -->
      />
    </div>
    <ComposeModal
      :isVisible="showComposeModal"
      :initialData="composeInitialData"
      @close="closeComposeModal"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'; // Added watch
import ConversationList from '@/components/im_ui/ConversationList.vue';
import ConversationPanel from '@/components/im_ui/ConversationPanel.vue';
import ComposeModal from '@/components/ComposeModal.vue';
import { useThreadStore } from '@/stores/threadStore';
import { useAuthStore } from '@/stores/auth';
import { useEmailAccountsStore } from '@/stores/emailAccounts'; // Import accounts store

const threadStore = useThreadStore();
const authStore = useAuthStore();
const emailAccountsStore = useEmailAccountsStore(); // Use accounts store

const showComposeModal = ref(false);
const composeInitialData = ref(null);

const activeThreadInfo = computed(() => {
  return threadStore.getActiveThreadDetails;
});

const handleConversationSelected = (threadId) => {
  if (threadId) {
    threadStore.fetchMessagesForThread(threadId);
  } else {
    threadStore.clearActiveThread();
  }
};

const openComposeModal = (initialData) => {
  composeInitialData.value = initialData;
  showComposeModal.value = true;
};

const closeComposeModal = () => {
  showComposeModal.value = false;
  composeInitialData.value = null; // Clear initial data
};

const handleReplyToMessage = (messageToReply) => {
  // Basic quoting and subject prefix for reply
  const initialData = {
    to_recipients: [messageToReply.sender_address], // Assuming sender_address is a single email string
    subject: `Re: ${messageToReply.subject || ''}`,
    quoted_body: `\n\n\n--- On ${new Date(messageToReply.sent_at || Date.now()).toLocaleString()} ${messageToReply.sender_address || 'Unknown Sender'} wrote: ---\n> ` +
                 (messageToReply.body_text || '').split('\n').join('\n> ')
  };
  openComposeModal(initialData);
};

const handleUseSuggestion = (suggestionText) => {
  // If compose modal is already open for a reply (i.e., composeInitialData is set for reply context),
  // append the suggestion to its body. Otherwise, open a new compose with the suggestion as the body.
  if (showComposeModal.value && composeInitialData.value && composeInitialData.value.quoted_body) {
    // Modal is already open for a reply, append suggestion to existing body
    composeInitialData.value = {
      ...composeInitialData.value, // Keep existing to, subject, etc.
      // Append to existing body_text if any, or to quoted_body
      body_text: (composeInitialData.value.body_text || composeInitialData.value.quoted_body) + '\n\n' + suggestionText,
    };
  } else {
    // Not currently in reply mode, or modal closed. Open new compose with suggestion.
    // If there's an active thread, maybe prefill "To" based on last sender of active thread?
    // For now, just the suggestion in the body.
    let to_recipients = [];
    let subject = '';
    if (threadStore.getActiveThreadDetails && threadStore.activeThreadMessages.length > 0) {
        const lastMessage = threadStore.activeThreadMessages[threadStore.activeThreadMessages.length - 1];
        if (lastMessage && lastMessage.sender_address && lastMessage.sender_address !== authStore.user?.email) { // Basic check not to reply to self
            to_recipients = [lastMessage.sender_address];
        }
        subject = `Re: ${threadStore.getActiveThreadDetails.subject || ''}`;
    }

    composeInitialData.value = {
      to_recipients: to_recipients,
      subject: subject,
      body_text: suggestionText,
      // No quoted_body for a fresh compose from suggestion, unless we decide otherwise
    };
  }
  showComposeModal.value = true; // Ensure modal is visible
};


onMounted(() => {
  if (authStore.isAuthenticated) {
    // Fetch threads for the initially active account (or null if none)
    // emailAccountsStore should have already tried to set an active account if one exists
    threadStore.fetchThreads(emailAccountsStore.activeAccountId);
  }
});

// Watch for changes in activeAccountId and re-fetch threads
watch(() => emailAccountsStore.activeAccountId, (newAccountId, oldAccountId) => {
  if (authStore.isAuthenticated) {
    console.log(`Active account changed from ${oldAccountId} to ${newAccountId}. Fetching threads.`);
    threadStore.fetchThreads(newAccountId);
  }
});

</script>

<style scoped>
.im-view-wrapper {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px); /* Full height minus nav */
}
.compose-new-button {
  margin: 10px;
  padding: 8px 15px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  align-self: flex-start; /* Position button to the left or as desired */
}
.compose-new-button:hover {
  background-color: #0056b3;
}
.im-view {
  display: flex;
  flex-grow: 1; /* Takes remaining height */
  overflow: hidden;
}
</style>
