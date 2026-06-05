<template>
  <div class="not-found-container">
    <h1>404</h1>
    <p>页面不存在</p>
    <el-button type="primary" @click="goHome">返回首页</el-button>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.not-found-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

h1 {
  font-size: 120px;
  color: #409eff;
  margin-bottom: 20px;
}

p {
  font-size: 20px;
  color: #666;
  margin-bottom: 30px;
}
</style>
