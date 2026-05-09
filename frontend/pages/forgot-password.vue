<template>
  <div class="forgot-container">
    <div class="background-grid">
      <div class="grid-line" v-for="i in 20" :key="i" :style="{ animationDelay: `${i * 0.1}s` }"></div>
    </div>

    <div class="particles">
      <div class="particle" v-for="i in 10" :key="`p-${i}`" :style="particleStyle(i)"></div>
    </div>

    <div class="forgot-card">
      <div class="back-link">
        <NuxtLink to="/" class="back-btn">
          <span>←</span>
          <span>返回登录</span>
        </NuxtLink>
      </div>

      <div class="card-header">
        <div class="icon-wrapper">🔑</div>
        <h1 class="card-title">忘记密码</h1>
        <p class="card-subtitle">输入您的邮箱地址，我们将发送重置链接</p>
      </div>

      <form class="forgot-form" @submit.prevent="handleSubmit">
        <div class="input-group" :class="{ 'has-error': errors.email }">
          <label class="input-label" for="email">邮箱地址</label>
          <div class="input-wrapper">
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="input-field"
              :class="{ 'error': errors.email }"
              placeholder="your@email.com"
              :disabled="isLoading"
            />
            <span v-if="emailSent" class="input-success">✓</span>
          </div>
          <p v-if="errors.email" class="input-error">{{ errors.email }}</p>
        </div>

        <button
          type="submit"
          class="submit-btn"
          :disabled="isLoading || !form.email"
          :class="{ 'loading': isLoading }"
        >
          <span v-if="!isLoading">{{ emailSent ? '重新发送' : '发送重置链接' }}</span>
          <span v-else>发送中...</span>
        </button>
      </form>

      <Transition name="fade">
        <div v-if="emailSent" class="success-message">
          <span class="success-icon">✉️</span>
          <p>重置链接已发送到您的邮箱</p>
          <span class="success-text">请检查您的收件箱（包括垃圾邮件文件夹）</span>
        </div>
      </Transition>

      <div class="card-footer">
        <p>记住密码了？<NuxtLink to="/">立即登录</NuxtLink></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  auth: false
})

interface ForgotForm {
  email: string
}

const form = reactive<ForgotForm>({
  email: ''
})

const errors = reactive<{ email?: string }>({})
const isLoading = ref(false)
const emailSent = ref(false)

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

const handleSubmit = async () => {
  if (!validateEmail()) return

  isLoading.value = true
  await new Promise(resolve => setTimeout(resolve, 1500))
  emailSent.value = true
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

.forgot-container {
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

.forgot-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 400px;
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

.forgot-form {
  margin-bottom: 24px;
}

.input-group {
  margin-bottom: 20px;
}

.input-label {
  display: block;
  font-size: 13px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

.input-wrapper {
  position: relative;
}

.input-field {
  width: 100%;
  padding: 14px 16px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  color: var(--color-text);
  font-size: 14px;
  transition: all 0.3s ease;
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

.input-success {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-primary);
  font-size: 16px;
}

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
  font-size: 32px;
}

.success-message p {
  font-size: 14px;
  color: var(--color-text);
  margin: 0;
}

.success-text {
  font-size: 12px;
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
  .forgot-card {
    margin: 16px;
    padding: 24px;
  }
}
</style>
