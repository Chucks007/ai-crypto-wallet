declare module "vitest/config" {
  import type { UserConfigExport } from "vite";
  export function defineConfig(config: UserConfigExport): UserConfigExport;
}
