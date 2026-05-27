/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'buy-zone': '#22c55e',    // 買入區 - 綠色
        'hold-zone': '#eab308',   // 持有區 - 黃色
        'sell-zone': '#ef4444',   // 賣出區 - 紅色
      }
    },
  },
  plugins: [],
}