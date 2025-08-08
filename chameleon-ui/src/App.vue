<template>
  <div class="">
    <router-view />
  </div>
</template>

<script setup>

import { useRouter } from 'vue-router';

const router = useRouter();
router.push('/')

</script>

<style scoped>


</style>