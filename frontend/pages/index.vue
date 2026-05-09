<template>
  <div class="login-container">
    <!-- 六边形网格背景 -->
    <div class="hex-grid"></div>

    <!-- 扫描线效果 -->
    <div class="scan-line"></div>

    <!-- 数据流动画层 -->
    <svg class="data-flow-layer" viewBox="0 0 100 100" preserveAspectRatio="none">
      <path class="flow-line flow-1" d="M0,20 Q25,18 50,20 T100,20" fill="none" stroke="rgba(16,185,129,0.3)" stroke-width="0.3"/>
      <path class="flow-line flow-2" d="M0,50 Q25,52 50,50 T100,50" fill="none" stroke="rgba(59,130,246,0.3)" stroke-width="0.3"/>
      <path class="flow-line flow-3" d="M0,80 Q25,78 50,80 T100,80" fill="none" stroke="rgba(16,185,129,0.3)" stroke-width="0.3"/>
      <path class="flow-line flow-4" d="M20,0 Q18,25 20,50 T20,100" fill="none" stroke="rgba(16,185,129,0.2)" stroke-width="0.3"/>
      <path class="flow-line flow-5" d="M80,0 Q82,25 80,50 T80,100" fill="none" stroke="rgba(59,130,246,0.2)" stroke-width="0.3"/>
    </svg>

    <!-- 顶部品牌 -->
    <div class="brand-header">
      <div class="brand-logo">
        <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M24 4L8 12V24C8 33.9414 15.1608 42.9242 24 46C32.8392 42.9242 40 33.9414 40 24V12L24 4Z" stroke="currentColor" stroke-width="2"/>
          <path d="M24 16V32M24 24H32" stroke="currentColor" stroke-width="2"/>
          <circle cx="24" cy="24" r="3" fill="currentColor"/>
        </svg>
      </div>
      <div class="brand-text">
        <h1 class="brand-name">MINIHES</h1>
        <p class="brand-subtitle">云端智能电表抄表系统</p>
      </div>
    </div>

    <!-- 系统状态指示器 -->
    <div class="system-status">
      <div class="status-item" v-for="item in systemStatus" :key="item.name">
        <span class="status-dot" :class="item.status"></span>
        <span class="status-label">{{ item.label }}</span>
      </div>
    </div>

    <!-- Loading 遮罩 -->
    <Transition name="fade">
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-container">
          <svg class="loading-ring" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(16,185,129,0.2)" stroke-width="2"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#10B981" stroke-width="2"
                    stroke-dasharray="251.2" stroke-dashoffset="62.8" class="loading-spinner"/>
          </svg>
          <p class="loading-text">{{ loadingText }}</p>
        </div>
      </div>
    </Transition>

    <!-- 主登录卡片 -->
    <div class="login-card" :class="{ 'shake': hasError }">
      <div class="card-glow"></div>

      <div class="card-top-bar">
        <div class="bar-segment active"></div>
        <div class="bar-segment"></div>
        <div class="bar-segment"></div>
        <div class="bar-segment"></div>
      </div>

      <form class="login-form" @submit.prevent="handleLogin" novalidate>
        <div class="form-header">
          <div class="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
            </svg>
          </div>
          <div>
            <h2 class="form-title">系统登录</h2>
            <p class="form-subtitle">请输入您的访问凭证</p>
          </div>
        </div>

        <Transition name="slide-down">
          <div v-if="globalError" class="global-error">
            <span class="error-icon">⚠️</span>
            <span>{{ globalError }}</span>
          </div>
        </Transition>

        <div class="input-group" :class="{ 'error': errors.email, 'success': !errors.email && form.email }">
          <label class="input-label" for="email">
            <span class="label-icon">📧</span>
            邮箱地址
          </label>
          <div class="input-wrapper">
            <input
              id="email"
              ref="emailInput"
              type="email"
              v-model="form.email"
              class="input-field"
              placeholder="admin@minihes.com"
              :disabled="isLoading"
              @blur="validateEmail"
              @input="clearError('email')"
            />
            <div class="input-border">
              <div class="border-fill"></div>
            </div>
            <span v-if="!errors.email && form.email" class="input-success">✓</span>
          </div>
          <p v-if="errors.email" class="error-text">{{ errors.email }}</p>
        </div>

        <div class="input-group" :class="{ 'error': errors.password }">
          <label class="input-label" for="password">
            <span class="label-icon">🔑</span>
            密码
          </label>
          <div class="input-wrapper">
            <input
              id="password"
              ref="passwordInput"
              :type="showPassword ? 'text' : 'password'"
              v-model="form.password"
              class="input-field"
              placeholder="••••••••"
              :disabled="isLoading"
              @blur="validatePassword"
              @input="handlePasswordInput"
            />
            <div class="input-border">
              <div class="border-fill"></div>
            </div>
            <button type="button" class="password-toggle" @click="showPassword = !showPassword" :disabled="isLoading">
              {{ showPassword ? '👁' : '👁‍🗨' }}
            </button>
          </div>

          <Transition name="slide-down">
            <div v-if="form.password && !errors.password" class="password-strength">
              <div class="strength-bar">
                <div class="strength-fill" :class="strengthClass" :style="{ width: strengthPercentage + '%' }"></div>
              </div>
              <span class="strength-label" :class="strengthClass">{{ strengthText }}</span>
            </div>
          </Transition>
          <p v-if="errors.password" class="error-text">{{ errors.password }}</p>
        </div>

        <div class="form-options">
          <label class="checkbox-item">
            <input type="checkbox" v-model="form.remember" class="checkbox" :disabled="isLoading"/>
            <span class="checkbox-box"></span>
            <span>记住我</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="form.autoLogin" class="checkbox" :disabled="isLoading"/>
            <span class="checkbox-box"></span>
            <span>自动登录</span>
          </label>
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading || !isFormValid" :class="{ 'loading': isLoading }">
          <span class="btn-bg"></span>
          <span v-if="!isLoading" class="btn-text">安全登录</span>
          <span v-else class="btn-text">{{ loadingText }}</span>
          <span v-if="!isLoading" class="btn-arrow">→</span>
          <svg v-else class="btn-spinner" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/>
            <path d="M12 2a10 10 0 0 1 10 10" fill="none" stroke="currentColor" stroke-width="2" class="spinner-path"/>
          </svg>
        </button>

        <div class="form-footer">
          <NuxtLink to="/forgot-password" class="footer-link">忘记密码?</NuxtLink>
          <span class="footer-divider">|</span>
          <NuxtLink to="/register" class="footer-link">申请账号</NuxtLink>
        </div>
      </form>
    </div>

    <!-- 底部通信状态 -->
    <div class="connection-bar">
      <div class="connection-item" v-for="conn in connections" :key="conn.name">
        <div class="conn-icon">{{ conn.icon }}</div>
        <div class="conn-info">
          <span class="conn-name">{{ conn.name }}</span>
          <div class="conn-dots">
            <span v-for="i in 4" :key="i" class="conn-dot" :class="{ active: i <= conn.strength }"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <p>DLMS/COSEM Protocol Stack · 多通信方式适配</p>
      <p>© 2024 MiniHES</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  auth: false
})

interface LoginForm {
  email: string
  password: string
  remember: boolean
  autoLogin: boolean
}

const form = reactive<LoginForm>({
  email: '',
  password: '',
  remember: false,
  autoLogin: false
})

const errors = reactive<{ email?: string; password?: string }>({})
const globalError = ref('')
const isLoading = ref(false)
const loadingText = ref('登录中...')
const showPassword = ref(false)
const passwordStrength = ref(0)
const hasError = ref(false)

const emailInput = ref<HTMLInputElement>()
const passwordInput = ref<HTMLInputElement>()

const isFormValid = computed(() => {
  return form.email && form.password.length >= 8 && !errors.email && !errors.password
})

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

const systemStatus = ref([
  { name: 'api', label: 'API', status: 'online' },
  { name: 'db', label: '数据库', status: 'online' },
  { name: 'dlms', label: 'DLMS', status: 'online' },
])

const connections = ref([
  { name: '红外', icon: '📡', strength: 2 },
  { name: 'NB-IoT', icon: '📶', strength: 3 },
  { name: 'LoRaWAN', icon: '📡', strength: 2 },
  { name: 'PLC', icon: '⚡', strength: 4 },
])

const validateEmail = (): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email) {
    errors.email = '请输入邮箱地址'
    return false
  }
  if (!emailRegex.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    return false
  }
  errors.email = ''
  return true
}

const validatePassword = (): boolean => {
  if (!form.password) {
    errors.password = '请输入密码'
    return false
  }
  if (form.password.length < 8) {
    errors.password = '密码至少需要8位字符'
    return false
  }
  errors.password = ''
  return true
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

const handlePasswordInput = () => {
  clearError('password')
  passwordStrength.value = calculatePasswordStrength(form.password)
}

const clearError = (field: 'email' | 'password') => {
  errors[field] = ''
}

const triggerShake = () => {
  hasError.value = true
  setTimeout(() => hasError.value = false, 500)
}

const handleLogin = async () => {
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()

  if (!isEmailValid || !isPasswordValid) {
    triggerShake()
    if (!isEmailValid) emailInput.value?.focus()
    else if (!isPasswordValid) passwordInput.value?.focus()
    return
  }

  isLoading.value = true
  loadingText.value = '正在连接...'

  await new Promise(resolve => setTimeout(resolve, 800))
  loadingText.value = '验证中...'
  await new Promise(resolve => setTimeout(resolve, 700))

  if (form.email === 'admin@minihes.com' && form.password === 'admin123456') {
    loadingText.value = '接入系统...'
    await new Promise(resolve => setTimeout(resolve, 500))

    if (form.remember) {
      localStorage.setItem('minihes_remember', 'true')
      localStorage.setItem('minihes_email', form.email)
    }
    if (form.autoLogin) {
      localStorage.setItem('minihes_auto_login', 'true')
    }

    await navigateTo('/dashboard')
  } else {
    isLoading.value = false
    globalError.value = '邮箱或密码错误，请重试'
    triggerShake()
    form.password = ''
    passwordStrength.value = 0
    passwordInput.value?.focus()
    setTimeout(() => globalError.value = '', 5000)
  }
}

onMounted(() => {
  const rememberedEmail = localStorage.getItem('minihes_email')
  const shouldRemember = localStorage.getItem('minihes_remember')

  if (shouldRemember === 'true' && rememberedEmail) {
    form.email = rememberedEmail
    form.remember = true
  }

  const shouldAutoLogin = localStorage.getItem('minihes_auto_login')
  if (shouldAutoLogin === 'true') {
    form.autoLogin = true
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
  --color-primary: #10B981;
  --color-primary-light: #34D399;
  --color-primary-dark: #059669;
  --color-secondary: #3B82F6;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-bg: #0a0e1a;
  --color-bg-light: #111827;
  --color-text: #E2E8F0;
  --color-text-muted: #94A3B8;
  --color-border: #1e3a5f;
}

.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%);
  font-family: 'Noto Sans SC', sans-serif;
  padding: 20px;
}

.hex-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(30deg, rgba(16, 185, 129, 0.03) 12%, transparent 12.5%, transparent 87%, rgba(16, 185, 129, 0.03) 87.5%, rgba(16, 185, 129, 0.03)),
    linear-gradient(150deg, rgba(16, 185, 129, 0.03) 12%, transparent 12.5%, transparent 87%, rgba(16, 185, 129, 0.03) 87.5%, rgba(16, 185, 129, 0.03)),
    linear-gradient(30deg, rgba(16, 185, 129, 0.03) 12%, transparent 12.5%, transparent 87%, rgba(16, 185, 129, 0.03) 87.5%, rgba(16, 185, 129, 0.03)),
    linear-gradient(150deg, rgba(16, 185, 129, 0.03) 12%, transparent 12.5%, transparent 87%, rgba(16, 185, 129, 0.03) 87.5%, rgba(16, 185, 129, 0.03)),
    linear-gradient(60deg, rgba(59, 130, 246, 0.02) 25%, transparent 25.5%, transparent 75%, rgba(59, 130, 246, 0.02) 75%, rgba(59, 130, 246, 0.02)),
    linear-gradient(60deg, rgba(59, 130, 246, 0.02) 25%, transparent 25.5%, transparent 75%, rgba(59, 130, 246, 0.02) 75%, rgba(59, 130, 246, 0.02));
  background-size: 80px 140px;
  background-position: 0 0, 0 0, 40px 70px, 40px 70px, 0 0, 40px 70px;
  animation: gridPulse 8s ease-in-out infinite;
  z-index: 1;
}

@keyframes gridPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.scan-line {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
  opacity: 0.3;
  animation: scan 4s linear infinite;
  z-index: 2;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.data-flow-layer {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
  opacity: 0.5;
}

.flow-line {
  stroke-dasharray: 5, 5;
  animation: flowDash 3s linear infinite;
}

.flow-1 { animation-duration: 4s; }
.flow-2 { animation-duration: 5s; animation-delay: 1s; }
.flow-3 { animation-duration: 4.5s; animation-delay: 2s; }
.flow-4 { animation-duration: 5.5s; animation-delay: 0.5s; }
.flow-5 { animation-duration: 4.2s; animation-delay: 1.5s; }

@keyframes flowDash {
  to { stroke-dashoffset: -15; }
}

.brand-header {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}

.brand-logo {
  width: 64px;
  height: 64px;
  color: var(--color-primary);
  filter: drop-shadow(0 0 20px rgba(16, 185, 129, 0.5));
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.brand-text {
  text-align: center;
  margin-top: 16px;
}

.brand-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 28px;
  font-weight: 900;
  color: var(--color-primary);
  letter-spacing: 6px;
  margin: 0;
  text-shadow: 0 0 30px rgba(16, 185, 129, 0.5);
}

.brand-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 4px 0 0 0;
  letter-spacing: 2px;
}

.system-status {
  position: relative;
  z-index: 10;
  display: flex;
  gap: 24px;
  margin-bottom: 32px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  animation: statusPulse 2s ease-in-out infinite;
}

.status-dot.online {
  background: var(--color-primary);
  box-shadow: 0 0 10px var(--color-primary);
}

@keyframes statusPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.2); }
}

.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 14, 26, 0.95);
  backdrop-filter: blur(10px);
}

.loading-container {
  text-align: center;
}

.loading-ring {
  width: 80px;
  height: 80px;
  animation: ringRotate 2s linear infinite;
}

@keyframes ringRotate {
  to { transform: rotate(360deg); }
}

.loading-spinner {
  transform-origin: center;
  animation: spinnerDash 1.5s ease-in-out infinite;
}

@keyframes spinnerDash {
  0% { stroke-dasharray: 1, 250; stroke-dashoffset: 0; }
  50% { stroke-dasharray: 100, 250; stroke-dashoffset: -50; }
  100% { stroke-dasharray: 1, 250; stroke-dashoffset: -250; }
}

.loading-text {
  margin-top: 20px;
  color: var(--color-primary);
  font-size: 14px;
  letter-spacing: 2px;
  animation: textPulse 1.5s ease-in-out infinite;
}

@keyframes textPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  background: linear-gradient(180deg, rgba(17, 24, 39, 0.95) 0%, rgba(10, 14, 26, 0.98) 100%);
  border-radius: 20px;
  overflow: hidden;
  animation: cardFadeIn 0.6s ease-out;
}

.login-card.shake {
  animation: shake 0.5s ease-in-out;
}

@keyframes cardFadeIn {
  from { opacity: 0; transform: scale(0.95) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-8px); }
  20%, 40%, 60%, 80% { transform: translateX(8px); }
}

.card-glow {
  position: absolute;
  inset: -1px;
  background: linear-gradient(45deg, var(--color-primary), transparent, var(--color-secondary), transparent);
  background-size: 400% 400%;
  animation: glowRotate 8s linear infinite;
  z-index: -1;
  opacity: 0.3;
  border-radius: 21px;
  filter: blur(20px);
}

@keyframes glowRotate {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.card-top-bar {
  display: flex;
  gap: 4px;
  padding: 16px 24px 0;
}

.bar-segment {
  flex: 1;
  height: 3px;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 2px;
  transition: all 0.5s ease;
}

.bar-segment.active {
  background: var(--color-primary);
  box-shadow: 0 0 10px var(--color-primary);
}

.login-form {
  padding: 24px 32px 32px;
}

.form-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}

.header-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 12px;
  color: var(--color-primary);
}

.form-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 2px 0;
}

.form-subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0;
}

.global-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: #FCA5A5;
  font-size: 13px;
}

.error-icon {
  font-size: 16px;
}

.input-group {
  margin-bottom: 20px;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.label-icon {
  font-size: 14px;
}

.input-wrapper {
  position: relative;
}

.input-field {
  width: 100%;
  padding: 14px 48px 14px 16px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  color: var(--color-text);
  font-size: 14px;
  transition: all 0.3s ease;
}

.input-field::placeholder {
  color: var(--color-text-muted);
}

.input-field:focus {
  outline: none;
  background: rgba(30, 41, 59, 0.8);
}

.input-field:disabled {
  opacity: 0.6;
}

.input-group.error .input-field {
  border-color: var(--color-error);
}

.input-group.success .input-field {
  border-color: var(--color-primary);
}

.input-border {
  position: absolute;
  bottom: 0;
  left: 16px;
  right: 16px;
  height: 1px;
  background: var(--color-border);
  overflow: hidden;
  border-radius: 1px;
}

.border-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 0;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  transition: width 0.5s ease;
}

.input-field:focus ~ .input-border .border-fill {
  width: 100%;
}

.input-group.error .input-field:focus ~ .input-border .border-fill {
  background: var(--color-error);
}

.input-success {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-primary);
  font-size: 14px;
  animation: scaleIn 0.2s ease;
}

@keyframes scaleIn {
  from { transform: translateY(-50%) scale(0); }
  to { transform: translateY(-50%) scale(1); }
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

.password-toggle:hover:not(:disabled) {
  opacity: 1;
}

.password-toggle:disabled {
  cursor: not-allowed;
}

.error-text {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-error);
}

.error-text::before {
  content: '⚠';
  font-size: 10px;
}

.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.strength-bar {
  flex: 1;
  height: 3px;
  background: rgba(51, 65, 85, 0.5);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s ease;
  border-radius: 2px;
}

.strength-fill.weak { background: var(--color-error); }
.strength-fill.fair { background: var(--color-warning); }
.strength-fill.good { background: var(--color-primary); }
.strength-fill.strong { background: var(--color-primary); box-shadow: 0 0 10px var(--color-primary); }

.strength-label {
  font-size: 10px;
  font-weight: 500;
  text-transform: uppercase;
}

.strength-label.weak { color: var(--color-error); }
.strength-label.fair { color: var(--color-warning); }
.strength-label.good { color: var(--color-primary); }
.strength-label.strong { color: var(--color-primary); }

.form-options {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--color-text-muted);
}

.checkbox {
  display: none;
}

.checkbox-box {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-radius: 4px;
  transition: all 0.3s ease;
  position: relative;
}

.checkbox:checked + .checkbox-box {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox:checked + .checkbox-box::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 10px;
}

.checkbox:disabled + .checkbox-box {
  opacity: 0.5;
  cursor: not-allowed;
}

.submit-btn {
  position: relative;
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
}

.btn-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transform: translateX(-100%);
  transition: transform 0.6s ease;
}

.submit-btn:hover:not(:disabled) .btn-bg {
  transform: translateX(100%);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.submit-btn:hover:not(:disabled) .btn-arrow {
  transform: translateX(4px);
}

.btn-spinner {
  width: 18px;
  height: 18px;
  animation: spin 1s linear infinite;
}

.spinner-path {
  stroke: currentColor;
  stroke-dasharray: 50;
  stroke-dashoffset: 25;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}

.footer-link {
  font-size: 13px;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-link:hover {
  color: var(--color-primary);
}

.footer-divider {
  color: var(--color-border);
}

.connection-bar {
  position: relative;
  z-index: 10;
  display: flex;
  gap: 32px;
  margin-top: 32px;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.conn-icon {
  font-size: 20px;
}

.conn-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conn-name {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.conn-dots {
  display: flex;
  gap: 3px;
}

.conn-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--color-border);
  transition: all 0.3s ease;
}

.conn-dot.active {
  background: var(--color-primary);
  box-shadow: 0 0 6px var(--color-primary);
}

.footer {
  position: relative;
  z-index: 10;
  text-align: center;
  margin-top: 32px;
}

.footer p {
  font-size: 11px;
  color: var(--color-text-muted);
  margin: 2px 0;
  font-family: 'JetBrains Mono', monospace;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  transform-origin: top;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: scaleY(0);
}

@media (max-width: 640px) {
  .login-container {
    padding: 16px;
  }

  .login-form {
    padding: 20px 20px 28px;
  }

  .connection-bar {
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }

  .system-status {
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
  }
}
</style>
