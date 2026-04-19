<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReminders, handleReminder } from '../api'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const query = reactive({ status: 'open', type: '', q: '', page: 1, pageSize: 10 })
const dialogVisible = ref(false)
const currentTaskId = ref<number | null>(null)
const handleForm = reactive({ action: 'notify', channel: 'phone', note: '' })

async function loadData() {
  if (query.page < 1) query.page = 1
  loading.value = true
  try {
    const res = await getReminders(query)
    rows.value = res.data.items || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function openHandle(id: number) {
  currentTaskId.value = id
  dialogVisible.value = true
}

async function submitHandle() {
  if (!currentTaskId.value) return
  await handleReminder(currentTaskId.value, handleForm)
  dialogVisible.value = false
  ElMessage.success('处理完成')
  loadData()
}

function doSearch() {
  query.page = 1
  loadData()
}

function handlePageChange(page: number) {
  query.page = page > 0 ? page : 1
  loadData()
}

onMounted(loadData)
</script>

<template>
  <el-card>
    <template #header>
      <div class="toolbar">
        <span>未体检待办</span>
        <div class="toolbar-right">
          <el-select v-model="query.status" placeholder="状态" style="width: 140px">
            <el-option value="open" label="待处理" />
            <el-option value="done" label="已处理" />
          </el-select>
          <el-select v-model="query.type" clearable placeholder="类型" style="width: 160px">
            <el-option value="NO_EXAM_3M" label="3个月未体检" />
            <el-option value="NO_EXAM_6M" label="6个月未体检" />
          </el-select>
          <el-input v-model="query.q" placeholder="用户关键词" style="width: 180px" />
          <el-button type="primary" @click="doSearch">筛选</el-button>
        </div>
      </div>
    </template>
    <el-table v-loading="loading" :data="rows" border>
      <el-table-column prop="id" label="任务ID" width="90" />
      <el-table-column prop="userId" label="用户ID" width="100" />
      <el-table-column prop="type" label="类型" />
      <el-table-column prop="status" label="状态" width="100" />
      <el-table-column label="操作" width="130">
        <template #default="{ row }">
          <el-button type="primary" link @click="openHandle(row.id)">处理</el-button>
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

  <el-dialog v-model="dialogVisible" title="处理待办" width="480px">
    <el-form label-position="top">
      <el-form-item label="动作">
        <el-select v-model="handleForm.action">
          <el-option value="notify" label="通知" />
          <el-option value="call" label="电话" />
          <el-option value="done" label="已处理" />
          <el-option value="other" label="其他" />
        </el-select>
      </el-form-item>
      <el-form-item label="渠道">
        <el-select v-model="handleForm.channel">
          <el-option value="phone" label="电话" />
          <el-option value="inapp" label="站内" />
          <el-option value="wechat_subscribe" label="订阅消息" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="handleForm.note" type="textarea" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitHandle">提交</el-button>
    </template>
  </el-dialog>
</template>
