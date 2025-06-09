<template>
  <div class="conversation-panel">
    <div v-if="conversationInfo" class="panel-header">
      <h3>{{ conversationInfo.subject || 'No Subject' }}</h3>
    </div>
    <div v-else class="panel-header">
      <h3>Select a conversation</h3>
    </div>

    <div class="messages-area" ref="messagesAreaRef">
      <div v-if="loading" class="loading-indicator">Loading messages...</div>
      <div v-else-if="error && !loading" class="error-message">{{ error }}</div> <!-- Only show message loading error if not also loading suggestions -->
      <div v-else-if="conversationInfo && messages && messages.length">
        <MessageBubble
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
        />
      </div>
      <p v-else-if="conversationInfo && (!messages || !messages.length) && !loading" class="no-messages-notice">
        No messages in this conversation yet.
      </p>
      <p v-else-if="!conversationInfo && !loading" class="no-messages-notice">
        Please select a conversation to see messages.
      </p>
    </div>

    <!-- AI Suggestions Area -->
    <div class="ai-suggestions-section" v-if="conversationInfo">
       <button
        @click="triggerFetchSuggestions"
        :disabled="aiFeaturesStore.isLoadingSuggestions || !targetMessageForSuggestions"
        class="fetch-suggestions-button">
        {{ aiFeaturesStore.isLoadingSuggestions ? 'Loading AI Suggestions...' : 'Get AI Suggestions' }}
      </button>
      <div v-if="aiFeaturesStore.isLoadingSuggestions" class="loading-indicator-small">Fetching suggestions...</div>
      <div v-if="aiFeaturesStore.suggestionError && !aiFeaturesStore.isLoadingSuggestions" class="error-message suggestions-error">
        AI Error: {{ aiFeaturesStore.suggestionError }}
      </div>
      <div class="suggestions-list" v-if="aiFeaturesStore.suggestions.length > 0 && !aiFeaturesStore.isLoadingSuggestions">
        <strong>Suggestions:</strong>
        <button
          v-for="(suggestion, index) in aiFeaturesStore.suggestions"
          :key="index"
          @click="emitUseSuggestion(suggestion)"
          class="suggestion-button">
          {{ suggestion }}
        </button>
      </div>
       <p v-if="!aiFeaturesStore.isLoadingSuggestions && aiFeaturesStore.suggestions.length === 0 && targetMessageForSuggestions && !aiFeaturesStore.suggestionError && suggestionsFetchedOnce" class="no-suggestions-notice-small">
        No AI suggestions available for this message.
      </p>
    </div>

    <div class="reply-area" v-if="conversationInfo">
      <textarea placeholder="Type your reply..." v-model="replyText" @keyup.enter.prevent="handleManualReply"></textarea>
      <button @click="handleManualReply" :disabled="!conversationInfo">Reply / New</button> <!-- Changed button text -->
    </div>

  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue';
import MessageBubble from './MessageBubble.vue';
import { useAiFeaturesStore } from '@/stores/aiFeaturesStore';

const props = defineProps({
  messages: Array,
  conversationInfo: Object,
  loading: Boolean, // Loading messages state
  error: String,   // Error loading messages
});

const emit = defineEmits(['replyToMessage', 'useSuggestion']);

const aiFeaturesStore = useAiFeaturesStore();
const messagesAreaRef = ref(null);
const replyText = ref(''); // For the manual reply box text (currently not directly used for sending)
const suggestionsFetchedOnce = ref(false); // To track if "Get AI Suggestions" has been clicked

const targetMessageForSuggestions = computed(() => {
  if (props.messages && props.messages.length > 0) {
    return props.messages[props.messages.length - 1]; // Target last message for suggestions
  }
  return null;
});

watch(() => [props.messages, props.conversationInfo], async () => {
  await nextTick();
  const area = messagesAreaRef.value;
  if (area) {
    area.scrollTop = area.scrollHeight;
  }
}, { deep: true, immediate: true });

watch(() => props.conversationInfo, (newConversationInfo) => {
    aiFeaturesStore.clearSuggestions();
    suggestionsFetchedOnce.value = false; // Reset for new conversation
    // replyText.value = ''; // Clear reply box for new conversation
}, { immediate: true });

const handleManualReply = () => {
  const messageToReplyTo = targetMessageForSuggestions.value ||
                           (props.conversationInfo ? {
                               subject: props.conversationInfo.subject,
                               sender_address: '', // Will be overridden by compose modal logic if needed
                               body_text: replyText.value, // Pass current text field value
                               sent_at: new Date().toISOString()
                            } : null);
  if (messageToReplyTo) {
    // If replyText has content, use it for the body, otherwise IMView will quote.
    // This is slightly different from previous; IMView's handleReplyToMessage will need to check.
    // For now, let's just pass the message object for context. IMView decides prefill.
    // IMView should get the replyText from this component or this component should pass it in emit.
    // Let's simplify: IMView's `handleReplyToMessage` will create the quote.
    // The `replyText` here is more for a direct send from this panel (not implemented).
    emit('replyToMessage', messageToReplyTo);
  }
};

const triggerFetchSuggestions = () => {
  if (targetMessageForSuggestions.value && targetMessageForSuggestions.value.id) {
    suggestionsFetchedOnce.value = true; // Mark that we've tried to fetch
    aiFeaturesStore.fetchReplySuggestions(targetMessageForSuggestions.value.id);
  } else {
    aiFeaturesStore.suggestionError = "No message selected or available to get suggestions for.";
  }
};

const emitUseSuggestion = (suggestionText) => {
  emit('useSuggestion', suggestionText);
  // Suggestions are not cleared here; IMView will open compose modal, which might clear them later.
};

</script>

<style scoped>
.conversation-panel { flex-grow: 1; display: flex; flex-direction: column; height: 100%; background-color: #fff; }
.panel-header { padding: 10px 15px; border-bottom: 1px solid #ccc; background-color: #f5f5f5; min-height: 40px; box-sizing: border-box; }
.panel-header h3 { margin: 0; font-size: 1.1em; line-height: 1.3; }
.messages-area { flex-grow: 1; overflow-y: auto; padding: 15px; }
.loading-indicator, .error-message, .no-messages-notice { text-align: center; color: #777; margin-top: 20px; padding: 10px; }
.loading-indicator-small { text-align:center; font-size:0.85em; color:#555; padding:5px;}
.no-suggestions-notice-small { text-align:center; font-size:0.8em; color:#6c757d; padding:5px 0;}
.error-message { color: red; }
.reply-area { padding: 10px 15px; border-top: 1px solid #ccc; display: flex; background-color: #f9f9f9; }
.reply-area textarea { flex-grow: 1; margin-right: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 5px; resize: none; min-height: 40px; max-height: 100px; box-sizing: border-box; }
.reply-area button { padding: 0 15px; border: none; background-color: #007bff; color: white; border-radius: 5px; cursor: pointer; }
.reply-area button:disabled { background-color: #aaa; cursor: not-allowed; }

.ai-suggestions-section { padding: 10px 15px; border-top: 1px solid #e0e0e0; background-color: #f9f9f9; }
.fetch-suggestions-button { padding: 6px 12px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 8px; font-size: 0.9em; }
.fetch-suggestions-button:disabled { background-color: #aaa; cursor: not-allowed; }
.fetch-suggestions-button:hover:not(:disabled) { background-color: #5a6268; }
.suggestions-list { margin-top: 8px; }
.suggestions-list strong { font-size: 0.9em; display: block; margin-bottom: 4px; color: #555; }
.suggestion-button { display: block; width: 100%; text-align: left; margin-bottom: 5px; padding: 8px 10px; background-color: #e9ecef; color: #212529; border: 1px solid #ced4da; border-radius: 4px; cursor: pointer; font-size: 0.85em; }
.suggestion-button:hover { background-color: #dde2e7; border-color: #b6c0c9; }
.suggestions-error { font-size: 0.9em; margin-top: 5px; padding: 5px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px; }
</style>
