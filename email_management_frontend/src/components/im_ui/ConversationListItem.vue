<template>
  <div class="conversation-list-item" @click="$emit('selectConversation', conversation.id)">
    <h4>{{ conversation.subject || 'No Subject' }}</h4>
    <!-- Sender info might be part of snippet or a participant list in future -->
    <!-- For now, focusing on snippet and timestamp -->
    <p class="snippet">{{ conversation.snippet || 'No snippet available.' }}</p>
    <small v-if="conversation.last_message_at">{{ new Date(conversation.last_message_at).toLocaleString() }}</small>
    <small v-else>No date</small>
    <!-- unreadCount would need to be added to EmailThreadOutput schema -->
    <!-- <span v-if="conversation.unreadCount > 0" class="unread-count">{{ conversation.unreadCount }}</span> -->
  </div>
</template>

<script setup>
defineProps({
  // Expecting conversation to be of type EmailThreadOutput from the backend
  conversation: Object
});
defineEmits(['selectConversation']);
</script>

<style scoped>
.conversation-list-item {
  padding: 10px 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.conversation-list-item:hover {
  background-color: #f0f0f0;
}
.conversation-list-item.active { /* Style for active selection if needed */
  background-color: #e0eafc;
}
h4 {
  margin: 0 0 5px 0;
  font-size: 1em;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.snippet {
  margin: 0 0 8px 0;
  font-size: 0.85em;
  color: #555;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* Limit to 2 lines */
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
small {
  font-size: 0.8em;
  color: #777;
}
/* .unread-count { background-color: red; color: white; border-radius: 50%; padding: 2px 6px; font-size: 0.8em; margin-left: 5px; display: inline-block; vertical-align: middle; } */
</style>
