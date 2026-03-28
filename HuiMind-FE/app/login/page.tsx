"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/lib/api";
import { isLoggedIn, setAuthSession } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@huimind.ai");
  const [password, setPassword] = useState("123456");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (isLoggedIn()) router.replace("/dashboard");
  }, [router]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await login(email, password);
      setAuthSession(data);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center p-6">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
        <div className="space-y-8">
          <div>
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-primary">HuiMind</span>
            <h1 className="text-4xl font-headline font-black text-on-surface mt-3 leading-tight">
              你的 AI 学习工作台
            </h1>
            <p className="text-on-surface-variant text-sm mt-4 leading-relaxed max-w-sm">
              把知识管理、AI 辅导、间隔复习和职业训练放进同一个工作空间里，建立自己的持续成长系统。
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "场景", value: "02", desc: "通用学习 / 职业发展" },
              { label: "AI 闭环", value: "RAG", desc: "提问、复盘、诊断" },
              { label: "记忆", value: "24h", desc: "间隔复习机制" },
            ].map((stat) => (
              <div key={stat.label} className="glass-card rounded-2xl p-4">
                <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">{stat.label}</span>
                <p className="text-2xl font-headline font-black text-primary mt-1">{stat.value}</p>
                <p className="text-[11px] text-on-surface-variant mt-1">{stat.desc}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 opacity-70">
            <div className="w-10 h-10 rounded-full bg-tertiary/20 border border-tertiary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-tertiary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
            </div>
            <div className="h-px flex-1 bg-gradient-to-r from-tertiary/30 to-transparent"></div>
            <div className="w-8 h-8 rounded-full bg-secondary/20 border border-secondary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-secondary text-sm">work</span>
            </div>
            <div className="h-px flex-1 bg-gradient-to-r from-secondary/30 to-transparent"></div>
            <div className="w-8 h-8 rounded-full border border-outline-variant/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-outline text-sm">lock</span>
            </div>
          </div>
        </div>

        <div className="glass-card rounded-3xl p-8 shadow-xl">
          <div className="mb-6">
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-primary">登录工作台</span>
            <h2 className="text-2xl font-headline font-bold text-on-surface mt-1">进入 HuiMind</h2>
            <p className="text-on-surface-variant text-xs mt-1">当前为演示账号，默认凭证已预填</p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">邮箱</span>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-1.5 w-full bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border border-outline-variant/30 focus:border-primary transition-colors"
              />
            </label>

            <label className="block">
              <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">密码</span>
              <input
                value={password}
                type="password"
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                className="mt-1.5 w-full bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border border-outline-variant/30 focus:border-primary transition-colors"
              />
            </label>

            {error && (
              <p className="text-error text-xs bg-error/10 rounded-xl px-4 py-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-primary to-secondary text-on-primary font-headline font-bold py-3.5 rounded-xl shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed mt-2 flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>workspace_premium</span>
              {loading ? "登录中..." : "进入工作台"}
            </button>

            <button
              type="button"
              onClick={() => router.replace("/dashboard")}
              className="w-full bg-surface-container-high text-on-surface font-headline font-bold py-3.5 rounded-xl border border-outline-variant/30 hover:bg-surface-container-highest hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
            >
              <span className="material-symbols-outlined">skip_next</span>
              跳过登录（调试模式）
            </button>
          </form>

          <div className="flex gap-2 mt-5 flex-wrap">
            <span className="text-[10px] font-label bg-surface-container-high px-3 py-1 rounded-full text-outline">demo@huimind.ai</span>
            <span className="text-[10px] font-label bg-surface-container-high px-3 py-1 rounded-full text-outline">接口：/api/v1</span>
          </div>
        </div>
      </div>
    </main>
  );
}
