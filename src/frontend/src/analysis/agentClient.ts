// AG-UI 프로토콜로 에이전트 앱(/agent)과 통신하는 클라이언트.
import { EventType, HttpAgent, type BaseEvent } from "@ag-ui/client";
import type { AnalysisError, AnalysisResult } from "../types";

export interface AnalysisProgress {
  label: string;
}

export class AgentError extends Error {}

type TextContentEvent = BaseEvent & { messageId: string; delta: string };
type RunErrorEvent = BaseEvent & { message: string };

function extractAnalysisPayload(
  texts: string[],
): AnalysisResult | AnalysisError | null {
  let found: AnalysisResult | AnalysisError | null = null;
  for (const text of texts) {
    const trimmed = text.trim();
    const start = trimmed.indexOf("{");
    const end = trimmed.lastIndexOf("}");
    if (start < 0 || end <= start) continue;
    try {
      const parsed = JSON.parse(trimmed.slice(start, end + 1)) as {
        type?: string;
      };
      if (parsed.type === "analysis_result" || parsed.type === "analysis_error") {
        found = parsed as AnalysisResult | AnalysisError;
      }
    } catch {
      // JSON이 아닌 메시지(에이전트 중간 산출물)는 무시한다.
    }
  }
  return found;
}

export function runAnalysis(
  prompt: string,
  onProgress: (progress: AnalysisProgress) => void,
  endpoint = "/agent",
): Promise<AnalysisResult> {
  const agent = new HttpAgent({ url: endpoint });
  const input = {
    threadId: `thread-${Date.now()}`,
    runId: `run-${Date.now()}`,
    messages: [{ id: "m-1", role: "user" as const, content: prompt }],
    tools: [],
    context: [],
    state: {},
    forwardedProps: {},
  };

  return new Promise<AnalysisResult>((resolve, reject) => {
    const messageTexts = new Map<string, string>();
    let settled = false;

    const finish = () => {
      if (settled) return;
      settled = true;
      const payload = extractAnalysisPayload([...messageTexts.values()]);
      if (!payload) {
        reject(new AgentError("에이전트 분석 결과를 해석하지 못했습니다."));
      } else if (payload.type === "analysis_error") {
        reject(new AgentError(payload.message));
      } else {
        resolve(payload);
      }
    };

    agent.run(input).subscribe({
      next: (event: BaseEvent) => {
        switch (event.type) {
          case EventType.RUN_STARTED:
            onProgress({ label: "멀티에이전트 분석을 시작했습니다." });
            break;
          case EventType.TEXT_MESSAGE_START:
            onProgress({ label: "에이전트 평가 결과를 수신하는 중입니다." });
            break;
          case EventType.TEXT_MESSAGE_CONTENT: {
            const { messageId, delta } = event as TextContentEvent;
            messageTexts.set(messageId, (messageTexts.get(messageId) ?? "") + delta);
            break;
          }
          case EventType.RUN_FINISHED:
            onProgress({ label: "분석이 완료되었습니다." });
            finish();
            break;
          case EventType.RUN_ERROR: {
            if (!settled) {
              settled = true;
              reject(new AgentError((event as RunErrorEvent).message || "분석 실행에 실패했습니다."));
            }
            break;
          }
          default:
            break;
        }
      },
      error: (err: unknown) => {
        if (!settled) {
          settled = true;
          reject(
            err instanceof Error
              ? err
              : new AgentError("에이전트 서버와 통신하지 못했습니다."),
          );
        }
      },
      complete: () => finish(),
    });
  });
}
