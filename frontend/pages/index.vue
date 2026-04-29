<template>
  <div class="container">
    <h1>{{ appConfig.title }}</h1>
    <p>Welcome to MiniHES</p>
  </div>
</template>

<script setup lang="ts">
const appConfig = useAppConfig()
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
