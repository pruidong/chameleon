<!-- /src/components/HistoryGallery.vue -->
<template>
  <div v-if="history.length > 0" class="history-gallery">
    <h3 style="text-align: left;">历史记录</h3>
    <div class="history-grid">
      <div v-for="(item, index) in history" :key="index" class="history-item" @click="loadItem(item)">
        <img :alt="`History Image ${index}`" :src="item.image" class="history-image" />
        <div class="history-info">
          <p class="timestamp">{{ formatTimestamp(item.timestamp) }}</p>
          <p class="prompt">{{ truncatePrompt(item.prompt) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>

interface HistoryItem {
  timestamp: number;
  image: string;
  prompt: string;
  model: string;
}
interface Props {
  history?: HistoryItem[];
}
const props = withDefaults(defineProps<Props>(), {
  history: () => []
});

const emit = defineEmits<{
  (e: 'load-history', item: HistoryItem): void;
}>();

// 简单的日期格式化函数
const formatTimestamp = (timestamp: number): string => {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}`;
};

// 提示词截断
const truncatePrompt = (prompt: string): string => {
  return prompt.length > 20 ? prompt.substring(0, 20) + '...' : prompt;
};

const loadItem = (item: HistoryItem) => {
  emit('load-history', item);
};
</script>
<style scoped>
.history-gallery {
  margin-top: 30px;
  text-align: left;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.history-item {
  cursor: pointer;
  border: 1px solid #eee;
  border-radius: 6px;
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.1s ease;
  background-color: #fff;
}

.history-item:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  transform: translateY(-2px);
}

.history-image {
  width: 100%;
  height: 100px;
  object-fit: cover;
  display: block;
}

.history-info {
  padding: 6px;
}

.timestamp {
  font-size: 11px;
  color: #888;
  margin: 0 0 4px 0;
}

.prompt {
  font-size: 12px;
  color: #333;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 针对非常小的屏幕 (如旧手机) */
@media (max-width: 480px) {
  .history-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 10px;
  }

  .history-image {
    height: 90px;
  }

  .history-info {
    padding: 5px;
  }

  .timestamp {
    font-size: 10px;
  }

  .prompt {
    font-size: 11px;
  }
}
</style>