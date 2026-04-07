"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { isLoggedIn } from "@/lib/auth";
import { useMvpData } from "@/hooks/use-mvp-data";
import { StreamingChat, sceneOptions } from "@/components/streaming-chat";
import type { SceneId } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const [selectedScene, setSelectedScene] = useState<SceneId>("general");
  const { buddyProfile, documents, weakPoints, reviewTasks, loading } = useMvpData(selectedScene);

  useEffect(() => {
    if (!isLoggedIn()) {
      router.replace("/login");
    }
  }, [router]);

  if (!isLoggedIn()) {
    return null;
  }

  const currentSceneInfo = sceneOptions.find((s) => s.id === selectedScene);
  const pendingReviews = reviewTasks.filter((t) => t.status === "pending").length;
  const weakCount = weakPoints.length;

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            </div>
            <div>
              <h1 className="text-lg font-headline font-bold text-on-surface">HuiMind</h1>
              <p className="text-[10px] text-outline">AI 伴学平台</p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => router.push("/knowledge-base")}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10 transition-colors border border-outline-variant/10"
            >
              <span className="material-symbols-outlined text-base">folder_open</span>
              知识库
            </button>
            <button
              type="button"
              onClick={() => router.push("/profile")}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10 transition-colors border border-outline-variant/10"
            >
              <span className="material-symbols-outlined text-base">person</span>
              我的
            </button>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-6">
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          {/* Chat area - main */}
          <div className="col-span-12 lg:col-span-8">
            <div className="h-full flex flex-col glass-card rounded-3xl border border-outline-variant/10 p-6">
              {/* AI Buddy greeting */}
              <div className="flex items-center gap-3 mb-4 pb-4 border-b border-outline-variant/10">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/30 to-secondary/30 flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                </div>
                <div className="flex-1">
                  <h2 className="text-lg font-headline font-bold text-on-surface">{buddyProfile?.name ?? "小智"}</h2>
                  <p className="text-xs text-outline">{currentSceneInfo?.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] bg-tertiary/10 text-tertiary px-2.5 py-1 rounded-full font-label border border-tertiary/20">
                    {documents.length} 份资料
                  </span>
                </div>
              </div>

              {/* Streaming chat */}
              <div className="flex-1 min-h-0">
                <StreamingChat
                  sceneId={selectedScene}
                  onSceneChange={setSelectedScene}
                  showSceneSwitcher={true}
                  placeholder={`向 ${buddyProfile?.name ?? "小智"} 提问，开始学习之旅...`}
                />
              </div>
            </div>
          </div>

          {/* Right sidebar */}
          <aside className="col-span-12 lg:col-span-4 space-y-4 overflow-y-auto">
            {/* Quick stats */}
            <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary text-base">analytics</span>
                <h3 className="font-headline font-bold text-on-surface text-sm">学习概览</h3>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface-container-high/40 rounded-xl p-3 text-center">
                  <p className="text-2xl font-headline font-black text-primary">{documents.length}</p>
                  <p className="text-[10px] text-outline">资料</p>
                </div>
                <div className="bg-surface-container-high/40 rounded-xl p-3 text-center">
                  <p className="text-2xl font-headline font-black text-error">{weakCount}</p>
                  <p className="text-[10px] text-outline">薄弱点</p>
                </div>
                <div className="bg-surface-container-high/40 rounded-xl p-3 text-center">
                  <p className="text-2xl font-headline font-black text-tertiary">{pendingReviews}</p>
                  <p className="text-[10px] text-outline">待复习</p>
                </div>
              </div>
            </div>

            {/* Pending reviews */}
            {reviewTasks.length > 0 && (
              <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-tertiary text-base">event_note</span>
                    <h3 className="font-headline font-bold text-on-surface text-sm">待复习任务</h3>
                  </div>
                  <span className="text-[10px] bg-tertiary/10 text-tertiary px-2 py-0.5 rounded-full font-bold">{pendingReviews} 项</span>
                </div>
                <div className="space-y-2">
                  {reviewTasks.slice(0, 3).map((task) => (
                    <div key={task.id} className="flex items-center gap-3 p-2 rounded-xl bg-surface-container-high/40">
                      <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                        <span className="material-symbols-outlined text-xs text-secondary">task_alt</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-bold text-on-surface truncate">{task.concept}</p>
                        <p className="text-[10px] text-outline">{task.due_at}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick actions */}
            <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-secondary text-base">bolt</span>
                <h3 className="font-headline font-bold text-on-surface text-sm">快捷入口</h3>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => router.push("/knowledge-base")}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl bg-surface-container-high/40 hover:bg-primary/10 transition-colors group"
                >
                  <span className="material-symbols-outlined text-secondary text-xl group-hover:text-primary">upload_file</span>
                  <span className="text-xs font-bold text-on-surface">上传资料</span>
                </button>
                <button
                  type="button"
                  onClick={() => router.push("/profile")}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl bg-surface-container-high/40 hover:bg-primary/10 transition-colors group"
                >
                  <span className="material-symbols-outlined text-secondary text-xl group-hover:text-primary">auto_graph</span>
                  <span className="text-xs font-bold text-on-surface">学习记录</span>
                </button>
              </div>
            </div>

            {/* Weak points */}
            {weakPoints.length > 0 && (
              <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-error text-base">warning</span>
                    <h3 className="font-headline font-bold text-on-surface text-sm">薄弱知识点</h3>
                  </div>
                  <span className="text-[10px] bg-error/10 text-error px-2 py-0.5 rounded-full font-bold">{weakCount} 项</span>
                </div>
                <div className="space-y-2">
                  {weakPoints.slice(0, 3).map((wp) => (
                    <div key={wp.id} className="flex items-center justify-between p-2 rounded-xl bg-surface-container-high/40">
                      <span className="text-xs text-on-surface truncate flex-1">{wp.concept}</span>
                      <span className="text-[10px] text-error font-bold ml-2">{wp.correct_rate}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
