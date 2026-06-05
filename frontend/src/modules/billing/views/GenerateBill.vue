<template>
  <div class="billing-container">
    <!-- 生成账单卡片：仅管理员可见 -->
    <el-card v-if="isAdmin">
      <template #header>
        <div class="header-actions">
          <span class="title">生成帐单</span>
        </div>
      </template>

      <el-form :inline="true" class="generate-form">
        <el-form-item label="公寓">
          <el-select v-model="generateForm.apartment_id" placeholder="请选择公寓" style="width: 250px">
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="`${apt.code} - ${apt.name}`"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账单月份">
          <el-date-picker
            v-model="generateForm.billMonth"
            type="month"
            placeholder="选择月份"
            format="YYYY-MM"
            value-format="YYYY-MM"
            style="width: 150px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate" :loading="generating">
            <el-icon><DocumentAdd /></el-icon>
            生成账单
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="header-actions">
          <span class="title">账单记录</span>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="公寓">
          <el-select v-model="searchForm.apartment_id" placeholder="全部公寓" clearable style="width: 200px">
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账单月份">
          <el-date-picker
            v-model="searchForm.bill_month"
            type="month"
            placeholder="选择月份"
            format="YYYY-MM"
            value-format="YYYY-MM"
            style="width: 150px"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRecords">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="records" v-loading="loading" stripe>
        <el-table-column prop="bill_month" label="账单月份" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.bill_month }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="apartment_code" label="公寓编号" width="120" align="center" />
        <el-table-column prop="apartment_name" label="公寓名称" min-width="150" />
        <el-table-column prop="total_accounts" label="总账号" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.total_accounts }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="active_accounts" label="开通账号" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.active_accounts }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="inactive_accounts" label="未开通" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.inactive_accounts }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_amount" label="总费用" width="120" align="right">
          <template #default="{ row }">
            <span style="color: #409eff; font-weight: bold;">¥{{ row.total_amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="文件大小" width="100" align="center">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="100" align="center" />
        <el-table-column prop="created_at" label="生成时间" width="160" align="center" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetails(row)">
              查看
            </el-button>
            <el-button link type="success" @click="downloadRecord(row)">
              下载
            </el-button>
            <el-button v-if="isAdmin" link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > 0"
        style="margin-top: 20px; text-align: right"
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadRecords"
        @current-change="loadRecords"
      />
    </el-card>

    <el-dialog
      v-model="detailsVisible"
      :title="`账单详情 - ${currentRecord?.apartment_name || ''}`"
      width="90%"
      top="5vh"
    >
      <div v-if="currentRecord" class="record-details">
        <el-descriptions :column="3" border style="margin-bottom: 20px">
          <el-descriptions-item label="账单月份">
            <el-tag type="info">{{ currentRecord.bill_month }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="公寓编号">{{ currentRecord.apartment_code }}</el-descriptions-item>
          <el-descriptions-item label="公寓名称">{{ currentRecord.apartment_name }}</el-descriptions-item>
          <el-descriptions-item label="总账号数">{{ currentRecord.total_accounts }}</el-descriptions-item>
          <el-descriptions-item label="开通账号">
            <el-tag type="success">{{ currentRecord.active_accounts }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="未开通账号">
            <el-tag type="info">{{ currentRecord.inactive_accounts }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总费用" :span="3">
            <span style="color: #409eff; font-size: 18px; font-weight: bold;">
              ¥{{ currentRecord.total_amount }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="生成时间" :span="3">{{ currentRecord.created_at }}</el-descriptions-item>
        </el-descriptions>

        <div style="text-align: center; margin-bottom: 20px">
          <el-button type="success" size="large" @click="downloadRecord(currentRecord)">
            <el-icon><Download /></el-icon>
            下载Excel文件
          </el-button>
          <el-tag type="info" style="margin-left: 20px">
            文件: {{ currentRecord.file_name }}
          </el-tag>
          <el-tag type="info" style="margin-left: 10px">
            大小: {{ formatFileSize(currentRecord.file_size) }}
          </el-tag>
        </div>

        <el-divider content-position="left">账单明细</el-divider>

        <el-table
          v-if="currentRecord.bill_details && currentRecord.bill_details.length > 0"
          :data="currentRecord.bill_details"
          stripe
          max-height="400"
        >
          <el-table-column prop="username" label="宽带账号" width="150" fixed />
          <el-table-column prop="room" label="房间号" width="100" align="center" />
          <el-table-column prop="plan_name" label="套餐名称" min-width="180" />
          <el-table-column prop="plan_price" label="月费" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.plan_price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="activate_date" label="开通时间" width="120" />
          <el-table-column prop="expire_date" label="到期时间" width="120" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                {{ row.status === 'active' ? '已开通' : '已停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="monthly_fee" label="本月费用" width="120" align="right">
            <template #default="{ row }">
              <span v-if="row.monthly_fee == 0" style="color: #e6a23c;">免费</span>
              <span v-else style="color: #409eff; font-weight: bold;">¥{{ row.monthly_fee.toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <el-empty v-else description="暂无明细数据" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, DocumentAdd, Download } from '@element-plus/icons-vue'
import {
  generateBill,
  getBillRecords,
  getBillRecord,
  getBillDetails,
  deleteBill,
  downloadBill,
  getBillingApartments
} from '../api_new'

const generating = ref(false)
const loading = ref(false)
const records = ref([])
const total = ref(0)
const apartments = ref([])
const detailsVisible = ref(false)
const currentRecord = ref(null)

// 判断是否为管理员
const isAdmin = computed(() => {
  const role = localStorage.getItem('role')
  return role === 'admin'
})

const generateForm = reactive({
  apartment_id: null,
  billMonth: ''
})

const searchForm = reactive({
  apartment_id: null,
  bill_month: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

onMounted(() => {
  loadApartments().then(() => {
    // 如果是非管理员，自动选择自己关联的公寓
    if (!isAdmin.value && apartments.value.length > 0) {
      searchForm.apartment_id = apartments.value[0].id
    }
  })
  loadRecords()
})

const loadApartments = async () => {
  try {
    // 如果是管理员，加载所有公寓；否则只加载自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
      const res = await getBillingApartments()
      if (res.code === 200) {
        apartments.value = res.data || []
      }
    } else {
      // 非管理员只能看到自己关联的公寓
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error)
  }
}

const handleGenerate = async () => {
  if (!generateForm.apartment_id) {
    ElMessage.warning('请选择公寓')
    return
  }

  if (!generateForm.billMonth) {
    ElMessage.warning('请选择账单月份')
    return
  }

  generating.value = true
  try {
    const [year, month] = generateForm.billMonth.split('-')

    const res = await generateBill({
      year: parseInt(year),
      month: parseInt(month),
      apartment_id: generateForm.apartment_id
    })

    if (res.code === 200) {
      ElMessage.success('账单生成成功')
      loadRecords()
    } else {
      ElMessage.error(res.message || '生成失败')
    }
  } catch (error) {
    console.error('生成账单失败:', error)
    ElMessage.error('生成失败')
  } finally {
    generating.value = false
  }
}

const loadRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }

    if (searchForm.apartment_id) {
      params.apartment_id = searchForm.apartment_id
    }

    if (searchForm.bill_month) {
      params.bill_month = searchForm.bill_month
    }

    const res = await getBillRecords(params)

    if (res.code === 200) {
      records.value = res.data || []
      total.value = res.total || 0
    }
  } catch (error) {
    console.error('加载账单记录失败:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.apartment_id = null
  searchForm.bill_month = ''
  pagination.page = 1
  loadRecords()
}

const showDetails = async (row) => {
  try {
    const res = await getBillDetails(row.id)

    if (res.code === 200) {
      currentRecord.value = res.data
      detailsVisible.value = true
    } else {
      ElMessage.error(res.message || '获取详情失败')
    }
  } catch (error) {
    console.error('获取详情失败:', error)
    ElMessage.error('获取详情失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${row.apartment_name} ${row.bill_month} 的账单吗？删除后无法恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await deleteBill(row.id)

    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadRecords()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const downloadRecord = async (row) => {
  try {
    const res = await downloadBill(row.id)

    const blob = new Blob([res], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })

    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = row.file_name || '账单.xlsx'
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i]
}
</script>

<style scoped>
.billing-container {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.generate-form {
  margin-bottom: 0;
}

.search-form {
  margin-bottom: 20px;
}

.record-details {
  padding: 10px;
}
</style>
