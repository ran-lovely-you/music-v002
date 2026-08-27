import type {
  GenerateRequest,
  GenerationResult,
  OptionsResponse,
  ProjectRecord,
  PromptSet,
  YoutubeMetadata,
} from "../types";

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    let detail = `通信エラーが発生しました（HTTP ${resp.status}）。`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // レスポンスがJSONでない場合はデフォルトメッセージを使用する
    }
    throw new ApiError(detail);
  }
  return (await resp.json()) as T;
}

export function getOptions(): Promise<OptionsResponse> {
  return request<OptionsResponse>("/api/options");
}

export function generatePrompt(req: GenerateRequest): Promise<PromptSet> {
  return request<PromptSet>("/api/prompt/generate", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function generateBgm(req: GenerateRequest): Promise<GenerationResult> {
  return request<GenerationResult>("/api/bgm/generate", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function exportUrl(generationId: string, format: "wav" | "mp3" | "flac"): string {
  return `/api/bgm/${generationId}/export?format=${format}`;
}

export async function downloadExport(generationId: string, format: "wav" | "mp3" | "flac"): Promise<Blob> {
  const resp = await fetch(exportUrl(generationId, format), { method: "POST" });
  if (!resp.ok) {
    let detail = "書き出しに失敗しました。";
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new ApiError(detail);
  }
  return await resp.blob();
}

export function saveProject(generationId: string, title: string): Promise<ProjectRecord> {
  return request<ProjectRecord>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ generation_id: generationId, title }),
  });
}

export function listProjects(): Promise<ProjectRecord[]> {
  return request<ProjectRecord[]>("/api/projects");
}

export function deleteProject(projectId: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>(`/api/projects/${projectId}`, { method: "DELETE" });
}

export function getYoutubeMetadata(req: GenerateRequest): Promise<YoutubeMetadata> {
  return request<YoutubeMetadata>("/api/youtube/metadata", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
