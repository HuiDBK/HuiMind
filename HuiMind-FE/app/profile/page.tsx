"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { isLoggedIn } from "@/lib/auth";
import { useMvpData } from "@/hooks/use-mvp-data";
import type { SceneId } from "@/lib/types";

export default function ProfilePage() {
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

  const pendingReviews = reviewTasks.filter((t) => t.status === "pending");
  const completedReviews = reviewTasks.filter((t) => t.status === "completed");

  return (
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => router.push("/")}
              className="w-10 h-10 rounded-xl bg-surface-container-high/60 flex items-center justify-center hover:bg-primary/10 transition-colors"
            >
              <span className="material-symbols-outlined text-secondary">arrow_back</span>
            </button>
            <h1 className="text-lg font-headline font-bold text-on-surface">我的</h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-6 space-y-6">
        {/* AI Buddy Profile */}
        <section className="glass-card rounded-3xl border border-outline-variant/10 p-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/30 to-secondary/30 flex items-center justify-center">
              <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
            </div>
            <div className="flex-1">
              <h2 className="text-xl font-headline font-bold text-on-surface">{buddyProfile?.name ?? "小智"}</h2>
              <p className="text-sm text-outline">{buddyProfile?.persona ?? "严师型"} · AI 学习搭子</p>
            </div>
            <button
              type="button"
              className="px-4 py-2 rounded-xl text-sm font-bold bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
            >
              编辑
            </button>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-surface-container-high/40 rounded-xl p-4 text-center">
              <p className="text-2xl font-headline font-black text-primary">{documents.length}</p>
              <p className="text-xs text-outline mt-1">学习资料</p>
            </div>
            <div className="bg-surface-container-high/40 rounded-xl p-4 text-center">
              <p className="text-2xl font-headline font-black text-tertiary">{pendingReviews.length}</p>
              <p className="text-xs text-outline mt-1">待复习</p>
            </div>
            <div className="bg-surface-container-high/40 rounded-xl p-4 text-center">
              <p className="text-2xl font-headline font-black text-error">{weakPoints.length}</p>
              <p className="text-xs text-outline mt-1">薄弱点</p>
            </div>
          </div>
        </section>

        {/* Scene Filter */}
        <section className="flex items-center gap-2 overflow-x-auto pb-2">
          {["general", "career", "kaoyan", "gongkao"].map((scene) => {
            const isActive = selectedScene === scene;
            const labels: Record<string, string> = {
              general: "通用",
              career: "求职",
              kaoyan: "考研",
              gongkao: "考公",
            };
            return (
              <button
                key={scene}
                type="button"
                onClick={() => setSelectedScene(scene as SceneId)}
                className={`px-4 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-primary text-on-primary"
                    : "bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10"
                }`}
              >
                {labels[scene]}
              </button>
            );
          })}
        </section>

        {/* Weak Points */}
        <section className="glass-card rounded-3xl border border-outline-variant/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-headline font-bold text-on-surface">薄弱知识点</h3>
            <span className="text-xs bg-error/10 text-error px-2 py-1 rounded-full font-bold">{weakPoints.length} 项</span>
          </div>
          {weakPoints.length > 0 ? (
            <div className="space-y-3">
              {weakPoints.map((wp) => (
                <div key={wp.id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40">
                  <div className="flex-1">
                    <p className="text-sm font-bold text-on-surface">{wp.concept}</p>
                    <p className="text-xs text-outline mt-1">场景：{wp.scene_id}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-error">{wp.correct_rate}%</p>
                    <p className="text-xs text-outline">正确率</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <span className="material-symbols-outlined text-outline text-4xl">check_circle</span>
              <p className="text-sm text-outline mt-2">暂无薄弱知识点</p>
            </div>
          )}
        </section>

        {/* Review Tasks */}
        <section className="glass-card rounded-3xl border border-outline-variant/10 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-headline font-bold text-on-surface">复习任务</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs bg-tertiary/10 text-tertiary px-2 py-1 rounded-full font-bold">{pendingReviews.length} 待复习</span>
              <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full font-bold">{completedReviews.length} 已完成</span>
            </div>
          </div>
          {reviewTasks.length > 0 ? (
            <div className="space-y-3">
              {reviewTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${task.status === "completed" ? "bg-primary/20" : "bg-tertiary/20"}`}>
                      <span className={`material-symbols-outlined text-base ${task.status === "completed" ? "text-primary" : "text-tertiary"}`}>
                        {task.status === "completed" ? "check" : "schedule"}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-bold text-on-surface">{task.concept}</p>
                      <p className="text-xs text-outline">到期：{task.due_at}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-bold ${task.status === "completed" ? "bg-primary/10 text-primary" : "bg-tertiary/10 text-tertiary"}`}>
                    {task.status === "completed" ? "已完成" : "待复习"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <span className="material-symbols-outlined text-outline text-4xl">event_note</span>
              <p className="text-sm text-outline mt-2">暂无复习任务</p>
            </div>
          )}
        </section>

        {/* Quick Actions */}
        <section className="glass-card rounded-3xl border border-outline-variant/10 p-6">
          <h3 className="font-headline font-bold text-on-surface mb-4">快捷操作</h3>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => router.push("/knowledge-base")}
              className="flex items-center gap-3 p-4 rounded-xl bg-surface-container-high/40 hover:bg-primary/10 transition-colors group"
            >
              <span className="material-symbols-outlined text-secondary text-xl group-hover:text-primary">folder_open</span>
              <span className="text-sm font-bold text-on-surface">管理资料</span>
            </button>
            <button
              type="button"
              onClick={() => router.push("/")}
              className="flex items-center gap-3 p-4 rounded-xl bg-surface-container-high/40 hover:bg-primary/10 transition-colors group"
            >
              <span className="material-symbols-outlined text-secondary text-xl group-hover:text-primary">chat</span>
              <span className="text-sm font-bold text-on-surface">开始学习</span>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
