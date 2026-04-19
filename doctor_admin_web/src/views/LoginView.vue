<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { adminLogin } from '../api'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '13800138000',
  password: 'admin123',
})

async function submit() {
  loading.value = true
  try {
    const res = await adminLogin(form.username, form.password)
    localStorage.setItem('eh_admin_token', res.token)
    ElMessage.success('登录成功')
    router.push('/reminders')
  } catch {
    ElMessage.error('登录失败，请检查账号或后端服务')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>医生管理端登录</h2>
      <el-form label-position="top">
        <el-form-item label="手机号">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-button type="primary" :loading="loading" class="w-full" @click="submit">登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>
