"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { clearAuthSession, getStoredUser, isLoggedIn } from "@/lib/auth";

const primaryNavItems = [
  { href: "/dashboard", label: "学习中枢", icon: "space_dashboard" },
  { href: "/knowledge-base", label: "知识库", icon: "folder_open" },
  { href: "/tutor", label: "学习辅导", icon: "psychology" },
  { href: "/progress", label: "复习进度", icon: "query_stats" },
];

const sceneItems = [
  { href: "/career", label: "求职助手", icon: "work", enabled: true },
  { href: "/kaoyan", label: "考研备考", icon: "school", enabled: true },
  { href: "/gongkao", label: "考公备考", icon: "account_balance", enabled: true },
];

type WorkspaceFrameProps = {
  title: string;
  subtitle: string;
  badge: string;
  children: ReactNode;
  hidePageHeader?: boolean;
};

export function WorkspaceFrame({
  title,
  subtitle,
  badge,
  children,
  hidePageHeader = false,
}: WorkspaceFrameProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [authReady, setAuthReady] = useState(false);
  const [nickname, setNickname] = useState("学员");
  const [sceneMenuOpen, setSceneMenuOpen] = useState(false);

  const sceneActive = sceneItems.some((item) => item.enabled && (pathname === item.href || pathname.startsWith(item.href + "/")));

  useEffect(() => {
    // 临时关闭登录检查，确保可以直接访问系统界面
    // if (!isLoggedIn()) {
    //   router.replace("/login");
    //   return;
    // }
    // 模拟用户已登录状态
    setNickname("测试用户");
    setAuthReady(true);
  }, [router]);

  function handleLogout() {
    clearAuthSession();
    router.replace("/login");
  }

  if (!authReady) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="glass-card rounded-3xl p-10 border border-outline-variant/40 text-center space-y-3 shadow-[0_18px_60px_rgba(107,95,184,0.12)]">
          <span className="material-symbols-outlined text-primary text-4xl animate-pulse">bolt</span>
          <p className="font-headline font-bold text-on-surface">正在加载工作台...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden md:flex flex-col w-64 fixed left-0 top-0 h-screen z-40 bg-[#060e20] backdrop-blur-xl border-r border-outline-variant/60 shadow-[0_18px_60px_rgba(0,0,0,0.35)]">
        <div className="px-6 py-5 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary/15 flex items-center justify-center shadow-[0_10px_30px_rgba(132,85,239,0.16)]">
            <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
          </div>
          <div>
            <h1 className="text-primary font-headline font-bold text-sm leading-tight">HuiMind</h1>
            <p className="text-[10px] text-outline font-label">AI 学习操作台</p>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-2">
          {primaryNavItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all duration-300 ${
                  active
                    ? "bg-primary/12 text-primary border border-primary/20 rounded-2xl shadow-[0_12px_30px_rgba(132,85,239,0.08)]"
                    : "text-secondary hover:bg-white/5 hover:text-primary rounded-2xl border border-transparent"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]" style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                  {item.icon}
                </span>
                <span className="font-body">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="px-6 py-4">
          <button className="w-full bg-gradient-to-r from-tertiary to-secondary text-on-tertiary font-headline font-bold py-3 rounded-xl shadow-lg shadow-tertiary/20 hover:scale-[1.02] active:scale-95 transition-all text-sm flex items-center justify-center gap-2">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>timer</span>
            开始专注
          </button>
        </div>

        <div className="px-4 py-4 border-t border-outline-variant/20 space-y-1">
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-secondary hover:text-primary text-xs transition-colors rounded-xl hover:bg-white/5">
            <span className="material-symbols-outlined text-sm">settings</span>
            设置
          </a>
          <a href="#" className="flex items-center gap-3 px-4 py-2 text-secondary hover:text-primary text-xs transition-colors rounded-xl hover:bg-white/5">
            <span className="material-symbols-outlined text-sm">help_outline</span>
            帮助
          </a>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-2 text-error hover:bg-error/10 text-xs transition-colors w-full rounded-xl hover:bg-white/5"
          >
            <span className="material-symbols-outlined text-sm">logout</span>
            退出登录
          </button>
        </div>
      </aside>

      <div className="md:ml-64 flex-1 flex flex-col min-h-screen">
        <header className="sticky top-0 z-50 bg-[#060e20]/80 backdrop-blur-xl border-b border-outline-variant/40 shadow-[0_10px_40px_rgba(0,0,0,0.28)] flex justify-between items-center px-6 py-3">
          <div className="flex items-center gap-6">
            <span className="text-xl font-headline font-black text-primary tracking-tighter md:hidden">HuiMind</span>
            <nav className="hidden md:flex items-center gap-4">
              <Link href="/tutor" className={`flex items-center gap-2 font-headline font-bold tracking-tight text-sm transition-colors ${
                pathname === "/tutor" || pathname.startsWith("/tutor/")
                  ? "text-primary border-b-2 border-primary pb-0.5"
                  : "text-secondary hover:text-primary"
              }`}>
                <span className="material-symbols-outlined text-[18px]" style={pathname === "/tutor" ? { fontVariationSettings: "'FILL' 1" } : {}}>
                  psychology
                </span>
                <span>通用学习</span>
              </Link>
              {sceneItems.map((item) => {
                const active = item.enabled && (pathname === item.href || pathname.startsWith(item.href + "/"));
                if (!item.enabled) {
                  return (
                    <div key={item.label} className="flex items-center gap-2 font-headline font-bold tracking-tight text-sm text-outline cursor-not-allowed">
                      <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                      <span>{item.label}</span>
                      <span className="text-[10px] text-outline">待开放</span>
                    </div>
                  );
                }
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-2 font-headline font-bold tracking-tight text-sm transition-colors ${
                      active ? "text-primary border-b-2 border-primary pb-0.5" : "text-secondary hover:text-primary"
                    }`}
                  >
                    <span className="material-symbols-outlined text-[18px]">
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-secondary p-0.5 cursor-pointer">
              <div className="w-full h-full rounded-full bg-surface flex items-center justify-center">
                <span className="text-[10px] font-headline font-bold text-primary">{nickname.slice(0, 1).toUpperCase()}</span>
              </div>
            </div>
          </div>
        </header>

        {!hidePageHeader && (
          <div className="px-8 pt-8 pb-2">
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-primary">{badge}</span>
            <h2 className="text-3xl font-headline font-bold text-on-surface mt-1">{title}</h2>
            <p className="text-on-surface-variant text-sm mt-1">{subtitle}</p>
          </div>
        )}

        <div className="flex-1 px-8 py-6 pb-16">
          {children}
        </div>

        <div className="hidden md:flex fixed bottom-0 left-64 right-0 bg-[#091328]/90 backdrop-blur-md border-t border-outline-variant/40 h-11 z-50 items-center justify-between px-8 shadow-[0_-10px_30px_rgba(0,0,0,0.22)]">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-tertiary">
              <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>timer</span>
              <span className="font-label text-[10px] uppercase tracking-widest font-bold">专注中：25:00</span>
            </div>
            <div className="flex items-center gap-2 text-outline">
              <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>local_fire_department</span>
              <span className="font-label text-[10px] uppercase tracking-widest font-bold">连续学习：12 天</span>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="font-label text-[10px] uppercase tracking-widest font-bold text-outline">本次经验</span>
              <div className="w-28 h-1.5 bg-surface-container-lowest rounded-full overflow-hidden">
                <div className="h-full bg-primary w-2/3"></div>
              </div>
              <span className="font-label text-[10px] font-bold text-primary">+150</span>
            </div>
            <button className="bg-primary/10 text-primary border border-primary/20 px-4 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest hover:bg-primary hover:text-on-primary transition-all">
              结束学习
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
