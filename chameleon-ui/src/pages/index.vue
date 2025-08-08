<!-- src/pages/index.vue -->
<template>
  <div class="app-container">
    <van-nav-bar class="top-nav-bar">
      <!-- 左侧 Logo -->
      <template #left>
        <van-image
          :src="logoPath"
          alt="App Logo"
          class="nav-logo"
          fit="contain"
          round
        />
      </template>

      <!-- 右侧按钮 -->
      <template #right>
        <div v-if="!isLoggedIn" class="nav-right">
          <!-- 未登录：显示登录按钮 -->
          <van-button class="nav-button" plain size="small" type="primary" @click="initiateGithubLogin">
            Github登录
          </van-button>
        </div>
        <div v-else class="nav-right">
          <!-- 已登录：显示用户名和退出按钮 -->
          <span class="username"><van-icon color="#000" name="manager-o" />&nbsp;{{ displayedUsername }}</span>
          <van-button class="nav-button" plain size="small" type="danger" @click="handleLogout">
            退出
          </van-button>
        </div>
      </template>
    </van-nav-bar>

    <div class="main-content">
      <image-uploader
        :disabled="!isLoggedIn"
        style="margin-bottom: 16px;"
        @image-uploaded="onImageUploaded"
        @image-cleared="onImageClear"
      ></image-uploader>

      <!-- 免责声明 -->
      <div class="disclaimer">
        系统不会永久保存您的图片，上传图片仅保留1小时，请及时下载处理结果。
      </div>

      <!-- 提示词编辑 -->
      <prompt-editor
        v-model:prompt="userPrompt"
        :disabled="!isLoggedIn"
        :is-processing-flag="isTransProcessing"
        style="margin-bottom: 16px;"
        @translate="onTranslatePrompt"
      ></prompt-editor>
      <div class="disclaimer">服务使用免费接口，处理速度较慢，感谢您的理解！
      </div>

      <!-- 开始处理按钮 -->
      <van-button
        :disabled="!isLoggedIn || !isProcessable"
        :loading="isProcessing"
        block
        loading-text="处理时间较长，请耐心等待..."
        style="margin-bottom: 24px;"
        type="primary"
        @click="processImage"
      >
        开始处理
      </van-button>

      <!-- 处理结果区域 -->
      <div v-if="processedImage" class="result-section">
        <h3>处理结果:</h3>
        <div class="image-container">
          <img :src="processedImage" alt="Processed Image" class="result-image" />
        </div>
        <van-button size="small" @click="downloadImage">下载图片</van-button>
      </div>

      <!-- 历史记录 -->
      <history-gallery :history="userHistory" @load-history="loadHistoryItem"></history-gallery>
      <div class="bottom-info" @click="showGzh">欢迎关注公众号（锤子代码），交流学习AIGC</div>
    </div>
  </div>
</template>

<script lang="ts" setup>

import { computed, onMounted, ref, Ref } from 'vue';
import { showImagePreview, showNotify } from 'vant';
import ImageUploader from '~/components/ImageUploader.vue';
import PromptEditor from '~/components/PromptEditor.vue';
import HistoryGallery from '~/components/HistoryGallery.vue';
import { encryptData, getPublicKey } from '~/utils/crypto';
import CryptoJS from 'crypto-js';
import { alovaInstance } from '~/api/api'; // 类型定义

// 类型定义

// 历史记录
interface HistoryItem {
  timestamp: number;
  image: string;
  prompt: string;
}

// 图片处理返回
interface ProcessImage {
  result: string;
  error?: string;
}

// 提示词翻译
interface TranslatePrompt {
  en_prompt: string;
  error?: string;
}

// Gihub登录
interface GithubLogin {
  auth_url: string;
  error: string;
}

// --- 响应式状态 ---
const isLoggedIn: Ref<boolean> = ref(false);
const sessionId: Ref<string> = ref('');
const userPrompt: Ref<string> = ref('');
const isProcessing: Ref<boolean> = ref(false);
const isTransProcessing: Ref<boolean> = ref(false);
const processedImage: Ref<string> = ref('');
const uploadImage = ref<File>();
const userHistory: Ref<HistoryItem[]> = ref([]);
const isProcessable = computed(() => {
  return userPrompt.value.trim().length > 0;
});

// Github登录用户名
const githubUsername = ref<string | null>(null);
// 显示用户名
const displayedUsername = computed(() => githubUsername.value || 'User');
// LOGO文件路径
const logoPath = '/chameleon/logo.png';

// 退出登录
const handleLogout = async () => {
  try {
    const token = localStorage.getItem('app_session_token');
    if (token) {
      localStorage.removeItem('app_session_token');
      localStorage.removeItem('github_user_id'); // 如果存储了用户ID

      isLoggedIn.value = false;
      sessionId.value = ''; // 清除内存中的 token 引用
      userHistory.value = []; // 清空历史记录
      processedImage.value = ''; // 清空处理结果
      userPrompt.value = ''; // 清空提示词
      showNotify({ type: 'success', message: '您已退出登录' });
      window.location.reload();
    }
  } catch (err) {
    console.error('退出登录失败:', err);
    isLoggedIn.value = false;
    sessionId.value = '';
    localStorage.removeItem('app_session_token');
    localStorage.removeItem('github_user_id');
    showNotify({ type: 'warning', message: '您已退出登录' });
  }
};


// GitHub 登录
const initiateGithubLogin = async (): Promise<void> => {
  try {
    const response = await alovaInstance.Get('/api/auth/github') as GithubLogin;
    const { error, auth_url } = response;
    if (error) {
      showNotify({ type: 'danger', message: error });
      return;
    }
    window.location.href = auth_url;
  } catch (err: any) {
    showNotify({ type: 'danger', message: err.message || '获取Github授权URL发生异常' });
  }
};

const onImageClear = (): void => {
  uploadImage.value = undefined;
};

// 图片上传,仅记录,不触发实际上传.
const onImageUploaded = (file: File): void => {
  uploadImage.value = file;
  console.log('Image uploaded:', file);
};

// 提示词翻译
const onTranslatePrompt = async (prompt: string): Promise<void> => {
  try {
    isTransProcessing.value = true;
    const encryptedPrompt = encryptData(prompt, getPublicKey());
    if (!encryptedPrompt) {
      throw new Error('加密失败');
    }

    const response = await alovaInstance.Post('/api/translate', { prompt: encryptedPrompt }, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionId.value}`
      }
    }) as TranslatePrompt;

    const { error, en_prompt } = response;
    if (error) {
      showNotify({ type: 'danger', message: error });
      return;
    }

    if (en_prompt) {
      userPrompt.value = en_prompt;
    }
    showNotify({ type: 'success', message: '翻译成功' });
  } catch (err: any) {
    showNotify({ type: 'danger', message: err.message || '翻译失败' });
  } finally {
    isTransProcessing.value = false;
  }
};

// 显示公众号二维码
const showGzh = () => {
  showImagePreview({ images: ['https://service.bckf.cn/chameleon/gzh.png'], closeable: true });
};

// 图片处理,在这个函数中执行实际上传
const processImage = async (): Promise<void> => {
  const file = uploadImage.value;
  if (!file) {
    showNotify({ type: 'warning', message: '请先上传图片' });
    return;
  }

  const formData = new FormData();
  formData.append('image', file);
  const encryptedPrompt = encryptData(userPrompt.value, getPublicKey());
  if (encryptedPrompt) formData.append('prompt', encryptedPrompt);

  isProcessing.value = true;
  processedImage.value = '';
  try {
    // 调用后端处理接口.
    const response = await alovaInstance.Post('/api/process', formData, {
      headers: {
        'Authorization': `Bearer ${sessionId.value}`
      }
    }) as ProcessImage;

    const { error, result } = response;
    if (error) {
      showNotify({ type: 'danger', message: error });
      return;
    }

    if (result) {
      processedImage.value = `data:image/png;base64,${result}`;
      addToHistory(processedImage.value, userPrompt.value);
      showNotify({ type: 'success', message: '处理成功' });
    }
  } catch (err: any) {
    showNotify({ type: 'danger', message: err.message || '图片处理异常' });
  } finally {
    isProcessing.value = false;
  }
};

// 下载图片
const downloadImage = (): void => {
  if (!processedImage.value) return;
  const link = document.createElement('a');
  link.href = processedImage.value;
  link.download = 'processed_image.png';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// 加载历史记录
const loadUserHistory = (): void => {
  const userId = localStorage.getItem('github_user_id') || 'default_user';
  const historyKey = `user_${CryptoJS.MD5(userId).toString()}`;
  const historyData = localStorage.getItem(historyKey);
  if (historyData) {
    try {
      const parsedData = JSON.parse(historyData);
      userHistory.value = parsedData.history || [];
    } catch (e) {
      console.error('历史记录转换失败:', e);
      userHistory.value = [];
    }
  }
};

// 添加历史记录
const addToHistory = (imageData: string, prompt: string): void => {
  const userId = localStorage.getItem('github_user_id') || 'default_user';
  const historyKey = `user_${CryptoJS.MD5(userId).toString()}`;

  const newItem: HistoryItem = {
    timestamp: Date.now(),
    image: imageData,
    prompt: prompt
  };
  userHistory.value.unshift(newItem);
  if (userHistory.value.length > 50) {
    userHistory.value.pop();
  }
  saveUserHistory(historyKey);
};

// 保存用户历史
const saveUserHistory = (historyKey: string): void => {
  const historyData = { history: userHistory.value };
  localStorage.setItem(historyKey, JSON.stringify(historyData));
};

// 加载历史记录细项
const loadHistoryItem = (item: HistoryItem): void => {
  processedImage.value = item.image;
  showNotify({ type: 'success', message: '历史记录已加载' });
};

// 登录状态检查
const checkLoginStatus = (): void => {
  const token = localStorage.getItem('app_session_token');
  if (token) {
    sessionId.value = token;
    isLoggedIn.value = true;
    let githubId = localStorage.getItem('github_user_id');
    if (githubId) {
      if (githubId.length > 2) {
        githubId = `${githubId.substring(0, 3)}**`;
      }
      githubUsername.value = githubId;
    }
    loadUserHistory();
  }
};

// 页面加载时
onMounted(() => {
  checkLoginStatus();
  const urlParams = new URLSearchParams(window.location.search);
  const tokenFromUrl = urlParams.get('token');
  if (tokenFromUrl) {
    localStorage.setItem('app_session_token', tokenFromUrl);
    window.history.replaceState({}, document.title, '/');
    checkLoginStatus();
  }
});
</script>

<style scoped>
.top-nav-bar {
  --van-nav-bar-background: #ffffff;
  --van-nav-bar-height: 50px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0 10px;
}

.nav-logo {
  width: 36px;
  height: 36px;
  margin-right: 10px;
}

.nav-right {
  display: flex;
  align-items: center;
  height: 100%;
}

.username {
  margin-right: 12px;
  font-size: 14px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.nav-button {
  --van-button-default-height: 30px;
  --van-button-small-font-size: 13px;
}

.main-content {
  padding-top: calc(var(--van-nav-bar-height, 46px) + 10px);
  max-width: 800px;
  margin: 0 auto;
  padding-left: 16px;
  padding-right: 16px;
  padding-bottom: 16px;
  text-align: center;
}


.app-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.disclaimer {
  font-size: 12px;
  color: #999;
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 16px;
  text-align: left;
}

.result-section {
  margin-top: 20px;
  padding: 15px;
  border-top: 1px solid #eee;
  text-align: center;
}

.image-container {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.result-image {
  max-width: 100%;
  height: auto;
  max-height: 500px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.bottom-info {
  font-size: 12px;
  color: #999;
  margin-top: 10px;
  position: absolute;
  bottom: 5px;
  text-align: center;
}


@media (max-width: 768px) {
  /*.app-container {
    !* padding: 10px; *!
  }*/
  .disclaimer {
    font-size: 11px;
    padding: 8px;
  }

  .result-image {
    max-height: 300px;
  }

  .top-nav-bar {
    --van-nav-bar-height: 46px;
    padding: 0 8px;
  }

  .nav-logo {
    width: 32px;
    height: 32px;
  }

  .username {
    font-size: 13px;
    margin-right: 8px;
    max-width: 100px;
  }

  .nav-button {
    --van-button-default-height: 28px;
    --van-button-small-font-size: 12px;
  }

  .main-content {
    padding-top: calc(var(--van-nav-bar-height, 46px) + 8px);
    padding-left: 12px;
    padding-right: 12px;
  }
}
</style>