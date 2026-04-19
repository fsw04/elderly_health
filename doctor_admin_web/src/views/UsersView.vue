<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { createUser, deleteUser, getUserDetail, getUserReminders, getUserReports, getUserSessions, getUsers, updateUser } from '../api'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const query = reactive({ q: '', page: 1, pageSize: 10 })
const dialogVisible = ref(false)
const isEdit = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detailUser = ref<any>(null)
const detailSessions = ref<any[]>([])
const detailReports = ref<any[]>([])
const detailReminders = ref<any[]>([])
const form = reactive({
  id: 0,
  phone: '',
  name: '',
  gender: 'U',
  birthDate: '',
  idCard: '',
  currentAddress: '',
})

function normalizeBirthDate(value: string | null | undefined) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (/^\d{8}$/.test(raw)) return raw
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw.replaceAll('-', '')
  return raw
}

function displayBirthDate(value: string | null | undefined) {
  const v = normalizeBirthDate(value)
  if (/^\d{8}$/.test(v)) {
    return `${v.slice(0, 4)}-${v.slice(4, 6)}-${v.slice(6, 8)}`
  }
  return v || '--'
}

function isValidYmd(value: string) {
  if (!/^\d{8}$/.test(value)) return false
  const year = Number(value.slice(0, 4))
  const month = Number(value.slice(4, 6))
  const day = Number(value.slice(6, 8))
  const dt = new Date(year, month - 1, day)
  return dt.getFullYear() === year && dt.getMonth() === month - 1 && dt.getDate() === day
}

async function loadData() {
  if (query.page < 1) query.page = 1
  loading.value = true
  try {
    const res = await getUsers(query)
    rows.value = res.data.items || []
    total.value = res.data.total || 0
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '用户列表加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

function doSearch() {
  query.page = 1
  loadData()
}

function handlePageChange(page: number) {
  query.page = page > 0 ? page : 1
  loadData()
}

function openCreate() {
  isEdit.value = false
  form.id = 0
  form.phone = ''
  form.name = ''
  form.gender = 'U'
  form.birthDate = ''
  form.idCard = ''
  form.currentAddress = ''
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true
  form.id = row.id
  form.phone = row.phone || ''
  form.name = row.name || ''
  form.gender = row.gender || 'U'
  form.birthDate = normalizeBirthDate(row.birthDate)
  form.idCard = row.idCard || ''
  form.currentAddress = row.currentAddress || ''
  dialogVisible.value = true
}

async function saveUser() {
  if (!/^\d{11}$/.test(form.phone)) {
    ElMessage.error('手机号必须是11位数字')
    return
  }
  if (form.birthDate && !isValidYmd(form.birthDate)) {
    ElMessage.error('出生日期格式应为YYYYMMDD（请优先用日期选择器）')
    return
  }
  if (form.idCard && !/^(\d{15}|\d{17}[\dXx])$/.test(form.idCard)) {
    ElMessage.error('证件号格式不正确')
    return
  }
  const payload = {
    phone: form.phone,
    name: form.name,
    gender: form.gender,
    birthDate: form.birthDate || null,
    idCard: form.idCard || null,
    currentAddress: form.currentAddress || null,
  }
  try {
    if (isEdit.value) {
      await updateUser(form.id, payload)
      ElMessage.success('用户已更新')
    } else {
      await createUser(payload)
      ElMessage.success('用户已创建')
    }
    dialogVisible.value = false
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function removeUser(id: number) {
  try {
    await ElMessageBox.confirm('确认删除该用户？', '提示', { type: 'warning' })
    await deleteUser(id)
    ElMessage.success('已删除')
    loadData()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.detail || '删除失败')
    }
  }
}

async function openDetail(id: number) {
  detailVisible.value = true
  detailLoading.value = true
  try {
    const [uRes, sRes, rRes, mRes] = await Promise.all([
      getUserDetail(id),
      getUserSessions(id, { page: 1, pageSize: 20 }),
      getUserReports(id, { page: 1, pageSize: 20 }),
      getUserReminders(id, { page: 1, pageSize: 20 }),
    ])
    detailUser.value = uRes.data
    detailSessions.value = sRes.data.items || []
    detailReports.value = rRes.data.items || []
    detailReminders.value = mRes.data.items || []
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '详情加载失败')
  } finally {
    detailLoading.value = false
  }
}
</script>

<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>用户管理</span>
        <div class="toolbar-right">
          <el-input v-model="query.q" placeholder="姓名/手机号/证件号/现住址" style="width: 300px" />
          <el-button type="primary" @click="doSearch">搜索</el-button>
          <el-button type="success" @click="openCreate">新增用户</el-button>
        </div>
      </div>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column prop="idCard" label="证件号" min-width="180" />
      <el-table-column prop="age" label="年龄" width="90" />
      <el-table-column prop="currentAddress" label="现住址" min-width="220" />
      <el-table-column prop="gender" label="性别" width="100" />
      <el-table-column label="生日">
        <template #default="{ row }">
          {{ displayBirthDate(row.birthDate) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" link @click="openDetail(row.id)">详情</el-button>
          <el-button type="primary" link @click="openEdit(row)">编辑</el-button>
          <el-button type="danger" link @click="removeUser(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="query.page"
      :page-size="query.pageSize"
      :total="total"
      layout="total, prev, pager, next"
      class="pager"
      @current-change="handlePageChange"
    />
  </el-card>

  <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新增用户'" width="520px">
    <el-form label-position="top">
      <el-form-item label="手机号">
        <el-input v-model="form.phone" />
      </el-form-item>
      <el-form-item label="姓名">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="性别">
        <el-select v-model="form.gender">
          <el-option value="M" label="男" />
          <el-option value="F" label="女" />
          <el-option value="U" label="未知" />
        </el-select>
      </el-form-item>
      <el-form-item label="生日">
        <el-date-picker
          v-model="form.birthDate"
          type="date"
          format="YYYY-MM-DD"
          value-format="YYYYMMDD"
          placeholder="请选择出生日期"
        />
      </el-form-item>
      <el-form-item label="证件号">
        <el-input v-model="form.idCard" placeholder="15位或18位，末位可X" />
      </el-form-item>
      <el-form-item label="现住址">
        <el-input v-model="form.currentAddress" type="textarea" :rows="2" placeholder="请输入现住址" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveUser">保存</el-button>
    </template>
  </el-dialog>

  <el-drawer v-model="detailVisible" title="用户详情" size="50%">
    <div v-loading="detailLoading">
      <div v-if="detailUser">
        <p><b>ID：</b>{{ detailUser.id }}</p>
        <p><b>姓名：</b>{{ detailUser.name || '--' }}</p>
        <p><b>手机号：</b>{{ detailUser.phone || '--' }}</p>
        <p><b>证件号：</b>{{ detailUser.idCard || '--' }}</p>
        <p><b>生日：</b>{{ displayBirthDate(detailUser.birthDate) }}</p>
        <p><b>年龄：</b>{{ detailUser.age ?? '--' }}</p>
        <p><b>现住址：</b>{{ detailUser.currentAddress || '--' }}</p>
        <p><b>性别：</b>{{ detailUser.gender || '--' }}</p>
      </div>
      <el-divider />
      <el-tabs>
        <el-tab-pane label="会话记录">
          <el-table :data="detailSessions" border size="small">
            <el-table-column prop="id" label="会话ID" />
            <el-table-column prop="status" label="状态" width="120" />
            <el-table-column prop="startTime" label="开始时间" />
            <el-table-column prop="endTime" label="结束时间" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="报告记录">
          <el-table :data="detailReports" border size="small">
            <el-table-column prop="id" label="报告ID" />
            <el-table-column prop="riskLevel" label="风险" width="100" />
            <el-table-column prop="createdAt" label="创建时间" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="提醒记录">
          <el-table :data="detailReminders" border size="small">
            <el-table-column prop="id" label="任务ID" width="90" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="status" label="状态" width="100" />
            <el-table-column prop="handleAction" label="处理动作" />
            <el-table-column prop="createdAt" label="创建时间" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </el-drawer>
</template>
