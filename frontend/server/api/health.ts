export default defineEventHandler(async () => {
  const config = useRuntimeConfig()
  const response = await fetch(`${config.public.apiBase}/health`)
  return await response.json()
})
