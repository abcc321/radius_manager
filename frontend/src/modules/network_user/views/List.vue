<template>
  <div class="network-user-container">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span class="title">网络用户管理</span>
          <div class="actions">
            <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建用户
          </el-button>
          <el-button @click="handleImport">
            <el-icon><Upload /></el-icon>
            导入
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
          <el-button
            type="warning"
            @click="handleBatchDeactivate"
            :disabled="selectedUsers.length === 0"
          >
            <el-icon><CircleClose /></el-icon>
            批量停用
          </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" class="search-form">
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="已开通" value="active" />
            <el-option label="即将到期" value="expiring" />
            <el-option label="已过期" value="expired" />
            <el-option label="未开通" value="inactive" />
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
        <el-form-item label="套餐">
          <el-select v-model="searchForm.plan_id" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option
              v-for="plan in plans"
              :key="plan.id"
              :label="plan.name"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="账号/姓名/手机号"
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

      <el-table :data="tableData" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="username" label="上网账号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column prop="room" label="房间号" width="80" />
        <el-table-column prop="apartment_name" label="公寓" width="120" />
        <el-table-column prop="plan_name" label="套餐" width="150">
          <template #default="{ row }">
            {{ row.plan_name || '-' }}
            <span v-if="row.plan_price" style="color: #909399; font-size: 12px;">
              ({{ row.plan_price }})
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)">
              {{ getStatusText(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="activate_date" label="开通日期" width="110" />
        <el-table-column prop="expire_date" label="到期日期" width="110" />
        <el-table-column label="操作" fixed="right" width="240">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleDetail(row)">
              详情
            </el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">
              开通
            </el-button>
            <el-button link type="warning" size="small" @click="handleDeactivate(row)">
              停用
            </el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
            <el-button link type="info" size="small" @click="handleReportFault(row)">
              报障
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="上网账号" prop="username" v-if="!isEdit">
          <el-input v-model="formData.username" placeholder="请输入上网账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="formData.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="房间号" prop="room">
          <el-input v-model="formData.room" placeholder="请输入房间号" />
        </el-form-item>
        <el-form-item label="所属公寓" prop="apartment_id">
          <el-select v-model="formData.apartment_id" placeholder="请选择公寓" style="width: 100%" @change="handleApartmentChange">
            <el-option
              v-for="apt in apartments"
              :key="apt.id"
              :label="apt.name"
              :value="apt.id"
            />
          </el-select>
        </el-form-item>
        <el-divider v-if="isEdit" content-position="left">开通设置</el-divider>
        <el-form-item label="选择套餐" prop="plan_id" v-if="isEdit">
          <el-select v-model="formData.plan_id" placeholder="请选择套餐" style="width: 100%" :disabled="!formData.apartment_id">
            <el-option label="无" :value="0" />
            <el-option
              v-for="plan in filteredPlans"
              :key="plan.id"
              :label="`${plan.name} (${plan.price})`"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐" prop="plan_id" v-if="!isEdit">
          <el-select v-model="formData.plan_id" placeholder="请先选择公寓" style="width: 100%" :disabled="!formData.apartment_id">
            <el-option label="无" :value="0" />
            <el-option
              v-for="plan in filteredPlans"
              :key="plan.id"
              :label="`${plan.name} (${plan.price})`"
              :value="plan.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="开通时间" prop="activate_date" v-if="isEdit">
          <el-date-picker
            v-model="formData.activate_date"
            type="date"
            placeholder="选择开通日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="calculateExpireDateByMonths"
          />
        </el-form-item>
        <el-form-item label="开通时间" prop="activate_date" v-if="!isEdit">
          <el-date-picker
            v-model="formData.activate_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @change="calculateExpireDate"
          />
        </el-form-item>
        <el-form-item label="开通月数" prop="months" v-if="isEdit">
          <el-select v-model="formData.months" placeholder="请选择开通月数" style="width: 100%" @change="calculateExpireDateByMonths">
            <el-option label="1个月" :value="1" />
            <el-option label="2个月" :value="2" />
            <el-option label="3个月" :value="3" />
            <el-option label="6个月" :value="6" />
            <el-option label="12个月" :value="12" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期日期" v-if="isEdit">
          <el-input v-model="formData.expire_date" disabled placeholder="选择开通月数后自动计算">
            <template #prefix>
              <el-icon><Calendar /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="到期日期" prop="expire_date" v-if="!isEdit">
          <el-date-picker
            v-model="formData.expire_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="用户详情"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="detailData">
        <el-descriptions-item label="上网账号">
          <el-tag type="primary" size="small">{{ detailData.username }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="密码">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span>{{ showPassword ? detailData.password : '••••••' }}</span>
            <el-button
              :icon="showPassword ? 'View' : 'Hide'"
              size="small"
              link
              @click="togglePasswordVisibility"
            >
              {{ showPassword ? '隐藏' : '显示' }}
            </el-button>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="姓名">{{ detailData.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ detailData.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="房间号">{{ detailData.room || '-' }}</el-descriptions-item>
        <el-descriptions-item label="所属公寓">
          {{ detailData.apartment_name?.name || detailData.apartment_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(detailData)">
            {{ getStatusText(detailData) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="套餐" :span="2">
          <template v-if="detailData.plan">
            {{ detailData.plan.name }}
            <el-tag size="small" type="success" style="margin-left: 10px;">
              {{ detailData.plan_price }}
            </el-tag>
            <div style="margin-top: 5px; font-size: 12px; color: #909399;">
              上行: {{ detailData.plan_upload_speed }} kbps |
              下行: {{ detailData.plan_download_speed }} kbps
            </div>
          </template>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="开通日期">{{ detailData.activate_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="到期日期">{{ detailData.expire_date || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="detailData.plan && detailData.activate_date && detailData.expire_date" style="margin-top: 20px;">
        <h4 style="margin-bottom: 10px;">费用明细（按月计算）</h4>
        <el-table :data="monthlyFees" stripe size="small">
          <el-table-column prop="month" label="月份" width="120" align="center" />
          <el-table-column prop="startDate" label="开始日期" width="120" align="center" />
          <el-table-column prop="endDate" label="结束日期" width="120" align="center" />
          <el-table-column prop="days" label="天数" width="80" align="center" />
          <el-table-column prop="amount" label="费用" width="100" align="center">
            <template #default="{ row }">
              <template v-if="row.isTrial">
                <el-tag type="warning" size="small">体验使用</el-tag>
              </template>
              <template v-else>
                <strong style="color: #409eff;">{{ row.amount }} 元</strong>
              </template>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" align="center">
            <template #default="{ row }">
              <el-tag :type="row.isCurrent ? 'success' : 'info'" size="small">
                {{ row.isCurrent ? '当前' : (row.isPast ? '已过期' : '未来') }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 15px; text-align: right; font-size: 16px; color: #303133;">
          <strong>总费用：{{ totalFee }} 元</strong>
        </div>
      </div>
    </el-dialog>

    <el-dialog
      v-model="importDialogVisible"
      title="导入用户"
      width="500px"
    >
      <div class="import-tips">
        <p>请上传Excel文件（.xlsx或.xls格式）</p>
        <p>文件应包含以下列：</p>
        <ul>
          <li>上网账号（必填）</li>
          <li>密码（必填）</li>
          <li>姓名</li>
          <li>手机号</li>
          <li>房间号</li>
          <li>公寓名称（必填）</li>
          <li>套餐名称</li>
          <li>开通日期（格式：YYYY-MM-DD）</li>
          <li>到期日期（格式：YYYY-MM-DD）</li>
        </ul>
      </div>
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        style="margin-top: 20px;"
      >
        <el-button type="primary">选择文件</el-button>
        <template #tip>
          <div class="el-upload__tip">支持.xlsx和.xls格式</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImportSubmit" :loading="importLoading">
          导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 报障弹窗 -->
    <el-dialog
      v-model="faultDialogVisible"
      title="提交故障报告"
      width="500px"
    >
      <el-form :model="faultForm" label-width="100px">
        <el-form-item label="上网账号">
          <span>{{ faultForm.username }}</span>
        </el-form-item>
        <el-form-item label="报障人" prop="reporter_name">
          <el-input v-model="faultForm.reporter_name" placeholder="请输入报障人姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="reporter_phone">
          <el-input v-model="faultForm.reporter_phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="故障类型" prop="fault_type">
          <el-select v-model="faultForm.fault_type" placeholder="请选择故障类型" style="width: 100%">
            <el-option label="不能上网" value="cannot_connect" />
            <el-option label="网络卡顿" value="slow_network" />
            <el-option label="频繁掉线" value="frequent_disconnect" />
          </el-select>
        </el-form-item>
        <el-form-item label="故障描述" prop="description">
          <el-input
            v-model="faultForm.description"
            type="textarea"
            :rows="3"
            placeholder="请详细描述故障情况"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="faultDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFaultSubmit" :loading="faultSubmitLoading">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, Refresh, Upload, Download, Calendar, CircleClose } from '@element-plus/icons-vue';
import {
  getNetworkUsers,
  createNetworkUser,
  updateNetworkUser,
  deleteNetworkUser,
  deactivateNetworkUser,
  exportNetworkUsers,
  importNetworkUsers,
  getApartments,
  getAllPlans,
  getNetworkUserDetail,
  createFaultReport
} from '../api';

const loading = ref(false);
const tableData = ref([]);
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
});

const selectedUsers = ref([]);

const handleSelectionChange = (selection) => {
  selectedUsers.value = selection;
};

const searchForm = reactive({
  keyword: '',
  status: '',
  apartment_id: '',
  plan_id: ''
});

const apartments = ref([]);
const plans = ref([]);

const filteredPlans = computed(() => {
  if (!formData.apartment_id) {
    return [];
  }
  return plans.value.filter(plan => {
    return !plan.apartment_id || plan.apartment_id === formData.apartment_id;
  });
});

const handleApartmentChange = async () => {
  formData.plan_id = 0;
  await loadPlansForApartment();
};

const monthlyFees = computed(() => {
  if (!detailData.value || !detailData.value.activate_date || !detailData.value.expire_date || !detailData.value.plan_price) {
    return [];
  }

  const fees = [];
  const activateDate = new Date(detailData.value.activate_date);
  const expireDate = new Date(detailData.value.expire_date);
  const monthlyPrice = parseFloat(detailData.value.plan_price);

  let currentYear = activateDate.getFullYear();
  let currentMonth = activateDate.getMonth() + 1;

  const today = new Date();
  let monthIndex = 1;

  while (true) {
    const monthStartDate = new Date(currentYear, currentMonth - 1, 1);
    const monthEndDate = new Date(currentYear, currentMonth, 0);

    if (monthStartDate > expireDate) {
      break;
    }

    const monthStr = `${currentYear}年${currentMonth}月`;
    const daysInMonth = monthEndDate.getDate();

    let actualStartDate = monthStartDate;
    let actualEndDate = monthEndDate;
    let isFirstMonth = false;
    let isTrial = false;
    let amount = monthlyPrice;

    if (monthIndex === 1) {
      isFirstMonth = true;
      actualStartDate = new Date(activateDate);
      const activateDay = activateDate.getDate();
      const monthLastDay = daysInMonth;
      const daysUntilMonthEnd = monthLastDay - activateDay + 1;

      if (daysUntilMonthEnd < 26) {
        isTrial = true;
        amount = 0;
      }

      if (actualEndDate > expireDate) {
        actualEndDate = new Date(expireDate);
      }
    } else {
      const isLastMonth = currentYear === expireDate.getFullYear() && currentMonth === expireDate.getMonth() + 1;
      if (isLastMonth) {
        actualEndDate = new Date(expireDate);
        const expireDay = expireDate.getDate();
        if (expireDay < 26) {
          isTrial = true;
          amount = 0;
        }
      }
    }

    const isPast = actualEndDate < today;
    const isCurrent = actualStartDate <= today && actualEndDate >= today;

    fees.push({
      month: monthStr,
      startDate: formatDate(actualStartDate),
      endDate: formatDate(actualEndDate),
      days: actualEndDate.getDate(),
      amount: amount.toFixed(2),
      isTrial,
      isFirstMonth,
      isPast,
      isCurrent
    });

    currentMonth++;
    if (currentMonth > 12) {
      currentMonth = 1;
      currentYear++;
    }
    monthIndex++;
  }

  return fees;
});

const totalFee = computed(() => {
  if (!monthlyFees.value.length) return '0.00';
  const total = monthlyFees.value.reduce((sum, fee) => sum + parseFloat(fee.amount), 0);
  return total.toFixed(2);
});

const formatDate = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getStatusText = (row) => {
  if (!row.expire_date) {
    return '未开通';
  }

  const now = new Date();
  const expireDate = new Date(row.expire_date);
  const oneMonthLater = new Date(now);
  oneMonthLater.setMonth(oneMonthLater.getMonth() + 1);

  if (expireDate <= now) {
    return '已过期';
  } else if (expireDate <= oneMonthLater) {
    return '即将到期';
  } else {
    return '已开通';
  }
};

const getStatusType = (row) => {
  if (!row.expire_date) {
    return 'info';
  }

  const now = new Date();
  const expireDate = new Date(row.expire_date);
  const oneMonthLater = new Date(now);
  oneMonthLater.setMonth(oneMonthLater.getMonth() + 1);

  if (expireDate <= now) {
    return 'danger';
  } else if (expireDate <= oneMonthLater) {
    return 'warning';
  } else {
    return 'success';
  }
};

const loadPlansForApartment = async () => {
  try {
    const params = { status: 'active' };
    if (formData.apartment_id) {
      params.apartment_id = formData.apartment_id;
    }
    const res = await getAllPlans(params);
    if (res.code === 200) {
      plans.value = res.data || [];
    }
  } catch (error) {
    console.error('加载套餐列表失败:', error);
  }
};

const calculateExpireDate = (activateDate) => {
  if (!activateDate) return;

  const date = new Date(activateDate);
  date.setMonth(date.getMonth() + 1);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  formData.expire_date = `${year}-${month}-${day}`;
};

const calculateExpireDateByMonths = () => {
  if (!formData.activate_date || !formData.months) {
    formData.expire_date = '';
    return;
  }

  const date = new Date(formData.activate_date);
  date.setMonth(date.getMonth() + formData.months);
  date.setDate(date.getDate() - 1);

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  formData.expire_date = `${year}-${month}-${day}`;
};

const dialogVisible = ref(false);
const dialogTitle = ref('新建用户');
const isEdit = ref(false);
const formRef = ref(null);
const submitLoading = ref(false);
const formData = reactive({
  _id: null,
  username: '',
  password: '',
  name: '',
  phone: '',
  room: '',
  apartment_id: '',
  plan_id: 0,
  activate_date: '',
  expire_date: '',
  months: 1
});

const formRules = {
  username: [{ required: true, message: '请输入上网账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  apartment_id: [{ required: true, message: '请选择公寓', trigger: 'change' }]
};

const detailVisible = ref(false);
const detailData = ref(null);
const showPassword = ref(false);

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

watch(detailVisible, (newVal) => {
  if (!newVal) {
    showPassword.value = false;
  }
});

const importDialogVisible = ref(false);
const importLoading = ref(false);
const uploadRef = ref(null);
const importFile = ref(null);

onMounted(() => {
  loadData();
  loadApartments().then(() => {
    // 如果是非管理员，自动选择自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'
    if (!isAdmin && apartments.value.length > 0) {
      searchForm.apartment_id = apartments.value[0].id
    }
  })
  loadPlans()
});

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

    const res = await getNetworkUsers(params);
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

const loadApartments = async () => {
  try {
    // 如果是管理员，加载所有公寓；否则只加载自己关联的公寓
    const isAdmin = localStorage.getItem('role') === 'admin'

    if (isAdmin) {
      const res = await getApartments({ page: 1, page_size: 100, status: 'active' });
      if (res.code === 200) {
        apartments.value = res.data || [];
      }
    } else {
      // 非管理员只能看到自己关联的公寓
      const storedApartments = localStorage.getItem('apartments')
      apartments.value = storedApartments ? JSON.parse(storedApartments) : []
    }
  } catch (error) {
    console.error('加载公寓列表失败:', error);
  }
};

const loadPlans = async () => {
  try {
    const res = await getAllPlans({ status: 'active' });
    if (res.code === 200) {
      plans.value = res.data || [];
    }
  } catch (error) {
    console.error('加载套餐列表失败:', error);
  }
};

const resetSearch = () => {
  searchForm.keyword = '';
  searchForm.status = '';
  searchForm.apartment_id = '';
  searchForm.plan_id = '';
  pagination.page = 1;
  loadData();
};

const handleCreate = () => {
  isEdit.value = false;
  dialogTitle.value = '新建用户';
  resetFormData();
  loadPlansForApartment();
  dialogVisible.value = true;
};

const handleEdit = async (row) => {
  isEdit.value = true;
  dialogTitle.value = '开通设置';
  formData._id = row.id;
  formData.username = row.username;
  formData.password = '';
  formData.name = row.name || '';
  formData.phone = row.phone || '';
  formData.room = row.room || '';
  formData.apartment_id = row.apartment_id;
  formData.plan_id = row.plan_id || 0;

  const now = new Date();
  formData.activate_date = formatDate(now);
  formData.months = 1;
  formData.expire_date = '';

  await loadPlansForApartment();
  dialogVisible.value = true;
};

const handleDetail = async (row) => {
  try {
    const res = await getNetworkUserDetail(row.id);
    if (res.code === 200) {
      detailData.value = res.data;
      detailVisible.value = true;
    }
  } catch (error) {
    console.error('获取详情失败:', error);
    ElMessage.error('获取详情失败');
  }
};

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    submitLoading.value = true;

    const data = {
      ...formData
    };
    if (data.plan_id === 0) {
      data.plan_id = null;
    }

    if (isEdit.value) {
      const updateData = {
        plan_id: data.plan_id,
        activate_date: data.activate_date,
        expire_date: data.expire_date
      };
      await updateNetworkUser(formData._id, updateData);
      ElMessage.success('开通设置成功');
    } else {
      await createNetworkUser(data);
      ElMessage.success('创建成功');
    }

    dialogVisible.value = false;
    loadData();
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error);
      ElMessage.error(error.response?.data?.detail || '操作失败');
    }
  } finally {
    submitLoading.value = false;
  }
};

const handleDeactivate = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要停用用户"${row.username}"吗？停用后将清空开通日期和到期日期。`,
      '停用确认',
      { type: 'warning' }
    );

    await deactivateNetworkUser(row.id);
    ElMessage.success('停用成功');
    loadData();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停用失败:', error);
      ElMessage.error(error.response?.data?.detail || '停用失败');
    }
  }
};

const handleBatchDeactivate = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请先选择要停用的用户');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要停用选中的 ${selectedUsers.value.length} 个用户吗？停用后将清空开通日期和到期日期。`,
      '批量停用确认',
      { type: 'warning' }
    );

    const deactivatePromises = selectedUsers.value.map(user =>
      deactivateNetworkUser(user.id)
    );

    await Promise.all(deactivatePromises);
    ElMessage.success(`成功停用 ${selectedUsers.value.length} 个用户`);
    selectedUsers.value = [];
    loadData();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量停用失败:', error);
      ElMessage.error(error.response?.data?.detail || '批量停用失败');
    }
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户"${row.username}"吗？此操作不可恢复！`,
      '删除确认',
      { type: 'error' }
    );
    await deleteNetworkUser(row.id);
    ElMessage.success('删除成功');
    loadData();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error);
      ElMessage.error(error.response?.data?.detail || '删除失败');
    }
  }
};

const handleExport = async () => {
  try {
    const params = { ...searchForm };
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key];
      }
    });

    const res = await exportNetworkUsers(params);

    const blob = new Blob([res], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `network_users_${new Date().getTime()}.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);

    ElMessage.success('导出成功');
  } catch (error) {
    console.error('导出失败:', error);
    ElMessage.error('导出失败');
  }
};

const handleImport = () => {
  importFile.value = null;
  importDialogVisible.value = true;
};

const handleFileChange = (file) => {
  importFile.value = file.raw;
};

const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning('请选择文件');
    return;
  }

  try {
    importLoading.value = true;
    const formData = new FormData();
    formData.append('file', importFile.value);

    const res = await importNetworkUsers(formData);
    if (res.code === 200) {
      ElMessage.success(`导入完成：成功${res.data.success_count}条，失败${res.data.error_count}条`);
      if (res.data.errors && res.data.errors.length > 0) {
        console.error('导入错误:', res.data.errors);
      }
      importDialogVisible.value = false;
      loadData();
    }
  } catch (error) {
    console.error('导入失败:', error);
    ElMessage.error(error.response?.data?.detail || '导入失败');
  } finally {
    importLoading.value = false;
  }
};

const handleDialogClose = () => {
  formRef.value?.resetFields();
  resetFormData();
};

const resetFormData = () => {
  formData._id = null;
  formData.username = '';
  formData.password = '';
  formData.name = '';
  formData.phone = '';
  formData.room = '';
  formData.apartment_id = '';
  formData.plan_id = 0;
  formData.activate_date = '';
  formData.expire_date = '';
  formData.months = 1;
};

// 报障相关
const faultDialogVisible = ref(false);
const faultSubmitLoading = ref(false);
const faultForm = reactive({
  user_id: null,
  username: '',
  reporter_name: '',
  reporter_phone: '',
  fault_type: '',
  description: ''
});

const handleReportFault = (row) => {
  faultForm.user_id = row.id;
  faultForm.username = row.username;
  faultForm.reporter_name = row.name || '';
  faultForm.reporter_phone = row.phone || '';
  faultForm.fault_type = '';
  faultForm.description = '';
  faultDialogVisible.value = true;
};

const handleFaultSubmit = async () => {
  if (!faultForm.fault_type) {
    ElMessage.warning('请选择故障类型');
    return;
  }

  try {
    faultSubmitLoading.value = true;
    await createFaultReport({
      user_id: faultForm.user_id,
      fault_type: faultForm.fault_type,
      description: faultForm.description,
      reporter_name: faultForm.reporter_name,
      reporter_phone: faultForm.reporter_phone
    });
    ElMessage.success('故障报告已提交');
    faultDialogVisible.value = false;
  } catch (error) {
    console.error('提交故障报告失败:', error);
    ElMessage.error(error.response?.data?.detail || '提交失败');
  } finally {
    faultSubmitLoading.value = false;
  }
};
</script>

<style scoped>
.network-user-container {
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

.actions {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
}

.import-tips {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 10px;
}

.import-tips p {
  margin: 0 0 10px 0;
  color: #606266;
}

.import-tips ul {
  margin: 0;
  padding-left: 20px;
  color: #909399;
}

.import-tips li {
  margin-bottom: 5px;
}
</style>
