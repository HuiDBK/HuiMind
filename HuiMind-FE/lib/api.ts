import type {
  ApiResponse,
  AskData,
  BuddyChatData,
  BuddyProfile,
  DashboardData,
  DocumentItem,
  InterviewAnswerData,
  InterviewSessionCreateData,
  InterviewSessionDetail,
  LoginData,
  PageData,
  ResumeDiagnosisData,
  ReviewTaskItem,
  SceneItem,
  UserInfo,
  WeakPointItem,
} from "@/lib/types";
import { clearAuthSession, getAuthToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAuthSession();
    }
    throw new Error(`请求失败: ${response.status}`);
  }

  const payload = (await response.json()) as ApiResponse<T>;
  if (payload.code !== 0) {
    throw new Error(payload.message || "业务请求失败");
  }

  return payload.data;
}

export async function login(email: string, password: string) {
  return request<LoginData>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return request<UserInfo>("/me");
}

export async function getDashboard() {
  return request<DashboardData>("/dashboard");
}

export async function getScenes() {
  const data = await request<PageData<SceneItem>>("/scenes");
  return data.data_list;
}

export async function getDocuments(sceneId?: string) {
  const query = sceneId ? `?scene_id=${sceneId}` : "";
  const data = await request<PageData<DocumentItem>>(`/documents${query}`);
  return data.data_list;
}

export async function uploadFile(payload: { scene_id?: string; file: globalThis.File }) {
  const form = new FormData();
  form.append("file", payload.file);
  if (payload.scene_id) {
    form.append("scene_id", payload.scene_id);
  }
  return request<{ file_id: number; oss_key: string; filename: string }>(`/files/upload`, { method: "POST", body: form });
}

export async function createDocumentFromFile(payload: { scene_id: string; doc_type: string; file_id: number; oss_key: string }) {
  return request<{ document_id: number; status: string; filename: string }>(`/documents/upload`, { method: "POST", body: JSON.stringify(payload) });
}

export async function createJd(payload: { scene_id: "career"; title: string; content?: string; source_url?: string }) {
  return request<{ document_id: number; status: string; filename: string }>(`/documents/jd`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function askQuestion(payload: { scene_id: string; session_id?: number; question: string }) {
  return request<AskData>("/qa/ask", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getBuddyProfile() {
  return request<BuddyProfile>("/buddy/profile");
}

export async function updateBuddyProfile(payload: { name: string; persona: string }) {
  return request<BuddyProfile>("/buddy/profile", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function chatWithBuddy(payload: { scene_id: string; message: string }) {
  return request<BuddyChatData>("/buddy/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getWeakPoints(sceneId?: string) {
  const query = sceneId ? `?scene_id=${sceneId}` : "";
  const data = await request<PageData<WeakPointItem>>(`/memory/weak-points${query}`);
  return data.data_list;
}

export async function getReviewTasks(sceneId?: string) {
  const query = sceneId ? `?scene_id=${sceneId}` : "";
  const data = await request<PageData<ReviewTaskItem>>(`/review/tasks${query}`);
  return data.data_list;
}

export async function completeReviewTask(taskId: number, result: "mastered" | "review_again") {
  return request<{ task_id: number; status: string; next_review_at: string }>(`/review/tasks/${taskId}/complete`, {
    method: "POST",
    body: JSON.stringify({ result }),
  });
}

export async function runResumeDiagnosis(payload: { scene_id: "career"; resume_doc_id: number; jd_doc_id: number }) {
  return request<ResumeDiagnosisData>("/career/resume-diagnosis", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createInterviewSession(payload: { scene_id: "career"; jd_doc_id: number; mode: "standard" | "pressure" }) {
  return request<InterviewSessionCreateData>("/career/interview/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getInterviewSession(sessionId: number) {
  return request<InterviewSessionDetail>(`/career/interview/sessions/${sessionId}`);
}

export async function answerInterviewQuestion(payload: { sessionId: number; turnId: number; answer: string }) {
  return request<InterviewAnswerData>(`/career/interview/sessions/${payload.sessionId}/answer`, {
    method: "POST",
    body: JSON.stringify({ turn_id: payload.turnId, answer: payload.answer }),
  });
}
