<template>
  <div class="conversation-list">
    <h3>Conversations</h3>
    <div v-if="loading" class="loading-indicator">Loading threads...</div>
    <div v-if="error" class="error-message">{{ error }}</div>
    <ConversationListItem
      v-if="!loading && !error && conversations && conversations.length"
      v-for="convo in conversations"
      :key="convo.id"
      :conversation="convo" <!-- Prop name matches, data structure will be EmailThreadOutput -->
      @selectConversation="$emit('conversationSelected', convo.id)"
    />
    <p v-if="!loading && !error && (!conversations || !conversations.length)">No conversations found.</p>
  </div>
</template>

<script setup>
import ConversationListItem from './ConversationListItem.vue';

defineProps({
  conversations: Array, // Will be Array of EmailThreadOutput
  loading: Boolean,
  error: String, // Or Object if error has more structure
});
defineEmits(['conversationSelected']);
</script>

<style scoped>
.conversation-list {
  width: 300px;
  min-width: 250px;
  border-right: 1px solid #ccc;
  height: 100%;
  overflow-y: auto;
  background-color: #fdfdfd;
}
.conversation-list h3 {
  padding: 10px 15px;
  margin: 0;
  border-bottom: 1px solid #eee;
  background-color: #f5f5f5;
  font-size: 1.1em;
  position: sticky; /* Keep header visible */
  top: 0;
  z-index: 1;
}
.loading-indicator, .error-message, .conversation-list p {
  padding: 15px;
  text-align: center;
  color: #777;
}
.error-message {
  color: red;
}
</style>
