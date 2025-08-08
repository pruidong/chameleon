<!-- src/components/ImageUploader.vue -->
<template>
  <div>
    <!-- 上传区域 -->
    <div v-if="!previewImage">
      <van-uploader
        :after-read="afterRead"
        :disabled="disabled"
        :max-count="1"
        :max-size="5 * 1024 * 1024"
        accept="image/*"
        reupload
        @oversize="onOversize"
      >
        <!-- 自定义上传触发元素 -->
        <div :class="{ 'is-dragging': isDragging }" class="upload-area">
          <van-icon name="photograph" size="32" />
          <div class="upload-text">
            <span v-if="disabled">请先登录</span>
            <span v-else>点击上传图片，或将图片拖拽到此处</span>
            <div class="upload-hint">(最大 5MB)</div>
          </div>
        </div>
      </van-uploader>
    </div>

    <!-- 预览区域 -->
    <div v-else class="preview-container">
      <img :src="previewImage" alt="Preview" class="preview-image" />
      <!-- 关闭按钮 -->
      <van-icon
        class="close-button"
        name="cross"
        @click="clearPreview"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { Icon as VanIcon, showNotify } from 'vant'; // 导入 VanIcon 组件

interface Props {
  disabled?: boolean;
}

withDefaults(defineProps<Props>(), {
  disabled: false
});

const emit = defineEmits<{
  (e: 'image-uploaded', file: File): void
  (e: 'image-cleared'): void
}>();

const previewImage = ref<string>('');
const isDragging = ref<boolean>(false);

// 清除预览
const clearPreview = () => {
  previewImage.value = '';
  emit('image-cleared');
};

// 实际并未执行图片上传
const afterRead = (file: any) => {
  isDragging.value = false;
  previewImage.value = file.content;
  emit('image-uploaded', file.file);
  // showNotify({ type: 'success', message: '图片上传成功' });
};

// 大小限制
const onOversize = () => {
  isDragging.value = false;
  showNotify({ type: 'danger', message: '文件大小超过5MB限制' });
};
</script>

<style scoped>
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 2px dashed #e0e0e0;
  border-radius: 6px;
  background-color: #fafafa;
  cursor: pointer;
  transition: all 0.2s ease;
}

.upload-area:hover,
.upload-area.is-dragging {
  border-color: #1989fa;
  background-color: #ecf5ff;
}

.upload-text {
  margin-top: 8px;
  font-size: 14px;
  color: #666;
  text-align: center;
}

.upload-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.preview-container {
  position: relative;
  display: inline-block;
  margin-top: 10px;
}

.preview-image {
  max-width: 100%;
  height: auto;
  max-height: 200px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  display: block;
}

.close-button {
  position: absolute;
  top: -8px;
  right: -8px;
  background-color: rgba(0, 0, 0, 0.5);
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
  z-index: 1;
}

.close-button:hover {
  background-color: rgba(0, 0, 0, 0.7);
}


.upload-area :deep(.van-icon) {
  color: #c8c9cc;
}
</style>