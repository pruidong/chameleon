<!-- src/components/PromptEditor.vue -->
<template>
  <div class="prompt-editor">
    <van-field
      v-model="internalPrompt"
      :disabled="disabled"
      autosize
      label="提示词"
      label-align="top"
      maxlength="200"
      placeholder="请输入提示词（输入提示词后按钮，按钮自动可用）"
      required
      rows="2"
      type="textarea"
    />
    <div style="margin: 10px 0; text-align: center;">
      <van-button
        :disabled="disabled || internalPrompt.length === 0"
        :loading="isProcessingFlag"
        hairline
        loading-text="翻译中，请稍候.."
        plain
        size="small"
        type="primary"
        @click="translatePrompt"
      >
        翻译提示词
      </van-button>
      <van-button
        :disabled="disabled || internalPrompt.length === 0"
        hairline
        plain
        size="small"
        style="margin-left: 10px;"
        type="success"
        @click="restoreOriginal"
      >
        还原提示词
      </van-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';

// 定义 props
interface Props {
  prompt?: string;
  disabled?: boolean; // 添加 disabled prop
  isProcessingFlag?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  prompt: '',
  disabled: false // 默认不禁用
});

const emit = defineEmits<{
  (e: 'update:prompt', value: string): void;
  (e: 'translate', prompt: string): void;
}>();

const internalPrompt = ref<string>(props.prompt);
const originalPrompt = ref<string>('');

watch(() => props.prompt, (newVal) => {
  internalPrompt.value = newVal;
});

watch(internalPrompt, (newVal) => {
  emit('update:prompt', newVal);
});

const translatePrompt = () => {
  originalPrompt.value = internalPrompt.value;
  emit('translate', internalPrompt.value);
};

const restoreOriginal = () => {
  internalPrompt.value = originalPrompt.value;
};
</script>

<style scoped>
.prompt-editor {
  border-top: 1px dashed #ccc;
  border-bottom: 1px dashed #ccc;
}
</style>