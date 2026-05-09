<template>
  <div class="register-container">
    <div class="background-grid">
      <div class="grid-line" v-for="i in 20" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
    </div>

    <div class="particles">
      <div class="particle" v-for="i in 10" :key="`p-${i}`" :style="particleStyle(i)"></div>
    </div>

    <div class="register-card">
      <div class="back-link">
        <NuxtLink to="/" class="back-btn">
          <span>←</span>
          <span>返回登录</span>
        </NuxtLink>
      </div>

      <div class="card-header">
        <div class="icon-wrapper">📝</div>
        <h1 class="card-title">申请账号</h1>
        <p class="card-subtitle">填写以下信息申请 MiniHES 系统账号</p>
      </div>

      <form class="register-form" @submit.prevent="handleSubmit">
        <div class="form-row">
          <div class="input-group" :class="{ 'has-error': errors.name }">
            <label class="input-label" for="name">姓名</label>
            <input
              id="name"
              v-model="form.name"
              type="text"
              class="input-field"
              :class="{ 'error': errors.name }"
              placeholder="您的姓名"
              :disabled="isLoading"
            />
            <p v-if="errors.name" class="input-error">{{ errors.name }}</p>
          </div>

          <div class="input-group" :class="{ 'has-error': errors.email }">
            <label class="input-label" for="email">邮箱</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="input-field"
              :class="{ 'error': errors.email }"
              placeholder="your@email.com"
              :disabled="isLoading"
            />
            <p v-if="errors.email" class="input-error">{{ errors.email }}</p>
          </div>
        </div>

        <div class="input-group" :class="{ 'has-error': errors.company }">
          <label class="input-label" for="company">公司名称</label>
          <input
            id="company"
            v-model="form.company"
            type="text"
            class="input-field"
            :class="{ 'error': errors.company }"
            placeholder="请输入公司名称"
            :disabled="isLoading"
          />
          <p v-if="errors.company" class="input-error">{{ errors.company }}</p>
        </div>

        <div class="input-group" :class="{ 'has-error': errors.password }">
          <label class="input-label" for="password">密码</label>
          <div class="input-wrapper">
            <input
              id="password"
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="input-field"
              :class="{ 'error': errors.password }"
              placeholder="至少8位字符"
              :disabled="isLoading"
            />
            <button type="button" class="password-toggle" @click="showPassword = !showPassword">
              {{ showPassword ? '👁' : '👁‍🗨' }}
            </button>
          </div>
          <div v-if="form.password && !errors.password" class="password-strength">
            <div class="strength-bar">
              <div class="strength-fill" :class="strengthClass" :style="{ width: `${strengthPercentage}%` }"></div>
            </div>
            <span class="strength-text" :class="strengthClass">{{ strengthText }}</span>
          </div>
          <p v-if="errors.password" class="input-error">{{ errors.password }}</p>
        </div>

        <div class="input-group" :class="{ 'has-error': errors.confirmPassword }">
          <label class="input-label" for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            class="input-field"
            :class="{ 'error': errors.confirmPassword }"
            placeholder="再次输入密码"
            :disabled="isLoading"
          />
          <p v-if="errors.confirmPassword" class="input-error">{{ errors.confirmPassword }}</p>
        </div>

        <div class="input-group" :class="{ 'has-error': errors.reason }">
          <label class="input-label" for="reason">申请理由</label>
          <textarea
            id="reason"
            v-model="form.reason"
            class="input-field textarea"
            :class="{ 'error': errors.reason }"
            placeholder="请说明申请账号的原因..."
            rows="3"
            :disabled="isLoading"
          ></textarea>
          <p v-if="errors.reason" class="input-error">{{ errors.reason }}</p>
        </div>

        <div class="checkbox-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.agree" class="checkbox" :disabled="isLoading"/>
            <span>我已阅读并同意 <a href="#" class="link">服务条款</a> 和 <a href="#" class="link">隐私政策</a></span>
          </label>
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading || !form.agree" :class="{ 'loading': isLoading }">
          <span v-if="!isLoading">提交申请</span>
          <span v-else>提交中...</span>
        </button>
      </form>

      <Transition name="fade">
        <div v-if="submitted" class="success-message">
          <span class="success-icon">✓</span>
          <p>申请已提交</p>
          <span class="success-text">我们将在1-2个工作日内审核您的申请</span>
        </div>
      </Transition>

      <div class="card-footer">
        <p>已有账号？<NuxtLink to="/">立即登录</NuxtLink></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  auth: false
})

interface RegisterForm {
  name: string
  email: string
  company: string
  password: string
  confirmPassword: string
  reason: string
  agree: boolean
}

const form = reactive<RegisterForm>({
  name: '',
  email: '',
  company: '',
  password: '',
  confirmPassword: '',
  reason: '',
  agree: false
})

const errors = reactive<Partial<Record<keyof RegisterForm, string>>>({})
const isLoading = ref(false)
const submitted = ref(false)
const showPassword = ref(false)
const passwordStrength = ref(0)

const strengthPercentage = computed(() => (passwordStrength.value / 4) * 100)
const strengthClass = computed(() => {
  const level = passwordStrength.value
  if (level <= 1) return 'weak'
  if (level === 2) return 'fair'
  if (level === 3) return 'good'
  return 'strong'
})
const strengthText = computed(() => {
  const level = passwordStrength.value
  if (level <= 1) return '弱'
  if (level === 2) return '一般'
  if (level === 3) return '良好'
  return '强'
})

const validateForm = (): boolean => {
  let isValid = true

  if (!form.name) {
    errors.name = '请输入姓名'
    isValid = false
  } else errors.name = ''

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email) {
    errors.email = '请输入邮箱'
    isValid = false
  } else if (!emailRegex.test(form.email)) {
    errors.email = '请输入有效的邮箱'
    isValid = false
  } else errors.email = ''

  if (!form.company) {
    errors.company = '请输入公司名称'
    isValid = false
  } else errors.company = ''

  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 8) {
    errors.password = '密码至少需要8位字符'
    isValid = false
  } else errors.password = ''

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
    isValid = false
  } else errors.confirmPassword = ''

  if (!form.reason) {
    errors.reason = '请填写申请理由'
    isValid = false
  } else errors.reason = ''

  return isValid
}

const calculatePasswordStrength = (password: string): number => {
  let strength = 0
  if (password.length >= 8) strength++
  if (password.length >= 12) strength++
  if (/[a-z]/.test(password)) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/\d/.test(password)) strength++
  if (/[^a-zA-Z0-9]/.test(password)) strength++
  return Math.min(strength, 4)
}

watch(() => form.password, (newPwd) => {
  if (newPwd) {
    passwordStrength.value = calculatePasswordStrength(newPwd)
    errors.password = ''
  }
})

const handleSubmit = async () => {
  if (!validateForm()) return

  isLoading.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  submitted.value = true
  isLoading.value = false
}

const particleStyle = (index: number) => ({
  left: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 5}s`,
  animationDuration: `${5 + Math.random() * 10}s`
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
  --color-primary: #10B981;
  --color-primary-dark: #059669;
  --color-bg: #0F172A;
  --color-bg-light: #1E293B;
  --color-text: #E2E8F0;
  --color-text-muted: #94A3B8;
  --color-border: #334155;
  --color-error: #EF4444;
  --color-glow: rgba(16, 185, 129, 0.5);
}

.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow-y: auto;
  background: var(--color-bg);
  font-family: 'Noto Sans SC', sans-serif;
  isolation: isolate;
  padding: 20px 0;
}

.background-grid {
  position: fixed;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(20, 1fr);
  opacity: 0.1;
  z-index: 1;
  pointer-events: none;
}

.grid-line {
  background: linear-gradient(to bottom, transparent, var(--color-primary), transparent);
  animation: gridPulse 3s ease-in-out infinite;
}

@keyframes gridPulse {
  0%, 100% { opacity: 0.1; }
  50% { opacity: 0.3; }
}

.particles {
  position: fixed;
  inset: 0;
  z-index: 2;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: float linear infinite;
  box-shadow: 0 0 10px var(--color-glow);
}

@keyframes float {
  0% { transform: translateY(100vh) scale(0); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(-10vh) scale(1); opacity: 0; }
}

.register-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 480px;
  padding: 40px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 24px;
  backdrop-filter: blur(20px);
  box-shadow: 0 0 60px rgba(16, 185, 129, 0.1);
  animation: cardFadeIn 0.5s ease-out;
}

@keyframes cardFadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.back-link {
  margin-bottom: 24px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 13px;
  transition: color 0.3s ease;
}

.back-btn:hover {
  color: var(--color-primary);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 50%;
  font-size: 28px;
}

.card-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 8px 0;
}

.card-subtitle {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
}

.register-form {
  margin-bottom: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.input-group {
  margin-bottom: 16px;
}

.input-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.input-field {
  width: 100%;
  padding: 12px 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text);
  font-size: 14px;
  transition: all 0.3s ease;
  font-family: inherit;
}

.input-field:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.input-field.error {
  border-color: var(--color-error);
}

.input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-field.textarea {
  resize: vertical;
  min-height: 80px;
}

.input-wrapper {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.5;
  transition: opacity 0.3s;
}

.password-toggle:hover {
  opacity: 1;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.strength-fill.weak { background: #EF4444; }
.strength-fill.fair { background: #F59E0B; }
.strength-fill.good { background: #10B981; }
.strength-fill.strong { background: #10B981; box-shadow: 0 0 10px rgba(16, 185, 129, 0.3); }

.strength-text {
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
}

.strength-text.weak { color: #EF4444; }
.strength-text.fair { color: #F59E0B; }
.strength-text.good { color: #10B981; }
.strength-text.strong { color: #10B981; }

.input-error {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-error);
}

.input-error::before {
  content: '⚠';
}

.checkbox-group {
  margin-bottom: 20px;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-muted);
}

.checkbox-label input[type="checkbox"] {
  margin-top: 2px;
}

.link {
  color: var(--color-primary);
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}

.submit-btn {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  text-align: center;
}

.success-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  font-size: 24px;
}

.success-message p {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text);
  margin: 0;
}

.success-text {
  font-size: 13px;
  color: var(--color-text-muted);
}

.card-footer {
  text-align: center;
  padding-top: 24px;
  border-top: 1px solid rgba(51, 65, 85, 0.5);
}

.card-footer p {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.card-footer a {
  color: var(--color-primary);
  text-decoration: none;
}

.card-footer a:hover {
  text-decoration: underline;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 640px) {
  .register-card {
    margin: 16px;
    padding: 24px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
