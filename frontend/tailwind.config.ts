import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        chain: {
          valid: "#22c55e",
          invalid: "#ef4444",
          pending: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
