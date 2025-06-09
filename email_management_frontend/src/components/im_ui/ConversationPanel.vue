<template>
  <div class="conversation-panel">
    <div v-if="conversationInfo" class="panel-header">
      <h3>{{ conversationInfo.subject || 'No Subject' }}</h3>
      <!-- Participants info can be added here if available in conversationInfo -->
    </div>
    <div v-else class="panel-header">
      <h3>Select a conversation</h3>
    </div>

    <div class="messages-area" ref="messagesAreaRef">
      <div v-if="loading" class="loading-indicator">Loading messages...</div>
      <div v-else-if="error" class="error-message">{{ error }}</div>
      <div v-else-if="conversationInfo && messages && messages.length">
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :message="msg" <!-- Prop name matches, data structure will be EmailMessageOutput -->
        />
      </div>
      <p v-else-if="conversationInfo && (!messages || !messages.length)" class="no-messages-notice">
        No messages in this conversation yet.
      </p>
      <p v-else class="no-messages-notice">
        Please select a conversation to see messages.
      </p>
    </div>

    <div class="reply-area" v-if="conversationInfo">
      <textarea placeholder="Type your reply..." v-model="replyText" @keyup.enter.prevent="sendReply"></textarea>
      <button @click="sendReply" :disabled="!replyText.trim()">Send</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import MessageBubble from './MessageBubble.vue';

const props = defineProps({
  messages: Array, // Will be Array of EmailMessageOutput
  conversationInfo: Object, // Will be EmailThreadOutput or null
  loading: Boolean,
  error: String, // Or Object
});

const emit = defineEmits(['replyToMessage']); // Define emit

const messagesAreaRef = ref(null);
const replyText = ref('');

// Scroll to bottom when new messages are added or conversation changes
watch(() => [props.messages, props.conversationInfo], async () => {
  // Ensure messages are rendered before trying to scroll
  await nextTick();
  const area = messagesAreaRef.value;
  if (area) {
    area.scrollTop = area.scrollHeight;
  }
}, { deep: true, immediate: true });


const sendReply = () => {
  if (!replyText.value.trim()) return;
  // Placeholder for sending reply - this would actually send the message
  // For now, we are using this area to trigger a "reply" action that pre-fills the compose modal
  if (props.messages && props.messages.length > 0) {
    // As a placeholder, "reply" to the first message in the current view.
    // A real UI would have reply buttons on each message bubble.
    emit('replyToMessage', props.messages[0]);
  } else if (props.conversationInfo) {
    // If no messages, but we have conversation info, "reply" to the conversation (e.g. prefill To, Subject)
    emit('replyToMessage', {
        sender_address: '', // No specific sender if it's a new reply to whole thread
        subject: props.conversationInfo.subject,
        body_text: '',
        sent_at: new Date().toISOString() // Placeholder
    });
  }
  // The replyText itself is not used to prefill the compose modal via this button for now.
  // The IMView's handleReplyToMessage will construct the quoted body etc.
  // console.log("Reply button clicked for conversation:", props.conversationInfo?.id);
  // replyText.value = ''; // Keep text if user was typing something for a direct send (not implemented yet)
};

</script>

<style scoped>
.conversation-panel {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
}
.panel-header {
  padding: 10px 15px;
  border-bottom: 1px solid #ccc;
  background-color: #f5f5f5;
  min-height: 40px; /* Ensure header has some height */
  box-sizing: border-box;
}
.panel-header h3 {
  margin: 0;
  font-size: 1.1em;
  line-height: 1.3; /* Adjust for vertical centering if needed */
}
.messages-area {
  flex-grow: 1;
  overflow-y: auto;
  padding: 15px;
}
.loading-indicator, .error-message, .no-messages-notice {
  text-align: center;
  color: #777;
  margin-top: 20px;
  padding: 10px;
}
.error-message {
  color: red;
}
.reply-area {
  padding: 10px 15px;
  border-top: 1px solid #ccc;
  display: flex;
  background-color: #f9f9f9;
}
.reply-area textarea {
  flex-grow: 1;
  margin-right: 10px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 5px;
  resize: none;
  min-height: 40px;
  max-height: 100px;
  box-sizing: border-box;
}
.reply-area button {
  padding: 0 15px;
  border: none;
  background-color: #007bff;
  color: white;
  border-radius: 5px;
  cursor: pointer;
}
.reply-area button:disabled {
  background-color: #aaa;
  cursor: not-allowed;
}
</style>
