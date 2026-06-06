<template>
  <div class="fault-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">故障处理</span>
          <div class="statistics">
            <el-tag type="danger" size="large">
              待处理: {{ statistics.pending || 0 }}
            </el-tag>
            <el-tag type="warning" size="large">
              处理中: {{ statistics.processing || 0 }}
            </el-tag>
            <el-tag type="success" size="large">
              已解决: {{ statistics.resolved || 0 }}
            </el-tag>
            <el-tag type="info" size="large">
              已关闭: {{ statistics.closed || 0 }}
            </el-tag>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="故障类型">
          <el-select v-model="searchForm.fault_type" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="不能上网" value="cannot_connect" />
            <el-option label="网络卡顿" value="slow_network" />
            <el-option label="频繁掉线" value="frequent_disconnect" />
          </el-select>
        </el-form-item>
        <el-form-item label="公寓">
          <el-select v-model="searchForm.apartment_id" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="账号/报障人/描述"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="上网账号" width="120" />
        <el-table-column prop="apartment_name" label="公寓" width="120" />
        <el-table-column prop="room" label="房间号" width="80" />
        <el-table-column prop="fault_type_text" label="故障类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getFaultTypeTag(row.fault_type)">
              {{ row.fault_type_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reporter_name" label="报障人" width="100" />
        <el-table-column prop="reporter_phone" label="联系电话" width="120" />
        <el-table-column prop="description" label="故障描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="fault_time" label="故障时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.fault_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="处理人" width="100" />
        <el-table-column prop="resolve_time" label="处理时间" width="160">
          <template #default="{ row }">
            {{ row.resolve_time ? formatDateTime(row.resolve_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              link
              type="warning"
              size="small"
              @click="handleStartProcessing(row)"
            >
              开始处理
            </el-button>
            <el-button
              v-if="row.status === 'processing'"
              link
              type="success"
              size="small"
              @click="handleResolve(row)"
            >
              标记解决
            </el-button>
            <el-button
              v-if="row.status === 'resolved'"
              link
              type="info"
              size="small"
              @click="handleClose(row)"
            >
              关闭
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
        style="margin-top: 20px; justify-content: flex-end;"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="故障详情"
      width="700px"
    >
      <el-descriptions :column="2" border v-if="detailData">
        <el-descriptions-item label="上网账号">
          <el-tag type="primary" size="small">{{ detailData.username }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="报障人">{{ detailData.reporter_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ detailData.reporter_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="公寓">{{ detailData.apartment_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房间号">{{ detailData.room || '-' }}</el-descriptions-item>
        <el-descriptions-item label="故障类型">
          <el-tag :type="getFaultTypeTag(detailData.fault_type)">
            {{ detailData.fault_type_text }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="故障时间" :span="2">
          {{ formatDateTime(detailData.fault_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="故障描述" :span="2">
          {{ detailData.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailData.status)">
            {{ detailData.status_text }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理人">{{ detailData.operator_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="处理时间" :span="2">
          {{ detailData.resolve_time ? formatDateTime(detailData.resolve_time) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="处理说明" :span="2">
          {{ detailData.resolve_description || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <template #footer v-if="detailData && detailData.status !== 'closed'">
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          v-if="detailData.status === 'pending'"
          type="warning"
          @click="handleStartProcessing(detailData); detailVisible = false"
        >
          开始处理
        </el-button>
        <el-button
          v-if="detailData.status === 'processing'"
          type="success"
          @click="handleResolve(detailData)"
        >
          标记解决
        </el-button>
        <el-button
          v-if="detailData.status === 'resolved'"
          type="info"
          @click="handleClose(detailData); detailVisible = false"
        >
          关闭
        </el-button>
      </template>
    </el-dialog>

    <!-- 处理说明弹窗 -->
    <el-dialog
      v-model="resolveDialogVisible"
      title="处理故障"
      width="500px"
    >
      <el-form :model="resolveForm" label-width="100px">
        <el-form-item label="故障账号">
          <span>{{ resolveForm.username }}</span>
        </el-form-item>
        <el-form-item label="故障类型">
          <el-tag :type="getFaultTypeTag(resolveForm.fault_type)">
            {{ resolveForm.fault_type_text }}
          </el-tag>
        </el-form-item>
        <el-form-item label="处理说明" prop="resolve_description">
          <el-input
            v-model="resolveForm.resolve_description"
            type="textarea"
            :rows="4"
            placeholder="请输入处理说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="resolveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResolveSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh } from '@element-plus/icons-vue';
import {
  getFaultReports,
  updateFaultReport,
  getFaultStatistics,
  getApartments
} from './api';

const loading = ref(false);
const tableData = ref([]);
const statistics = ref({});
const apartments = ref([]);
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
});

const searchForm = reactive({
  keyword: '',
  status: '',
  fault_type: '',
  apartment_id: ''
});

const detailVisible = ref(false);
const detailData = ref(null);

const resolveDialogVisible = ref(false);
const submitLoading = ref(false);
const resolveForm = reactive({
  id: null,
  username: '',
  fault_type: '',
  fault_type_text: '',
  resolve_description: ''
});

const getFaultTypeTag = (type) => {
  const typeMap = {
    'cannot_connect': 'danger',
    'slow_network': 'warning',
    'frequent_disconnect': 'warning'
  };
  return typeMap[type] || 'info';
};

const getStatusType = (status) => {
  const statusMap = {
    'pending': 'danger',
    'processing': 'warning',
    'resolved': 'success',
    'closed': 'info'
  };
  return statusMap[status] || 'info';
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

const loadData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...searchForm
    };
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key];
      }
    });

    // 默认过滤掉已解决和已关闭的记录，除非用户明确选择了状态
    if (!params.status) {
      params.exclude_status = 'resolved,closed';
    }

    const res = await getFaultReports(params);
    if (res.code === 200) {
      tableData.value = res.data || [];
      pagination.total = res.total || 0;
    }
  } catch (error) {
    console.error('加载数据失败:', error);
    ElMessage.error('加载数据失败');
  } finally {
    loading.value = false;
  }
};

const loadStatistics = async () => {
  try {
    const res = await getFaultStatistics();
    if (res.code === 200) {
      statistics.value = res.data || {};
    }
  } catch (error) {
    console.error('加载统计数据失败:', error);
  }
};

const loadApartments = async () => {
  try {
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (isAdmin) {
      const res = await getApartments({ page: 1, page_size: 100, status: 'active' });
      if (res.code === 200) {
        apartments.value = res.data || [];
      }
    } else {
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error);
  }
};

const resetSearch = () => {
  searchForm.keyword = '';
  searchForm.status = '';
  searchForm.fault_type = '';
  searchForm.apartment_id = '';
  pagination.page = 1;
  loadData();
};

const handleView = (row) => {
  detailData.value = row;
  detailVisible.value = true;
};

const handleStartProcessing = async (row) => {
  try {
    await updateFaultReport(row.id, { status: 'processing' });
    ElMessage.success('已开始处理');
    loadData();
    loadStatistics();
    if (detailVisible.value) {
      detailVisible.value = false;
    }
  } catch (error) {
    console.error('处理失败:', error);
    ElMessage.error('操作失败');
  }
};

const handleResolve = (row) => {
  resolveForm.id = row.id;
  resolveForm.username = row.username;
  resolveForm.fault_type = row.fault_type;
  resolveForm.fault_type_text = row.fault_type_text;
  resolveForm.resolve_description = '';
  resolveDialogVisible.value = true;
};

const handleResolveSubmit = async () => {
  try {
    submitLoading.value = true;
    await updateFaultReport(resolveForm.id, {
      status: 'resolved',
      resolve_description: resolveForm.resolve_description
    });
    ElMessage.success('已标记为已解决');
    resolveDialogVisible.value = false;
    loadData();
    loadStatistics();
  } catch (error) {
    console.error('处理失败:', error);
    ElMessage.error('操作失败');
  } finally {
    submitLoading.value = false;
  }
};

const handleClose = async (row) => {
  try {
    await ElMessageBox.confirm('确定要关闭此故障记录吗？', '关闭确认', {
      type: 'info'
    });
    await updateFaultReport(row.id, { status: 'closed' });
    ElMessage.success('已关闭');
    loadData();
    loadStatistics();
    if (detailVisible.value) {
      detailVisible.value = false;
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('关闭失败:', error);
      ElMessage.error('操作失败');
    }
  }
};

onMounted(() => {
  loadData();
  loadStatistics();
  loadApartments();
});
</script>

<style scoped>
.fault-container {
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
}

.statistics {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
}
</style>
