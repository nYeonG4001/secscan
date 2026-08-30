type DemoEnvironment = {
  MODE?: string;
  VITE_DEMO_PREFILL?: string;
  VITE_DEMO_ADMIN_EMAIL?: string;
  VITE_DEMO_ADMIN_PASSWORD?: string;
};

const viteEnvironment = (import.meta as ImportMeta & { env: DemoEnvironment }).env;

export function getDemoPrefill(demoEnvironment: DemoEnvironment = viteEnvironment) {
  const { MODE, VITE_DEMO_PREFILL, VITE_DEMO_ADMIN_EMAIL, VITE_DEMO_ADMIN_PASSWORD } = demoEnvironment;

  if (MODE === "development" && VITE_DEMO_PREFILL === "true" && VITE_DEMO_ADMIN_EMAIL && VITE_DEMO_ADMIN_PASSWORD) {
    return { email: VITE_DEMO_ADMIN_EMAIL, password: VITE_DEMO_ADMIN_PASSWORD };
  }

  return { email: "", password: "" };
}
