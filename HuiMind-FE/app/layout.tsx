import type { Metadata } from "next";
import Script from "next/script";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "HuiMind | AI 学习工作台",
  description: "面向学习、复习与职业成长的 AI 工作台",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="bg-background text-on-background font-body selection:bg-primary/30 selection:text-primary">
        <Script src="https://cdn.tailwindcss.com?plugins=forms,container-queries" strategy="beforeInteractive" />
        <Script
          id="tw-config"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "surface-container-lowest": "#0b1428",
        "outline": "#8c96bd",
        "primary-container": "#2c2456",
        "error-container": "#4a2230",
        "surface-container-high": "#15203b",
        "surface-container-highest": "#1a2747",
        "surface-dim": "#0a1326",
        "surface-container": "#101a31",
        "on-secondary": "#ffffff",
        "secondary-container": "#20315a",
        "on-primary": "#ffffff",
        "background": "#060e20",
        "on-secondary-container": "#d9e3ff",
        "secondary": "#7f9cff",
        "error": "#ff7f9d",
        "surface": "#0d1730",
        "on-tertiary": "#052d20",
        "outline-variant": "#2c395c",
        "primary-fixed": "#cfc2ff",
        "surface-bright": "#162341",
        "secondary-dim": "#6484f1",
        "tertiary": "#52d2a3",
        "surface-variant": "#111b34",
        "on-surface": "#dee5ff",
        "primary": "#ba9eff",
        "surface-container-low": "#0f1830",
        "error-dim": "#ff9bb1",
        "surface-tint": "#ba9eff",
        "on-background": "#dee5ff",
        "on-surface-variant": "#93a0c6",
        "primary-dim": "#9d7dff",
      },
      fontFamily: {
        "headline": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "label": ["Plus Jakarta Sans", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
        full: "9999px",
      },
    },
  },
}
`,
          }}
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        {children}
      </body>
    </html>
  );
}
