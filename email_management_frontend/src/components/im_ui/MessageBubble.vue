<template>
  <div class="message-bubble-wrapper">
    <div class="message-bubble" :class="{ 'own-message': isOwnMessage }">
      <div class="message-content">
        <div v-if="message.body_html" v-html="sanitizeHtml(message.body_html)" class="html-content"></div>
        <pre v-else-if="message.body_text" class="text-content">{{ message.body_text }}</pre>
        <p v-else class="text-content-empty"><em>No message content.</em></p>
      </div>
      <div class="message-meta" v-if="message.category">
        <span class="category-badge">{{ message.category }}</span>
      </div>
      <div class="attachments-list" v-if="message.attachments && message.attachments.length">
        <strong>Attachments:</strong>
        <ul>
          <li v-for="att in message.attachments" :key="att.id">
            <a :href="getAttachmentDownloadUrl(att.id)" target="_blank" rel="noopener noreferrer" class="attachment-link">
              📎 {{ att.filename || 'untitled' }} ({{ formatBytes(att.size_bytes) }})
            </a>
          </li>
        </ul>
      </div>
      <small class="message-timestamp">
        {{ message.sender_address || 'Unknown Sender' }} -
        {{ message.sent_at ? new Date(message.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'No time' }}
      </small>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import DOMPurify from 'dompurify'; // Import DOMPurify

const props = defineProps({
  message: Object
});

const authStore = useAuthStore();

function sanitizeHtml(htmlString) {
  // Add a hook to make all links open in a new tab
  DOMPurify.addHook('afterSanitizeAttributes', function (node) {
    if ('target' in node) {
      node.setAttribute('target', '_blank');
      node.setAttribute('rel', 'noopener noreferrer');
    }
    // Example: Force https for image sources if desired
    // if (node.tagName === 'IMG' && node.hasAttribute('src')) {
    //   let src = node.getAttribute('src');
    //   if (src.startsWith('http:')) {
    //     node.setAttribute('src', src.replace('http:', 'https:'));
    //   }
    // }
  });
  // Configure DOMPurify: Allow common HTML tags, forbid scripts, etc.
  // USE_PROFILES: { html: true } is a good default for general HTML content.
  // You can customize further if needed, e.g. FORBID_TAGS, ADD_ATTR.
  return DOMPurify.sanitize(htmlString, { USE_PROFILES: { html: true } });
}

const getAttachmentDownloadUrl = (attachmentId) => {
  // Base URL for API. If your Nginx proxy or dev server setup changes, adjust this.
  // Assumes API is served from the same domain or correctly proxied under /api.
  // The backend route is /api/v1/attachments/{attachment_id}/download
  return `/api/v1/attachments/${attachmentId}/download`;
};

const formatBytes = (bytes, decimals = 1) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const isOwnMessage = computed(() => {
  if (!props.message || !props.message.sender_address) {
    return false;
  }
  // Basic check against the logged-in user's primary email.
  // A more robust solution would check against all linked email accounts of the user.
  if (authStore.user && authStore.user.email) {
    // Normalize or be careful with email comparisons (case sensitivity, etc.)
    return props.message.sender_address.toLowerCase() === authStore.user.email.toLowerCase();
  }
  // Further check: iterate through emailAccountsStore.accounts if available
  // return emailAccountsStore.accounts.some(acc => acc.email_address.toLowerCase() === props.message.sender_address.toLowerCase());
  return false;
});

// If using v-html for body_html, a sanitizer function would be needed here.
// For example, using DOMPurify:
// import DOMPurify from 'dompurify';
// const sanitizedHtml = computed(() => { ... }) // Not needed if sanitizeHtml is a method call in template

</script>

<style scoped>
.message-bubble-wrapper {
  overflow: auto;
  margin-bottom: 10px;
}
.message-bubble {
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 70%;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  word-wrap: break-word;
}
.message-bubble:not(.own-message) {
  background-color: #f0f0f0; /* Lighter grey for received messages */
  color: #333;
  float: left;
  border-bottom-left-radius: 4px;
}
.message-bubble.own-message {
  background-color: #007bff; /* Blue for sent messages */
  color: white;
  float: right;
  border-bottom-right-radius: 4px;
}
.message-content p {
  margin: 0 0 8px 0; /* Space between text and timestamp/attachments */
  white-space: pre-wrap;
}
.html-content {
  /* Basic styling for HTML content to blend in */
  line-height: 1.5;
}
/* Deeper styling for v-html content */
.html-content ::v-deep(p) { margin: 0 0 0.5em 0; }
.html-content ::v-deep(a) { color: var(--link-color, #007bff); text-decoration: underline; }
.html-content ::v-deep(img) { max-width: 100%; height: auto; margin: 0.5em 0; border-radius: 4px; }
.html-content ::v-deep(ul), .html-content ::v-deep(ol) { padding-left: 20px; margin-bottom: 0.5em; }
.html-content ::v-deep(blockquote) {
  margin: 0.5em 0 0.5em 10px;
  padding: 5px 10px;
  border-left: 3px solid #ccc;
  background-color: #f8f9fa; /* Slightly different background for blockquotes */
  color: #555;
}
.text-content-empty {
    color: #888;
    font-style: italic;
}

.message-timestamp {
  font-size: 0.75em;
  color: #666;
  margin-top: 5px;
  display: block;
  text-align: right; /* Timestamp usually aligned to the right of the bubble content */
}
.message-meta {
  text-align: right;
  margin-top: 4px;
}
.category-badge {
  background-color: #6c757d; /* Default grey, can be customized */
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7em;
  text-transform: uppercase;
}
.own-message .message-timestamp, .own-message .category-badge {
  color: #e0e0e0; /* Lighter color for timestamp on dark own message bubble */
}
.attachments-list {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0,0,0,0.05); /* Subtle separator */
}
.own-message .attachments-list {
  border-top: 1px solid rgba(255,255,255,0.2);
}
.attachments-list strong {
  font-size: 0.8em;
  display: block;
  margin-bottom: 4px;
}
.attachments-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.attachments-list li {
  font-size: 0.8em;
  padding: 2px 0;
}
.attachment-link {
  color: #007bff;
  text-decoration: none;
}
.attachment-link:hover {
  text-decoration: underline;
}
</style>
