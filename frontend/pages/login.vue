<template>
  <div class="login-container">
    <!-- 动态背景 -->
    <div class="background-grid">
      <div class="grid-line" v-for="i in 20" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
    </div>

    <!-- 浮动数据粒子 -->
    <div class="particles">
      <div class="particle" v-for="i in 15" :key="`p-${i}`" :style="particleStyle(i)"></div>
    </div>

    <!-- Loading 遮罩 -->
    <Transition name="fade">
      <div v-if="isLoading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p class="loading-text">登录中...</p>
      </div>
    </Transition>

    <!-- 主卡片 -->
    <div class="login-card">
      <!-- 顶部品牌区 -->
      <div class="brand-section">
        <div class="logo-wrapper">
          <div class="logo-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M24 4L8 12V24C8 33.9414 15.1608 42.9242 24 46C32.8392 42.9242 40 33.9414 40 24V12L24 4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M24 16V32M24 24H32" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="24" cy="24" r="3" fill="currentColor"/>
            </svg>
          </div>
          <div class="pulse-ring"></div>
        </div>
        <h1 class="brand-title">MINIHES</h1>
        <p class="brand-subtitle">云端智能电表抄表系统</p>
        <p class="brand-english">Cloud Smart Meter Reading System</p>
      </div>

      <!-- 数据流装饰 -->
      <div class="data-stream">
        <div class="stream-dot" v-for="i in 8" :key="`s-${i}`"></div>
      </div>

      <!-- 全局错误提示 -->
      <Transition name="shake">
        <div v-if="globalError" class="global-error" role="alert">
          <span class="error-icon">⚠️</span>
          <span class="error-text">{{ globalError }}</span>
          <button type="button" class="error-close" @click="globalError = ''" aria-label="关闭错误提示">×</button>
        </div>
      </Transition>

      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin" novalidate>
        <div class="form-header">
          <span class="form-icon">🔐</span>
          <h2 class="form-title">系统登录</h2>
        </div>

        <!-- 邮箱输入 -->
        <div class="input-group" :class="{ 'has-error': errors.email }">
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
              :class="{ 'error': errors.email, 'success': !errors.email && form.email }"
              placeholder="admin@minihes.com"
              :disabled="isLoading"
              :aria-invalid="errors.email ? 'true' : 'false'"
              :aria-describedby="errors.email ? 'email-error' : undefined"
              @blur="validateEmail"
              @input="clearError('email')"
            />
            <span v-if="!errors.email && form.email" class="input-success">✓</span>
            <div class="input-border"></div>
          </div>
          <Transition name="slide-down">
            <p v-if="errors.email" id="email-error" class="input-error" role="alert">{{ errors.email }}</p>
          </Transition>
        </div>

        <!-- 密码输入 -->
        <div class="input-group" :class="{ 'has-error': errors.password }">
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
              class="input-field password-field"
              :class="{ 'error': errors.password }"
              placeholder="••••••••"
              :disabled="isLoading"
              :aria-invalid="errors.password ? 'true' : 'false'"
              :aria-describedby="errors.password ? 'password-error' : 'password-strength'"
              @blur="validatePassword"
              @input="handlePasswordInput"
            />
            <button
              type="button"
              class="password-toggle"
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              :disabled="isLoading"
            >
              {{ showPassword ? '👁' : '👁‍🗨' }}
            </button>
            <div class="input-border"></div>
          </div>

          <!-- 密码强度指示器 -->
          <Transition name="slide-down">
            <div v-if="form.password && !errors.password" id="password-strength" class="password-strength">
              <div class="strength-bar">
                <div
                  class="strength-fill"
                  :class="strengthClass"
                  :style="{ width: `${strengthPercentage}%` }"
                ></div>
              </div>
              <span class="strength-text" :class="strengthClass">{{ strengthText }}</span>
            </div>
          </Transition>

          <Transition name="slide-down">
            <p v-if="errors.password" id="password-error" class="input-error" role="alert">{{ errors.password }}</p>
          </Transition>
        </div>

        <!-- 表单选项 -->
        <div class="form-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.remember" class="checkbox" :disabled="isLoading"/>
            <span class="checkbox-text">记住我</span>
          </label>
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.autoLogin" class="checkbox" :disabled="isLoading"/>
            <span class="checkbox-text">自动登录</span>
          </label>
        </div>

        <!-- 提交按钮 -->
        <button
          type="submit"
          class="submit-btn"
          :disabled="isLoading || !isFormValid"
          :class="{ 'loading': isLoading, 'disabled': !isFormValid }"
        >
          <span v-if="!isLoading" class="btn-text">安全登录</span>
          <span v-else class="btn-text">登录中...</span>
          <span v-if="!isLoading" class="btn-icon">→</span>
          <span v-else class="loading-icon">⟳</span>
          <div class="btn-glow"></div>
        </button>

        <div class="form-footer">
          <NuxtLink to="/forgot-password" class="footer-link">忘记密码?</NuxtLink>
          <span class="footer-divider">|</span>
          <NuxtLink to="/register" class="footer-link">申请账号</NuxtLink>
        </div>
      </form>

      <!-- 底部信息 -->
      <div class="footer-info">
        <p>DLMS/COSEM Protocol Stack</p>
        <p class="copyright">© 2024 MiniHES · 多通信方式适配</p>
      </div>
    </div>

    <!-- 语言选择 -->
    <div class="lang-selector">
      <button class="lang-btn">中文 ▼</button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 定义页面元数据
definePageMeta({
  layout: 'auth',
  auth: false
})

// 接口定义
interface LoginForm {
  email: string
  password: string
  remember: boolean
  autoLogin: boolean
}

interface FormErrors {
  email?: string
  password?: string
}

// 响应式状态
const form = reactive<LoginForm>({
  email: '',
  password: '',
  remember: false,
  autoLogin: false
})

const errors = reactive<FormErrors>({})
const globalError = ref('')
const isLoading = ref(false)
const showPassword = ref(false)
const passwordStrength = ref(0)

// Refs
const emailInput = ref<HTMLInputElement>()
const passwordInput = ref<HTMLInputElement>()

// 计算属性
const isFormValid = computed(() => {
  return form.email && form.password && !errors.email && !errors.password && passwordStrength.value >= 2
})

const strengthPercentage = computed(() => {
  return (passwordStrength.value / 4) * 100
})

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

// 邮箱验证
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

// 密码验证
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

// 计算密码强度
const calculatePasswordStrength = (password: string): number => {
  let strength = 0

  // 长度检查
  if (password.length >= 8) strength++
  if (password.length >= 12) strength++

  // 包含小写字母
  if (/[a-z]/.test(password)) strength++

  // 包含大写字母
  if (/[A-Z]/.test(password)) strength++

  // 包含数字
  if (/\d/.test(password)) strength++

  // 包含特殊字符
  if (/[^a-zA-Z0-9]/.test(password)) strength++

  return Math.min(strength, 4)
}

// 处理密码输入
const handlePasswordInput = () => {
  clearError('password')
  passwordStrength.value = calculatePasswordStrength(form.password)
}

// 清除错误
const clearError = (field: keyof FormErrors) => {
  errors[field] = ''
}

// 显示全局错误
const showGlobalError = (message: string) => {
  globalError.value = message
  setTimeout(() => {
    globalError.value = ''
  }, 5000)
}

// 处理登录
const handleLogin = async () => {
  // 验证表单
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()

  if (!isEmailValid || !isPasswordValid) {
    // 聚焦到第一个错误的输入框
    if (!isEmailValid) {
      emailInput.value?.focus()
    } else if (!isPasswordValid) {
      passwordInput.value?.focus()
    }
    return
  }

  isLoading.value = true

  try {
    // TODO: 替换为实际的 API 调用
    await new Promise(resolve => setTimeout(resolve, 1500))

    // 模拟 API 响应
    if (form.email === 'admin@minihes.com' && form.password === 'admin123456') {
      // 登录成功
      if (form.remember) {
        localStorage.setItem('minihes_remember', 'true')
        localStorage.setItem('minihes_email', form.email)
      }
      if (form.autoLogin) {
        localStorage.setItem('minihes_auto_login', 'true')
      }

      // 跳转到仪表盘
      await navigateTo('/dashboard')
    } else {
      // 登录失败
      showGlobalError('邮箱或密码错误，请重试')
      form.password = ''
      passwordStrength.value = 0
      passwordInput.value?.focus()
    }
  } catch (err) {
    showGlobalError('网络连接失败，请检查网络后重试')
  } finally {
    isLoading.value = false
  }
}

// 粒子样式生成
const particleStyle = (index: number) => ({
  left: `${Math.random() * 100}%`,
  animationDelay: `${Math.random() * 5}s`,
  animationDuration: `${5 + Math.random() * 10}s`
})

// 组件挂载时检查记住的用户
onMounted(() => {
  const rememberedEmail = localStorage.getItem('minihes_email')
  const shouldRemember = localStorage.getItem('minihes_remember')

  if (shouldRemember === 'true' && rememberedEmail) {
    form.email = rememberedEmail
    form.remember = true
  }

  // 检查自动登录
  const shouldAutoLogin = localStorage.getItem('minihes_auto_login')
  if (shouldAutoLogin === 'true') {
    form.autoLogin = true
  }
})
</script>

<style scoped>
/* ===== 字体定义 ===== */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Orbitron:wght@400;700;900&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

:root {
  --color-primary: #10B981;
  --color-primary-light: #34D399;
  --color-primary-dark: #059669;
  --color-secondary: #3B82F6;
  --color-accent: #F59E0B;
  --color-error: #EF4444;
  --color-warning: #F59E0B;
  --color-success: #10B981;
  --color-bg: #0F172A;
  --color-bg-light: #1E293B;
  --color-text: #E2E8F0;
  --color-text-muted: #94A3B8;
  --color-border: #334155;
  --color-glow: rgba(16, 185, 129, 0.5);
  --color-error-glow: rgba(239, 68, 68, 0.3);

  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;

  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
}

/* ===== 容器布局 ===== */
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--color-bg);
  font-family: 'Noto Sans SC', sans-serif;
  isolation: isolate;
}

/* ===== 动态网格背景 ===== */
.background-grid {
  position: absolute;
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

/* ===== 浮动粒子 ===== */
.particles {
  position: absolute;
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

/* ===== Loading 遮罩 ===== */
.loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(16, 185, 129, 0.2);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: var(--spacing-lg);
  color: var(--color-text);
  font-size: var(--text-base);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* ===== 登录卡片 ===== */
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 440px;
  padding: var(--spacing-2xl) 40px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: var(--radius-xl);
  backdrop-filter: blur(20px);
  box-shadow:
    0 0 60px rgba(16, 185, 129, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  animation: cardFadeIn 0.8s ease-out;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== 品牌区域 ===== */
.brand-section {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.logo-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: var(--spacing-md);
}

.logo-icon {
  width: 64px;
  height: 64px;
  color: var(--color-primary);
  animation: logoGlow 2s ease-in-out infinite;
}

@keyframes logoGlow {
  0%, 100% { filter: drop-shadow(0 0 10px var(--color-glow)); }
  50% { filter: drop-shadow(0 0 25px var(--color-glow)); }
}

.pulse-ring {
  position: absolute;
  inset: -8px;
  border: 2px solid var(--color-primary);
  border-radius: 50%;
  animation: pulseRing 2s ease-out infinite;
}

@keyframes pulseRing {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.5); opacity: 0; }
}

.brand-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 32px;
  font-weight: 900;
  color: var(--color-primary);
  letter-spacing: 8px;
  margin: 0 0 var(--spacing-sm) 0;
  text-shadow: 0 0 30px var(--color-glow);
}

.brand-subtitle {
  font-size: var(--text-md);
  color: var(--color-text);
  margin: 0 0 var(--spacing-xs) 0;
  font-weight: 500;
}

.brand-english {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 2px;
  margin: 0;
  text-transform: uppercase;
}

/* ===== 数据流装饰 ===== */
.data-stream {
  display: flex;
  justify-content: center;
  gap: var(--spacing-sm);
  margin: var(--spacing-lg) 0 var(--spacing-2xl) 0;
}

.stream-dot {
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 50%;
  animation: streamPulse 1.5s ease-in-out infinite;
}

.stream-dot:nth-child(1) { animation-delay: 0s; }
.stream-dot:nth-child(2) { animation-delay: 0.1s; }
.stream-dot:nth-child(3) { animation-delay: 0.2s; }
.stream-dot:nth-child(4) { animation-delay: 0.3s; }
.stream-dot:nth-child(5) { animation-delay: 0.4s; }
.stream-dot:nth-child(6) { animation-delay: 0.3s; }
.stream-dot:nth-child(7) { animation-delay: 0.2s; }
.stream-dot:nth-child(8) { animation-delay: 0.1s; }

@keyframes streamPulse {
  0%, 100% { transform: scale(0.8); opacity: 0.3; }
  50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 10px var(--color-glow); }
}

/* ===== 全局错误 ===== */
.global-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: var(--radius-md);
  color: #FCA5A5;
  font-size: var(--text-sm);
}

.error-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.error-text {
  flex: 1;
}

.error-close {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
  transition: color var(--duration-normal);
}

.error-close:hover {
  color: var(--color-text);
}

/* ===== 表单样式 ===== */
.login-form {
  margin-bottom: var(--spacing-lg);
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-2xl);
}

.form-icon {
  font-size: 24px;
}

.form-title {
  font-size: var(--text-xl);
  font-weight: 500;
  color: var(--color-text);
  margin: 0;
}

.input-group {
  margin-bottom: var(--spacing-lg);
}

.input-group.has-error .input-label {
  color: var(--color-error);
}

.input-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-sm);
  font-weight: 500;
  transition: color var(--duration-normal);
}

.label-icon {
  font-size: 16px;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-field {
  flex: 1;
  width: 100%;
  padding: 14px 16px;
  padding-right: 48px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
  font-size: var(--text-base);
  font-family: 'Noto Sans SC', sans-serif;
  transition: all var(--duration-normal) ease;
}

.input-field::placeholder {
  color: var(--color-text-muted);
}

.input-field:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.input-field.error {
  border-color: var(--color-error);
  box-shadow: 0 0 0 3px var(--color-error-glow);
}

.input-field.error:focus {
  box-shadow: 0 0 0 3px var(--color-error-glow);
}

.input-field.success {
  border-color: var(--color-success);
}

.input-field.success:focus {
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}

.input-field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-success {
  position: absolute;
  right: 48px;
  color: var(--color-success);
  font-size: 16px;
  animation: scaleIn 0.2s ease;
}

@keyframes scaleIn {
  from { transform: scale(0); }
  to { transform: scale(1); }
}

.password-field {
  padding-right: 88px;
}

.input-border {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: var(--color-primary);
  transition: all var(--duration-normal) ease;
  transform: translateX(-50%);
}

.input-field:focus ~ .input-border {
  width: calc(100% - 32px);
}

.input-field.error ~ .input-border {
  background: var(--color-error);
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.5;
  transition: opacity var(--duration-normal);
}

.password-toggle:hover:not(:disabled) {
  opacity: 1;
}

.password-toggle:disabled {
  cursor: not-allowed;
}

/* ===== 输入框错误提示 ===== */
.input-error {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-xs);
  font-size: var(--text-sm);
  color: var(--color-error);
}

.input-error::before {
  content: '⚠';
  font-size: 12px;
}

/* ===== 密码强度指示器 ===== */
.password-strength {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
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
  transition: all var(--duration-slow) ease;
  border-radius: 2px;
}

.strength-fill.weak {
  background: var(--color-error);
}

.strength-fill.fair {
  background: var(--color-warning);
}

.strength-fill.good {
  background: var(--color-primary);
}

.strength-fill.strong {
  background: var(--color-success);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
}

.strength-text {
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: uppercase;
}

.strength-text.weak { color: var(--color-error); }
.strength-text.fair { color: var(--color-warning); }
.strength-text.good { color: var(--color-primary); }
.strength-text.strong { color: var(--color-success); }

/* ===== 表单选项 ===== */
.form-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.checkbox {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-radius: 4px;
  background: rgba(30, 41, 59, 0.5);
  cursor: pointer;
  position: relative;
  transition: all var(--duration-normal) ease;
}

.checkbox:hover:not(:disabled) {
  border-color: var(--color-primary);
}

.checkbox:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.checkbox:checked::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
}

.checkbox:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.checkbox-text {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* ===== 提交按钮 ===== */
.submit-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-size: var(--text-md);
  font-weight: 500;
  cursor: pointer;
  overflow: hidden;
  transition: all var(--duration-normal) ease;
  font-family: 'Noto Sans SC', sans-serif;
}

.submit-btn:hover:not(:disabled):not(.disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled,
.submit-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.submit-btn.loading {
  pointer-events: none;
}

.btn-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(255,255,255,0.2) 0%, transparent 70%);
  opacity: 0;
  transition: opacity var(--duration-normal) ease;
}

.submit-btn:hover:not(:disabled):not(.disabled) .btn-glow {
  opacity: 1;
}

.btn-icon {
  font-size: 18px;
  transition: transform var(--duration-normal) ease;
}

.submit-btn:hover:not(:disabled):not(.disabled) .btn-icon {
  transform: translateX(4px);
}

.loading-icon {
  font-size: 18px;
  animation: spin 1s linear infinite;
}

/* ===== 表单底部 ===== */
.form-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-top: var(--spacing-lg);
}

.footer-link {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--duration-normal) ease;
}

.footer-link:hover {
  color: var(--color-primary);
}

.footer-divider {
  color: var(--color-border);
}

/* ===== 底部信息 ===== */
.footer-info {
  text-align: center;
  padding-top: var(--spacing-lg);
  border-top: 1px solid rgba(51, 65, 85, 0.5);
}

.footer-info p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin: 4px 0;
}

.footer-info .copyright {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

/* ===== 语言选择器 ===== */
.lang-selector {
  position: absolute;
  top: var(--spacing-lg);
  right: var(--spacing-lg);
  z-index: 20;
}

.lang-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-normal) ease;
}

.lang-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-text);
}

/* ===== 动画过渡 ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--duration-normal) ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all var(--duration-normal) ease;
  transform-origin: top;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: scaleY(0);
}

.shake-enter-active {
  animation: shake 0.5s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

/* ===== 响应式设计 ===== */
@media (max-width: 640px) {
  .login-container {
    padding: var(--spacing-md);
  }

  .login-card {
    margin: 0;
    padding: var(--spacing-xl) var(--spacing-lg);
  }

  .brand-title {
    font-size: 24px;
    letter-spacing: 4px;
  }

  .form-options {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
