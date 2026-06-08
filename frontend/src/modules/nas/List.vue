<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">NAS设备管理</span>
          <el-button type="primary" @click="handleCreate" size="small">
            <el-icon><Plus /></el-icon>
            <span class="hide-on-mobile">新增设备</span>
          </el-button>
        </div>
      </template>

      <div class="search-form responsive-search-form">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="公寓" class="hide-on-mobile">
            <el-select
              v-model="searchForm.apartment_id"
              placeholder="公寓"
              clearable
              filterable
              style="width: 150px;"
            >
              <el-option
                v-for="apt in apartments"
                :key="apt.id"
                :label="apt.name"
                :value="apt.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="关键词" class="hide-on-mobile">
            <el-input
              v-model="searchForm.keyword"
              placeholder="名称/IP/类型"
              clearable
              @keyup.enter="handleSearch"
              style="width: 150px"
            />
          </el-form-item>
          <el-form-item label="状态" class="hide-on-mobile">
            <el-select v-model="searchForm.status" placeholder="状态" clearable style="width: 120px">
              <el-option label="在线" value="online" />
              <el-option label="离线" value="offline" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch" size="small">
              <el-icon><Search /></el-icon>
              <span>查询</span>
            </el-button>
            <el-button @click="handleReset" size="small">
              <el-icon><Refresh /></el-icon>
              <span>重置</span>
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="table-responsive-wrapper">
        <el-table :data="tableData" v-loading="loading" stripe>
          <el-table-column prop="name" label="设备名称" min-width="120" />
          <el-table-column prop="ip_address" label="IP地址" width="130" />
          <el-table-column prop="apartment_name" label="公寓" width="120" class-name="hide-on-mobile">
            <template #default="{ row }">
              <el-tag v-if="row.apartment_name" size="small" type="info">
                {{ row.apartment_name }}
              </el-tag>
              <span v-else style="color: #999;">未分配</span>
            </template>
          </el-table-column>
          <el-table-column prop="nas_identifier" label="标识" width="150" class-name="hide-on-tablet">
            <template #default="{ row }">
              <span v-if="row.nas_identifier" style="color: #409eff;">
                {{ row.nas_identifier }}
              </span>
              <span v-else style="color: #999;">未设置</span>
            </template>
          </el-table-column>
          <el-table-column prop="secret" label="密钥" width="120" class-name="hide-on-mobile">
            <template #default="{ row }">
              <span style="color: #67c23a;">{{ row.secret || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="device_type" label="类型" width="100" class-name="hide-on-tablet" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.status === 'online' ? 'success' : row.status === 'offline' ? 'danger' : 'info'" size="small">
                {{ row.status === 'online' ? '在线' : row.status === 'offline' ? '离线' : '未知' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleDetail(row)">详情</el-button>
              <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadData"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="95%"
      class="responsive-dialog"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        class="responsive-form"
      >
        <el-form-item label="所属公寓" prop="apartment_id">
          <el-select
            v-model="form.apartment_id"
            placeholder="选择公寓（可选）"
            clearable
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="MAC地址" prop="mac_address">
          <el-input v-model="form.mac_address" placeholder="请输入MAC地址" />
        </el-form-item>
        <el-form-item label="标识" prop="nas_identifier">
          <el-input
            v-model="form.nas_identifier"
            placeholder="NAS设备标识符"
          />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="form.device_type" placeholder="请选择设备类型" clearable style="width: 100%">
            <el-option label="RouterOS" value="RouterOS" />
            <el-option label="Cisco" value="Cisco" />
            <el-option label="H3C" value="H3C" />
            <el-option label="Huawei" value="Huawei" />
            <el-option label="TP-Link" value="TP-Link" />
            <el-option label="Other" value="Other" />
          </el-select>
        </el-form-item>
        <el-form-item label="SNMP团体" prop="community">
          <el-input v-model="form.community" placeholder="请输入SNMP团体名" />
        </el-form-item>
        <el-form-item label="密钥" prop="secret">
          <el-input v-model="form.secret" placeholder="不修改请留空" />
        </el-form-item>
        <el-form-item label="检测间隔" prop="check_interval">
          <el-input-number v-model="form.check_interval" :min="1" :max="60" placeholder="检测间隔（分钟）" style="width: 100%" />
        </el-form-item>
        <el-form-item label="会话超时" prop="session_timeout">
          <el-input-number
            v-model="form.session_timeout"
            :min="0"
            :max="86400"
            placeholder="会话超时时间（秒）"
            style="width: 100%"
          />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">设置为0则不发送</span>
        </el-form-item>
        <el-form-item label="计费间隔" prop="acct_interim_interval">
          <el-input-number
            v-model="form.acct_interim_interval"
            :min="0"
            :max="86400"
            placeholder="计费更新间隔（秒）"
            style="width: 100%"
          />
          <span style="margin-left: 10px; color: #999; font-size: 12px;">设置为0则不发送</span>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" placeholder="请输入描述" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false" size="small">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit" size="small">
          确定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailDialogVisible"
      title="设备详情"
      width="95%"
      class="responsive-dialog"
    >
      <el-descriptions :column="2" border v-if="currentRow">
        <el-descriptions-item label="设备名称">{{ currentRow.name }}</el-descriptions-item>
        <el-descriptions-item label="所属公寓">
          <el-tag v-if="currentRow.apartment_name" size="small" type="info">
            {{ currentRow.apartment_name }}
          </el-tag>
          <span v-else style="color: #999;">未分配</span>
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentRow.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="MAC地址">{{ currentRow.mac_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="标识">
          <span v-if="currentRow.nas_identifier" style="color: #409eff;">
            {{ currentRow.nas_identifier }}
          </span>
          <span v-else style="color: #999;">未设置</span>
        </el-descriptions-item>
        <el-descriptions-item label="密钥">
          <span style="color: #67c23a;">{{ currentRow.secret || '-' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ currentRow.device_type || '-' }}</el-descriptions-item>
        <el-descriptions-item label="SNMP团体">{{ currentRow.community || '-' }}</el-descriptions-item>
        <el-descriptions-item label="设备状态">
          <el-tag size="small" :type="currentRow.status === 'online' ? 'success' : currentRow.status === 'offline' ? 'danger' : 'info'">
            {{ currentRow.status === 'online' ? '在线' : currentRow.status === 'offline' ? '离线' : '未知' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="最后检测">
          {{ currentRow.last_check ? formatDateTime(currentRow.last_check) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="响应时间">
          {{ currentRow.response_time ? currentRow.response_time + 'ms' : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentRow.description || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(currentRow.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(currentRow.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDate, formatDateTime } from '@/common/utils'
import {
  getNasDevices,
  getNasDevice,
  createNasDevice,
  updateNasDevice,
  deleteNasDevice,
  testNasDevice
} from './api'
import { getApartments } from '@/modules/apartment/api'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'

const loading = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const submitLoading = ref(false)
const formRef = ref()
const currentRow = ref(null)
const apartments = ref([])

const isEdit = computed(() => !!currentRow.value?.id)
const dialogTitle = computed(() => isEdit.value ? '编辑设备' : '新增设备')

const searchForm = reactive({
  apartment_id: '',
  keyword: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  name: '',
  ip_address: '',
  mac_address: '',
  nas_identifier: '',
  device_type: '',
  community: '',
  secret: '',
  check_interval: 1,
  session_timeout: 15682168,
  acct_interim_interval: 60,
  description: '',
  apartment_id: null
})

const formRules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '请输入正确的IP地址格式', trigger: 'blur' }
  ],
  secret: [{ required: true, message: '请输入共享密钥', trigger: 'blur' }]
}

const loadApartments = async () => {
  try {
    const res = await getApartments({ page: 1, page_size: 100 })
    apartments.value = res.data || []
  } catch (error) {
    console.error('加载公寓列表失败:', error)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (searchForm.keyword) {
      params.keyword = searchForm.keyword
    }
    if (searchForm.status) {
      params.status = searchForm.status
    }
    if (searchForm.apartment_id) {
      params.apartment_id = searchForm.apartment_id
    }

    const res = await getNasDevices(params)
    tableData.value = res.data || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.apartment_id = ''
  searchForm.keyword = ''
  searchForm.status = ''
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  Object.assign(form, {
    name: '',
    ip_address: '',
    mac_address: '',
    nas_identifier: '',
    device_type: '',
    community: '',
    secret: '',
    check_interval: 1,
    description: '',
    apartment_id: searchForm.apartment_id || null
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  currentRow.value = { ...row }
  Object.assign(form, {
    name: row.name,
    ip_address: row.ip_address,
    mac_address: row.mac_address,
    nas_identifier: row.nas_identifier || '',
    device_type: row.device_type,
    community: row.community,
    secret: row.secret || '',
    check_interval: row.check_interval || 1,
    session_timeout: row.session_timeout || null,
    acct_interim_interval: row.acct_interim_interval || null,
    description: row.description,
    apartment_id: row.apartment_id || null
  })
  dialogVisible.value = true
}

const handleDetail = async (row) => {
  try {
    const res = await getNasDevice(row.id)
    currentRow.value = res.data
    detailDialogVisible.value = true
  } catch (error) {
    console.error('加载详情失败:', error)
  }
}

const handleTest = async (row) => {
  try {
    ElMessage.info('正在测试设备连接...')
    const res = await testNasDevice(row.id)
    if (res.data.status === 'online') {
      ElMessage.success(`设备连接成功 (响应时间: ${res.data.response_time}ms)`)
    } else {
      ElMessage.error(`设备连接失败: ${res.data.error_message || 'Unknown error'}`)
    }
    loadData()
  } catch (error) {
    console.error('测试失败:', error)
    ElMessage.error('测试失败')
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          const updateData = { ...form }
          if (!updateData.secret) {
            delete updateData.secret
          }
          await updateNasDevice(currentRow.value.id, updateData)
          ElMessage.success('更新成功')
        } else {
          await createNasDevice(form)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadData()
      } catch (error) {
        console.error('提交失败:', error)
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除设备"${row.name}"吗？`,
      '提示',
      { type: 'warning' }
    )
    await deleteNasDevice(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  if (hours > 0) {
    return `${hours}小时${minutes}分`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadApartments()
  loadData()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.ml-10 {
  margin-left: 10px;
}

.empty-text {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
}

/* 手机端样式优化 */
@media (max-width: 767px) {
  .page-container {
    padding: 10px;
  }

  .search-form {
    padding: 12px;
    margin-bottom: 15px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .page-title {
    font-size: 16px;
    font-weight: 600;
  }

  .el-button--small {
    padding: 6px 12px;
  }

  .el-button .el-icon {
    margin-right: 4px;
  }
}

@media (max-width: 480px) {
  .el-button .el-icon {
    margin-right: 0;
  }

  .el-button span {
    display: none;
  }
}
</style>
