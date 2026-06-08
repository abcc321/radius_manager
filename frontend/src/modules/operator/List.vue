<template>
  <div class="page-container">
    <el-card>
      <template #header>
        <div class="page-header">
          <span class="page-title">操作员管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增操作员
          </el-button>
        </div>
      </template>

      <div class="search-form responsive-search-form">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="关键词" class="hide-on-mobile">
            <el-input
              v-model="searchForm.keyword"
              placeholder="用户名/姓名"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>
          <el-form-item label="角色" class="hide-on-mobile">
            <el-select v-model="searchForm.role" placeholder="角色" clearable>
              <el-option label="管理员" value="admin" />
              <el-option label="操作员" value="operator" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态" class="hide-on-mobile">
            <el-select v-model="searchForm.status" placeholder="状态" clearable>
              <el-option label="正常" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <el-icon><Search /></el-icon>
              查询
            </el-button>
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="table-responsive-wrapper">
        <el-table :data="tableData" v-loading="loading" stripe>
          <el-table-column prop="username" label="用户名" width="100" />
          <el-table-column prop="name" label="姓名" width="100" />
          <el-table-column prop="role" label="角色" width="80">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'" size="small">
                {{ row.role === "admin" ? "管理员" : "操作员" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="70">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                {{ row.status === "active" ? "正常" : "禁用" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="公寓" min-width="120" class-name="hide-on-tablet">
            <template #default="{ row }">
              <span v-if="row.apartment_ids && row.apartment_ids.length > 0">
                {{ row.apartment_ids.length }} 个公寓
              </span>
              <span v-else style="color: #999;">未分配</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="140" class-name="hide-on-mobile">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button link type="success" size="small" @click="handleAssignApartments(row)">分配</el-button>
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
      width="500px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :disabled="isEdit"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">正常</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="apartmentDialogVisible"
      title="分配公寓权限"
      width="600px"
      @close="handleApartmentDialogClose"
    >
      <div v-loading="apartmentLoading" style="min-height: 200px;">
        <div style="margin-bottom: 20px;">
          <p style="color: #666; margin-bottom: 10px;">
            为操作员 "<strong>{{ currentOperatorName }}</strong>" 分配可访问的公寓
          </p>
          <el-checkbox
            v-model="checkAllApartments"
            :indeterminate="isIndeterminate"
            @change="handleCheckAllChange"
          >
            全选
          </el-checkbox>
        </div>
        <el-checkbox-group v-model="selectedApartmentIds">
          <el-checkbox
            v-for="apt in apartmentList"
            :key="apt.id"
            :label="apt.id"
            :value="apt.id"
            style="display: block; margin-bottom: 10px; margin-left: 0;"
          >
            {{ apt.name }} ({{ apt.code }})
          </el-checkbox>
        </el-checkbox-group>
        <div v-if="!apartmentLoading && apartmentList.length === 0" style="color: #999; text-align: center; padding: 40px 0;">
          暂无可分配的公寓，请先创建公寓
        </div>
      </div>
      <template #footer>
        <el-button @click="apartmentDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleAssignSubmit">
          确定分配
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="400px"
      @close="handlePasswordDialogClose"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="80px"
      >
        <el-form-item label="原密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handlePasswordSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatDate } from "@/common/utils";
import {
  getOperators,
  createOperator,
  updateOperator,
  deleteOperator,
  changePassword,
  assignApartments,
  getApartments
} from "./api";

const loading = ref(false);
const tableData = ref([]);
const dialogVisible = ref(false);
const passwordDialogVisible = ref(false);
const apartmentDialogVisible = ref(false);
const submitLoading = ref(false);
const apartmentLoading = ref(false);
const formRef = ref();
const passwordFormRef = ref();
const currentOperatorId = ref(null);
const currentOperatorName = ref("");
const apartmentList = ref([]);
const selectedApartmentIds = ref([]);

const isEdit = computed(() => !!currentOperatorId.value);
const dialogTitle = computed(() => isEdit.value ? "编辑操作员" : "新增操作员");

const checkAllApartments = computed({
  get: () => selectedApartmentIds.value.length === apartmentList.value.length && apartmentList.value.length > 0,
  set: (val) => {
    selectedApartmentIds.value = val ? apartmentList.value.map((apt) => apt.id) : [];
  }
});

const isIndeterminate = computed(() => {
  return selectedApartmentIds.value.length > 0 && selectedApartmentIds.value.length < apartmentList.value.length;
});

const searchForm = reactive({
  keyword: "",
  role: "",
  status: ""
});

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
});

const form = reactive({
  username: "",
  name: "",
  role: "operator",
  password: "",
  status: "active",
  apartment_ids: []
});

const formRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于6位", trigger: "blur" }
  ]
};

const passwordForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: ""
});

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const passwordFormRules = {
  old_password: [{ required: true, message: "请输入原密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于6位", trigger: "blur" }
  ],
  confirm_password: [
    { required: true, message: "请再次输入新密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" }
  ]
};

const loadData = async () => {
  loading.value = true;
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...searchForm
    };
    const res = await getOperators(params);
    tableData.value = res.data || [];
    pagination.total = res.total || 0;
  } catch (error) {
    console.error("加载数据失败:", error);
  } finally {
    loading.value = false;
  }
};

const loadApartments = async () => {
  const res = await getApartments({ page: 1, page_size: 100 });
  apartmentList.value = res.data || [];
  return apartmentList.value;
};

const handleSearch = () => {
  pagination.page = 1;
  loadData();
};

const handleReset = () => {
  searchForm.keyword = "";
  searchForm.role = "";
  searchForm.status = "";
  handleSearch();
};

const handleCreate = () => {
  currentOperatorId.value = null;
  Object.assign(form, {
    username: "",
    name: "",
    role: "operator",
    password: "",
    status: "active",
    apartment_ids: []
  });
  dialogVisible.value = true;
};

const handleEdit = (row) => {
  currentOperatorId.value = row.id;
  Object.assign(form, {
    username: row.username,
    name: row.name,
    role: row.role,
    password: "",
    status: row.status,
    apartment_ids: row.apartment_ids || []
  });
  dialogVisible.value = true;
};

const handleDialogClose = () => {
  formRef.value?.resetFields();
};

const handleSubmit = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        if (isEdit.value) {
          await updateOperator(currentOperatorId.value, {
            name: form.name,
            role: form.role,
            status: form.status
          });
          ElMessage.success("更新成功");
        } else {
          await createOperator(form);
          ElMessage.success("创建成功");
        }
        dialogVisible.value = false;
        loadData();
      } catch (error) {
        console.error("提交失败:", error);
        ElMessage.error(error.response?.data?.detail || "操作失败，请重试");
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

const handleAssignApartments = async (row) => {
  currentOperatorId.value = row.id;
  currentOperatorName.value = row.username;
  selectedApartmentIds.value = row.apartment_ids || [];
  apartmentDialogVisible.value = true;
  apartmentLoading.value = true;

  try {
    await loadApartments();
  } catch (error) {
    console.error("加载公寓列表失败:", error);
    ElMessage.error("加载公寓列表失败，请重试");
    apartmentDialogVisible.value = false;
  } finally {
    apartmentLoading.value = false;
  }
};

const handleApartmentDialogClose = () => {
  selectedApartmentIds.value = [];
  currentOperatorName.value = "";
  currentOperatorId.value = null;
};

const handleCheckAllChange = (val) => {
  selectedApartmentIds.value = val ? apartmentList.value.map((apt) => apt.id) : [];
};

const handleAssignSubmit = async () => {
  if (!currentOperatorId.value) return;

  submitLoading.value = true;
  try {
    await assignApartments(currentOperatorId.value, {
      apartment_ids: selectedApartmentIds.value
    });
    ElMessage.success("公寓分配成功");
    apartmentDialogVisible.value = false;
    loadData();
  } catch (error) {
    console.error("分配失败:", error);
    ElMessage.error(error.response?.data?.detail || "分配失败，请重试");
  } finally {
    submitLoading.value = false;
  }
};

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除操作员"${row.username}"吗？`,
      "提示",
      { type: "warning" }
    );
    await deleteOperator(row.id);
    ElMessage.success("删除成功");
    loadData();
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

const handleChangePassword = (row) => {
  currentOperatorId.value = row.id;
  Object.assign(passwordForm, {
    old_password: "",
    new_password: "",
    confirm_password: ""
  });
  passwordDialogVisible.value = true;
};

const handlePasswordDialogClose = () => {
  passwordFormRef.value?.resetFields();
};

const handlePasswordSubmit = async () => {
  if (!passwordFormRef.value) return;

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      try {
        await changePassword(currentOperatorId.value, {
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password
        });
        ElMessage.success("密码修改成功");
        passwordDialogVisible.value = false;
      } catch (error) {
        console.error("修改密码失败:", error);
        ElMessage.error(error.response?.data?.detail || "修改密码失败");
      } finally {
        submitLoading.value = false;
      }
    }
  });
};

onMounted(() => {
  loadData();
});
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
</style>
