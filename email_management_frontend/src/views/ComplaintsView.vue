<template>
  <div class="complaints-view">
    <h2>Extracted Complaints & Suggestions Dashboard</h2>

    <div v-if="complaintsStore.isLoading && complaintsStore.complaints.length === 0" class="loading-indicator">
      Loading data...
    </div>
    <div v-else-if="complaintsStore.error" class="error-message">
      Error loading data: {{ complaintsStore.error }}
    </div>
    <div v-else-if="!complaintsStore.isLoading && complaintsStore.complaints.length === 0" class="no-data">
      No complaints or suggestions data found to display charts or table.
    </div>

    <div v-else>
      <!-- Charts Container -->
      <div class="charts-container">
        <div class="chart-wrapper" v-if="issueTypeChartDataReady">
          <h3>Complaints by Issue Type</h3>
          <Bar :data="issueTypeChartData" :options="chartOptions" style="height: 300px; width: 100%;" />
        </div>
        <div class="chart-wrapper" v-if="sentimentChartDataReady">
          <h3>Sentiment Distribution</h3>
          <Pie :data="sentimentChartData" :options="chartOptions" style="height: 300px; width: 100%;" />
        </div>
      </div>

      <!-- Existing Table Container -->
      <div class="complaints-table-container">
        <h3>Detailed Data</h3>
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
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue';
import { useComplaintsStore } from '@/stores/complaintsStore';
import { Bar, Pie } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement } from 'chart.js';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

const complaintsStore = useComplaintsStore();

const issueTypeChartData = computed(() => {
  if (!complaintsStore.complaints || complaintsStore.complaints.length === 0) {
    return { labels: [], datasets: [] }; // Return empty structure for chart component
  }
  const counts = complaintsStore.complaints.reduce((acc, complaint) => {
    const type = complaint.issue_type || 'Unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});
  return {
    labels: Object.keys(counts),
    datasets: [{
      label: 'Complaints by Issue Type',
      backgroundColor: ['#42A5F5', '#FFA726', '#66BB6A', '#EF5350', '#AB47BC', '#FFCA28', '#26A69A'], // Example colors
      data: Object.values(counts)
    }]
  };
});
const issueTypeChartDataReady = computed(() => issueTypeChartData.value.labels.length > 0);


const sentimentChartData = computed(() => {
  if (!complaintsStore.complaints || complaintsStore.complaints.length === 0) {
     return { labels: [], datasets: [] };
  }
  const counts = complaintsStore.complaints.reduce((acc, complaint) => {
    const sentiment = complaint.sentiment || 'Unknown';
    acc[sentiment] = (acc[sentiment] || 0) + 1;
    return acc;
  }, {});
  return {
    labels: Object.keys(counts),
    datasets: [{
      label: 'Sentiment Distribution',
      backgroundColor: ['#66BB6A', '#EF5350', '#FFCA28', '#BDBDBD'], // Positive, Negative, Neutral, Unknown
      data: Object.values(counts)
    }]
  };
});
const sentimentChartDataReady = computed(() => sentimentChartData.value.labels.length > 0);


const chartOptions = {
  responsive: true,
  maintainAspectRatio: false, // Important for fitting into styled wrappers
  plugins: {
    legend: {
      position: 'top',
    },
    title: { // Optional global title for charts, though often set per chart
      display: false, // Using h3 above charts instead
      text: 'Chart Title'
    }
  }
};

onMounted(() => {
  // Fetch data if not already loaded or if forced refresh is needed
  if (complaintsStore.complaints.length === 0) {
      complaintsStore.fetchComplaints();
  }
});
</script>

<style scoped>
.complaints-view {
  padding: 20px;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  background-color: #f9f9f9; /* Light background for the whole view */
  min-height: calc(100vh - 60px); /* Assuming 60px nav bar */
}
.complaints-view h2 {
    text-align: center;
    margin-bottom: 25px;
    color: #333;
}
.loading-indicator, .error-message, .no-data {
  text-align: center;
  margin-top: 30px;
  padding: 20px;
  color: #555;
  font-size: 1.1em;
}
.error-message {
  color: #D8000C; /* Error red */
  background-color: #FFD2D2; /* Light red background */
  border: 1px solid #D8000C;
  border-radius: 8px;
}
.no-data {
  background-color: #e9ecef;
  border: 1px solid #ced4da;
  border-radius: 8px;
}

.charts-container {
  display: flex;
  flex-wrap: wrap; /* Allow charts to wrap on smaller screens */
  gap: 20px; /* Space between charts */
  margin-bottom: 30px;
}
.chart-wrapper {
  flex: 1 1 400px; /* Flex grow, shrink, and basis (min-width before wrapping) */
  min-width: 300px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.chart-wrapper h3 {
  text-align: center;
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.2em;
  color: #444;
}

.complaints-table-container {
  margin-top: 20px;
  overflow-x: auto;
  background-color: #fff;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.complaints-table-container h3 {
    margin-top:0;
    margin-bottom: 15px;
    font-size: 1.2em;
    color: #444;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}
th, td {
  border: 1px solid #ddd;
  padding: 10px 12px; /* Slightly more padding */
  text-align: left;
  vertical-align: top;
}
th {
  background-color: #f0f2f5; /* Lighter, more modern header */
  font-weight: 600; /* Slightly bolder */
  color: #333;
}
tr:nth-child(even) {
  background-color: #f9fafc;
}
tr:hover {
  background-color: #f1f5f9; /* Subtle hover */
}
.summary-cell {
  min-width: 250px;
  white-space: pre-wrap;
  max-height: 100px; /* Limit height and make scrollable if needed */
  overflow-y: auto;
}
</style>
