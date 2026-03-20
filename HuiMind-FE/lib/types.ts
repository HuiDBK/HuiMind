export type SceneId = "general" | "career" | "kaoyan" | "gongkao";

export type SceneNavItem = {
  scene_id: SceneId;
  label: string;
  description: string;
  route: string;
  icon: string;
  enabled: boolean;
};

export type ApiResponse<T> = {
  code: number;
  message: string;
  data: T;
};

export type PageData<T> = {
  total: number;
  data_list: T[];
};

export type UserInfo = {
  id: number;
  email: string;
  nickname: string;
  default_scene_id: SceneId;
};

export type LoginData = {
  token: string;
  user: {
    id: number;
    email: string;
    nickname: string;
  };
};

export type SceneItem = {
  scene_id: SceneId;
  name: string;
  description: string;
  enabled_tools: string[];
};

export type DashboardCard = {
  title: string;
  subtitle: string;
};

export type DashboardData = {
  current_scene_id: SceneId;
  quick_actions: string[];
  cards: DashboardCard[];
};

export type DocumentItem = {
  id: number;
  scene_id: SceneId;
  doc_type: string;
  filename: string;
  status: string;
  summary: string;
  created_at: string;
};

export type WeakPointItem = {
  id: number;
  scene_id: SceneId;
  concept: string;
  source_type: string;
  wrong_count: number;
  correct_rate: number;
  mastery_level: string;
  next_review_at: string;
};

export type ReviewTaskItem = {
  id: number;
  scene_id: SceneId;
  concept: string;
  due_at: string;
  status: string;
};

export type BuddyProfile = {
  buddy_id: number;
  name: string;
  persona: "gentle" | "strict" | "energetic" | "calm";
  memory_summary: string;
  last_interaction_at: string | null;
};

export type CitationItem = {
  document_id: number;
  source_label: string;
  source_locator: string;
  quote: string;
};

export type AskData = {
  session_id: number;
  answer: string;
  citations: CitationItem[];
  insufficient_context: boolean;
};

export type BuddyChatData = {
  reply: string;
  memory_summary: string;
  suggested_actions: string[];
};

export type ResumeDiagnosisData = {
  diagnosis_id: number;
  match_score: number;
  matched_keywords: string[];
  missing_keywords: string[];
  risky_phrases: Array<{ original: string; reason: string }>;
  rewrite_suggestions: Array<{ original: string; rewritten: string }>;
  summary: string;
};

export type InterviewQuestion = {
  turn_id: number;
  question_order: number;
  question: string;
};

export type InterviewSessionCreateData = {
  session_id: number;
  status: string;
  questions: InterviewQuestion[];
};

export type InterviewSessionDetail = {
  id: number;
  scene_id: "career";
  status: string;
  overall_score: number;
  summary: string;
  turns: Array<{
    turn_id: number;
    question_order: number;
    question: string;
    answer: string | null;
    score: number | null;
  }>;
};

export type InterviewAnswerData = {
  session_id: number;
  turn_id: number;
  score: number;
  feedback: {
    relevance: number;
    clarity: number;
    evidence: number;
    structure: number;
    comment: string;
  };
  weak_points: string[];
  session_status: string;
};
