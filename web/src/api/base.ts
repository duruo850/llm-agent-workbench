/** 后端 API 根路径：经 nginx / vite 代理到 server（/api → server:8000）。 */
export function resolveApiBase(): string {
  return "/api";
}
