<!-- src/pages/github/callback.vue -->
<template>
  <div class="callback-container">
    <van-loading v-if="isLoading" size="24px" vertical>正在处理 GitHub 登录...</van-loading>
    <div v-else-if="error" class="error-section">
      <van-icon color="red" name="cross" size="32px" />
      <p style="margin: 10px 0;">{{ error }}</p>
      <van-button @click="goHome">返回首页</van-button>
    </div>
    <div v-else class="success-section">
      <van-icon color="green" name="passed" size="32px" />
      <p style="margin: 10px 0;">登录成功，正在跳转...</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { showNotify } from 'vant';
import { alovaInstance } from '~/api/api';

interface GithubCallbackResponse {
  token: string;
  identifier: string;
  error?: string;
}

const router = useRouter();
const isLoading = ref<boolean>(true);
const error = ref<string | null>(null);

const goHome = (): void => {
  router.push({ path: '/' });
};

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');

  if (!code) {
    isLoading.value = false;
    error.value = '缺少 GitHub 授权码';
    showNotify({ type: 'danger', message: error.value });
    return;
  }

  try {
    const response = await alovaInstance.Post('/api/auth/github/callback', { code }, {
      headers: {
        'Content-Type': 'application/json'
      }
    }) as GithubCallbackResponse;

    console.log('请求响应:', response);
    const { token, identifier } = response;

    localStorage.setItem('app_session_token', token);
    localStorage.setItem('github_user_id', identifier);

    isLoading.value = false;

    showNotify({ type: 'success', message: 'GitHub 登录成功' });

    setTimeout(() => {
      location.href = `${location.origin}${location.pathname}`;
    }, 0);

  } catch (err: any) {
    console.error('Github调用错误:', err);
    isLoading.value = false;
    error.value = err.message || '发生未知错误';
    showNotify({ type: 'danger', message: `${error.value}` });
  }
});
</script>

<style scoped>
.callback-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  text-align: center;
}

.error-section, .success-section {
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  background-color: #fff;
}
</style>