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
import { ref, computed, onMounted } from 'vue';
import ConversationList from '@/components/im_ui/ConversationList.vue';
import ConversationPanel from '@/components/im_ui/ConversationPanel.vue';
import ComposeModal from '@/components/ComposeModal.vue'; // Import ComposeModal
import { useThreadStore } from '@/stores/threadStore';
import { useAuthStore } from '@/stores/auth';

const threadStore = useThreadStore();
const authStore = useAuthStore();

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
    quoted_body: `\n\n\n--- On ${new Date(messageToReply.sent_at).toLocaleString()} ${messageToReply.sender_address} wrote: ---\n> ` +
                 (messageToReply.body_text || '').split('\n').join('\n> ')
  };
  openComposeModal(initialData);
};

onMounted(() => {
  if (authStore.isAuthenticated) {
    threadStore.fetchThreads();
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
