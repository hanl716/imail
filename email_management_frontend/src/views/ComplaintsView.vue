<template>
  <div class="complaints-view">
    <h2>Extracted Complaints & Suggestions</h2>

    <div v-if="complaintsStore.isLoading" class="loading-indicator">
      Loading data...
    </div>
    <div v-else-if="complaintsStore.error" class="error-message">
      Error loading data: {{ complaintsStore.error }}
    </div>
    <div v-else-if="complaintsStore.complaints.length === 0" class="no-data">
      No complaints or suggestions data found.
    </div>
    <div v-else class="complaints-table-container">
      <table>
        <thead>
          <tr>
            <th>Extracted At</th>
            <th>Original Subject</th>
            <th>Submitter Email</th>
            <th>Submitter Name</th>
            <th>Issue Type</th>
            <th>Category Detail</th>
            <th>Product/Service</th>
            <th>Summary</th>
            <th>Sentiment</th>
            <th>Original Email ID</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in complaintsStore.complaints" :key="item.id">
            <td>{{ new Date(item.extracted_at).toLocaleString() }}</td>
            <td>{{ item.email_subject || 'N/A' }}</td>
            <td>{{ item.submitter_email }}</td>
            <td>{{ item.submitter_name || 'N/A' }}</td>
            <td>{{ item.issue_type }}</td>
            <td>{{ item.category_detail || 'N/A' }}</td>
            <td>{{ item.product_service || 'N/A' }}</td>
            <td class="summary-cell">{{ item.summary }}</td>
            <td>{{ item.sentiment || 'N/A' }}</td>
            <td>{{ item.email_message_id }}</td>
            <!-- Optionally, add a link to view the original email message -->
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useComplaintsStore } from '@/stores/complaintsStore';

const complaintsStore = useComplaintsStore();

onMounted(() => {
  complaintsStore.fetchComplaints();
});
</script>

<style scoped>
.complaints-view {
  padding: 20px;
  font-family: Avenir, Helvetica, Arial, sans-serif;
}
.loading-indicator, .error-message, .no-data {
  text-align: center;
  margin-top: 20px;
  padding: 10px;
  color: #555;
}
.error-message {
  color: red;
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 4px;
}
.no-data {
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 4px;
}
.complaints-table-container {
  margin-top: 20px;
  overflow-x: auto; /* Allow horizontal scrolling for table on small screens */
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}
th, td {
  border: 1px solid #ddd;
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}
th {
  background-color: #f2f2f2;
  font-weight: bold;
}
tr:nth-child(even) {
  background-color: #f9f9f9;
}
tr:hover {
  background-color: #f1f1f1;
}
.summary-cell {
  min-width: 250px; /* Ensure summary has enough space */
  white-space: pre-wrap; /* Respect newlines in summary */
}
</style>
