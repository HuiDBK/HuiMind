"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { clearAuthSession, getStoredUser, isLoggedIn } from "@/lib/auth";

const primaryNavItems = [
  { href: "/dashboard", label: "学习中枢", icon: "space_dashboard" },
  { href: "/tutor", label: "学习辅导", icon: "psychology" },
  { href: "/progress", label: "复习进度", icon: "query_stats" },
];

const sceneItems = [
  { href: "/career", label: "职业发展", icon: "work", enabled: true },
  { href: "#", label: "考研", icon: "school", enabled: false },
  { href: "#", label: "考公", icon: "account_balance", enabled: false },
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
    if (!isLoggedIn()) {
      router.replace("/login");
      return;
    }
    const user = getStoredUser();
    if (user?.nickname) setNickname(user.nickname);
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

          <div className="rounded-2xl border border-transparent hover:border-outline-variant/20 hover:bg-white/5 transition-all">
            <button
              type="button"
              onClick={() => setSceneMenuOpen((prev) => !prev)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-all rounded-2xl ${
                sceneActive || sceneMenuOpen ? "text-primary bg-primary/10" : "text-secondary"
              }`}
            >
              <span className="material-symbols-outlined text-[20px]" style={sceneActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
                category
              </span>
              <span className="font-body flex-1 text-left">场景</span>
              <span className="material-symbols-outlined text-[18px] transition-transform" style={{ transform: sceneMenuOpen ? "rotate(180deg)" : "rotate(0deg)" }}>
                expand_more
              </span>
            </button>
            {sceneMenuOpen && (
              <div className="px-3 pb-3 space-y-1">
                {sceneItems.map((item) => {
                  const active = item.enabled && (pathname === item.href || pathname.startsWith(item.href + "/"));
                  const itemClass = `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                    item.enabled
                      ? active
                        ? "bg-surface-container-high text-primary border border-primary/20"
                        : "text-on-surface hover:bg-white/5 hover:text-primary border border-transparent"
                      : "text-outline cursor-not-allowed bg-white/5 border border-transparent opacity-70"
                  }`;

                  if (!item.enabled) {
                    return (
                      <div key={item.label} className={itemClass}>
                        <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                        <span className="flex-1">{item.label}</span>
                        <span className="text-[10px] font-label">敬请期待</span>
                      </div>
                    );
                  }

                  return (
                    <Link key={item.href} href={item.href} className={itemClass}>
                      <span className="material-symbols-outlined text-[18px]" style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                        {item.icon}
                      </span>
                      <span className="flex-1">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </nav>

        <div className="px-6 py-4">
          <button className="w-full bg-primary text-on-primary font-headline font-bold py-3 rounded-xl shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all text-sm">
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
            className="flex items-center gap-3 px-4 py-2 text-error/80 hover:text-error text-xs transition-colors w-full rounded-xl hover:bg-white/5"
          >
            <span className="material-symbols-outlined text-sm">logout</span>
            退出登录
          </button>
        </div>
      </aside>

      <div className="md:ml-64 flex-1 flex flex-col min-h-screen">
        <header className="sticky top-0 z-50 bg-[#060e20]/80 backdrop-blur-xl border-b border-outline-variant/40 shadow-[0_10px_40px_rgba(0,0,0,0.28)] flex justify-between items-center px-6 py-3">
          <div className="flex items-center gap-8">
            <span className="text-xl font-headline font-black text-primary tracking-tighter md:hidden">HuiMind</span>
            <nav className="hidden md:flex items-center gap-6">
              {primaryNavItems.map((item) => {
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`font-headline font-bold tracking-tight text-sm transition-colors ${
                      active ? "text-primary border-b-2 border-primary pb-0.5" : "text-secondary hover:text-primary"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setSceneMenuOpen((prev) => !prev)}
                  className={`flex items-center gap-1 font-headline font-bold tracking-tight text-sm transition-colors ${
                    sceneActive || sceneMenuOpen ? "text-primary" : "text-secondary hover:text-primary"
                  }`}
                >
                  场景
                  <span className="material-symbols-outlined text-base">expand_more</span>
                </button>
                {sceneMenuOpen && (
                  <div className="absolute top-9 left-0 min-w-44 rounded-2xl border border-outline-variant/30 bg-[#101a31]/95 backdrop-blur-xl shadow-[0_18px_50px_rgba(0,0,0,0.32)] p-2 space-y-1">
                    {sceneItems.map((item) => {
                      const active = item.enabled && (pathname === item.href || pathname.startsWith(item.href + "/"));
                      const itemClass = `flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${
                        item.enabled
                          ? active
                            ? "bg-primary/10 text-primary"
                            : "text-on-surface hover:bg-surface-container-high hover:text-primary"
                          : "text-outline bg-background/40 cursor-not-allowed"
                      }`;

                      if (!item.enabled) {
                        return (
                          <div key={item.label} className={itemClass}>
                            <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                            <span className="flex-1">{item.label}</span>
                            <span className="text-[10px]">待开放</span>
                          </div>
                        );
                      }

                      return (
                        <Link key={item.href} href={item.href} className={itemClass}>
                          <span className="material-symbols-outlined text-[18px]">{item.icon}</span>
                          <span>{item.label}</span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center bg-white/5 rounded-full px-4 py-1.5 border border-outline-variant/30 shadow-sm">
              <span className="material-symbols-outlined text-sm text-secondary mr-2">search</span>
              <input className="bg-transparent border-none outline-none text-xs w-40 text-on-surface placeholder:text-outline" placeholder="搜索知识内容..." />
            </div>
            <button className="p-2 text-secondary hover:bg-primary/10 rounded-lg transition-all active:scale-95">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <button className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-all active:scale-95">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>workspace_premium</span>
            </button>
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
