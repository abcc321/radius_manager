<template>
  <div class="diagnostic-container">
    <el-card>
      <template #header>
        <h2>WebSocket 诊断工具</h2>
      </template>

      <el-space direction="vertical" :size="20" style="width: 100%">
        <el-alert
          :title="connectionStatus"
          :type="isConnected ? 'success' : 'danger'"
          :description="wsUrl"
          show-icon
        />

        <el-descriptions border>
          <el-descriptions-item label="WebSocket URL">
            {{ wsUrl }}
          </el-descriptions-item>
          <el-descriptions-item label="连接状态">
            <el-tag :type="isConnected ? 'success' : 'danger'">
              {{ isConnected ? '已连接' : '未连接' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="最后接收时间">
            {{ lastMessageTime || '暂无' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>收到的消息</el-divider>

        <el-card v-if="messages.length > 0" class="messages-card">
          <el-scrollbar height="300px">
            <div v-for="(msg, index) in messages" :key="index" class="message-item">
              <el-tag :type="msg.type === 'radius_status' ? 'success' : 'info'" size="small">
                {{ msg.type }}
              </el-tag>
              <pre>{{ JSON.stringify(msg.data, null, 2) }}</pre>
            </div>
          </el-scrollbar>
        </el-card>
        <el-empty v-else description="暂无消息" />

        <el-space>
          <el-button type="primary" @click="testConnection">
            测试连接
          </el-button>
          <el-button @click="clearMessages">
            清空消息
          </el-button>
        </el-space>
      </el-space>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

const wsUrl = ref('')
const isConnected = ref(false)
const messages = ref([])
const lastMessageTime = ref(null)
let ws = null

const connectionStatus = computed(() => {
  return isConnected.value ? '✅ WebSocket已连接' : '❌ WebSocket未连接'
})

const testConnection = () => {
  if (ws) {
    ws.close()
    ws = null
  }

  wsUrl.value = `ws://${window.location.host}/ws/radius`
  console.log('[Diagnostic] Attempting to connect to:', wsUrl.value)

  try {
    ws = new WebSocket(wsUrl.value)

    ws.onopen = () => {
      console.log('[Diagnostic] Connected')
      isConnected.value = true
      ElMessage.success('WebSocket连接成功')
    }

    ws.onmessage = (event) => {
      console.log('[Diagnostic] Message received:', event.data)
      try {
        const data = JSON.parse(event.data)
        messages.value.unshift({
          type: data.type,
          data: data.data,
          timestamp: new Date().toLocaleTimeString()
        })
        lastMessageTime.value = new Date().toLocaleTimeString()
      } catch (e) {
        console.error('[Diagnostic] Parse error:', e)
      }
    }

    ws.onerror = (error) => {
      console.error('[Diagnostic] Error:', error)
      isConnected.value = false
      ElMessage.error('WebSocket连接错误')
    }

    ws.onclose = (event) => {
      console.log('[Diagnostic] Closed:', event.code, event.reason)
      isConnected.value = false
    }
  } catch (error) {
    console.error('[Diagnostic] Failed to create WebSocket:', error)
    ElMessage.error('创建WebSocket失败')
  }
}

const clearMessages = () => {
  messages.value = []
  lastMessageTime.value = null
}

onMounted(() => {
  testConnection()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
})
</script>

<style scoped>
.diagnostic-container {
  padding: 20px;
}

.messages-card {
  background: #f5f7fa;
}

.message-item {
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.message-item:last-child {
  border-bottom: none;
}

pre {
  margin: 10px 0 0 0;
  padding: 10px;
  background: white;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>
