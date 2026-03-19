"use client";

import { useCallback, useEffect, useState } from "react";

import { getBuddyProfile, getDashboard, getDocuments, getReviewTasks, getScenes, getWeakPoints } from "@/lib/api";
import type { BuddyProfile, DashboardData, DocumentItem, ReviewTaskItem, SceneId, SceneItem, WeakPointItem } from "@/lib/types";

type UseMvpDataResult = {
  loading: boolean;
  error: string;
  dashboard: DashboardData | null;
  scenes: SceneItem[];
  documents: DocumentItem[];
  weakPoints: WeakPointItem[];
  reviewTasks: ReviewTaskItem[];
  buddyProfile: BuddyProfile | null;
  reload: () => Promise<void>;
};

export function useMvpData(sceneId: SceneId): UseMvpDataResult {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [weakPoints, setWeakPoints] = useState<WeakPointItem[]>([]);
  const [reviewTasks, setReviewTasks] = useState<ReviewTaskItem[]>([]);
  const [buddyProfile, setBuddyProfile] = useState<BuddyProfile | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [dashboardData, sceneList, documentList, weakPointList, reviewTaskList, buddy] = await Promise.all([
        getDashboard(),
        getScenes(),
        getDocuments(sceneId),
        getWeakPoints(sceneId),
        getReviewTasks(sceneId),
        getBuddyProfile(),
      ]);

      setDashboard(dashboardData);
      setScenes(sceneList);
      setDocuments(documentList);
      setWeakPoints(weakPointList);
      setReviewTasks(reviewTaskList);
      setBuddyProfile(buddy);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载数据失败");
    } finally {
      setLoading(false);
    }
  }, [sceneId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { loading, error, dashboard, scenes, documents, weakPoints, reviewTasks, buddyProfile, reload };
}
