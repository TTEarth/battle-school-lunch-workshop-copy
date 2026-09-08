import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { AgentError, runAnalysis } from "../analysis/agentClient";
import {
  buildDefaultPrompt,
  isSelectableDate,
  selectableDateRange,
} from "../analysis/prompt";
import { pickRandomSchools } from "../analysis/randomSchools";
import type { AnalysisResult, School } from "../types";

type SchoolPhase = "loading" | "done" | "error";
type AnalysisPhase = "idle" | "running" | "done";

function schoolKey(school: School): string {
  return `${school.atpt_code}-${school.school_code}`;
}

export default function AnalysisPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [schoolPhase, setSchoolPhase] = useState<SchoolPhase>("loading");
  const [selected, setSelected] = useState<School[]>([]);
  const [date, setDate] = useState("");
  const [prompt, setPrompt] = useState("");
  const [promptTouched, setPromptTouched] = useState(false);
  const [phase, setPhase] = useState<AnalysisPhase>("idle");
  const [progress, setProgress] = useState<string[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");

  const dateRange = useMemo(() => selectableDateRange(), []);

  const loadSchools = async () => {
    setSchoolPhase("loading");
    setSelected([]);
    try {
      const picked = await pickRandomSchools(10);
      setSchools(picked);
      setSchoolPhase("done");
    } catch (e) {
      setSchools([]);
      setSchoolPhase("error");
      setError(
        e instanceof ApiError ? e.message : "무작위 학교 목록을 불러오지 못했습니다.",
      );
    }
  };

  useEffect(() => {
    void loadSchools();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 학교 2곳과 날짜가 정해지면 기본 프롬프트를 생성한다(사용자 수정 전까지).
  useEffect(() => {
    if (selected.length === 2 && date && !promptTouched) {
      setPrompt(buildDefaultPrompt([selected[0], selected[1]], date));
    }
  }, [selected, date, promptTouched]);

  const toggleSchool = (school: School) => {
    setError("");
    setSelected((prev) => {
      const exists = prev.some((s) => schoolKey(s) === schoolKey(school));
      if (exists) return prev.filter((s) => schoolKey(s) !== schoolKey(school));
      if (prev.length >= 2) return prev;
      return [...prev, school];
    });
  };

  const regeneratePrompt = () => {
    if (selected.length === 2 && date) {
      setPrompt(buildDefaultPrompt([selected[0], selected[1]], date));
      setPromptTouched(false);
    }
  };

  const handleAnalyze = async () => {
    if (selected.length !== 2) {
      setError("비교할 학교를 정확히 2개 선택해 주세요.");
      return;
    }
    if (!date || !isSelectableDate(date)) {
      setError("이번 달 또는 직전 달의 날짜를 선택해 주세요.");
      return;
    }
    if (!prompt.trim()) {
      setError("분석 프롬프트를 작성해 주세요.");
      return;
    }
    setError("");
    setResult(null);
    setProgress([]);
    setPhase("running");
    try {
      const analysis = await runAnalysis(prompt, (p) =>
        setProgress((prev) =>
          prev[prev.length - 1] === p.label ? prev : [...prev, p.label],
        ),
      );
      setResult(analysis);
      setPhase("done");
    } catch (e) {
      setPhase("idle");
      setError(
        e instanceof AgentError || e instanceof Error
          ? e.message
          : "급식 분석에 실패했습니다.",
      );
    }
  };

  const winnerName = (r: AnalysisResult): string | null => {
    if (r.is_tie || !r.winner_school_code) return null;
    return (
      r.schools.find((s) => s.school_code === r.winner_school_code)?.school_name ?? null
    );
  };

  return (
    <section className="page">
      <h2 className="page-title">급식 분석</h2>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}

      <section className="step" aria-labelledby="analysis-step1">
        <h3 id="analysis-step1">1단계. 학교 2곳 선택 (무작위 10개)</h3>
        <div className="row">
          <button onClick={loadSchools} disabled={schoolPhase === "loading"}>
            {schoolPhase === "loading" ? "학교 목록 불러오는 중..." : "다른 학교 보기"}
          </button>
          <span className="meta">선택됨: {selected.length} / 2</span>
        </div>
        {schoolPhase === "error" && (
          <p className="notice">학교 목록을 불러오지 못했습니다. 다시 시도해 주세요.</p>
        )}
        <ul className="school-list">
          {schools.map((school) => {
            const isSelected = selected.some(
              (s) => schoolKey(s) === schoolKey(school),
            );
            return (
              <li key={schoolKey(school)}>
                <button
                  className={isSelected ? "selected" : ""}
                  onClick={() => toggleSchool(school)}
                  aria-pressed={isSelected}
                  disabled={!isSelected && selected.length >= 2}
                >
                  <strong>{school.school_name}</strong>{" "}
                  <span className="meta">
                    {school.atpt_name}
                    {school.school_kind ? ` · ${school.school_kind}` : ""}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="step" aria-labelledby="analysis-step2">
        <h3 id="analysis-step2">2단계. 분석 날짜 선택 (이번 달·직전 달)</h3>
        <div className="row">
          <label>
            분석 날짜{" "}
            <input
              type="date"
              value={date}
              min={dateRange.min}
              max={dateRange.max}
              onChange={(e) => setDate(e.target.value)}
              aria-label="분석 날짜"
            />
          </label>
        </div>
      </section>

      <section className="step" aria-labelledby="analysis-step3">
        <h3 id="analysis-step3">3단계. 분석 프롬프트</h3>
        <p className="meta">
          프롬프트는 자유롭게 수정할 수 있습니다. 학교·날짜가 담긴 JSON 블록은 유지해
          주세요.
        </p>
        <textarea
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            setPromptTouched(true);
          }}
          rows={10}
          aria-label="분석 프롬프트"
          placeholder="학교 2곳과 날짜를 선택하면 기본 프롬프트가 생성됩니다."
        />
        <div className="row">
          <button
            onClick={regeneratePrompt}
            disabled={selected.length !== 2 || !date}
          >
            기본 프롬프트 다시 생성
          </button>
          <button onClick={handleAnalyze} disabled={phase === "running"}>
            {phase === "running" ? "분석 중..." : "분석 요청"}
          </button>
        </div>
      </section>

      <section className="step" aria-labelledby="analysis-step4">
        <h3 id="analysis-step4">4단계. 분석 결과</h3>
        {phase === "idle" && !result && (
          <p className="meta">분석 결과가 여기에 표시됩니다.</p>
        )}
        {progress.length > 0 && (
          <ul className="progress-log" aria-label="분석 진행 상태">
            {progress.map((label, index) => (
              <li key={`${index}-${label}`}>{label}</li>
            ))}
          </ul>
        )}
        {result && (
          <div className="analysis-result">
            <p className="verdict-line">
              {result.is_tie ? (
                <strong>두 학교가 동점입니다.</strong>
              ) : (
                <strong>{winnerName(result)} 승리!</strong>
              )}{" "}
              <span className="meta">({result.date} 중식 기준)</span>
            </p>
            <div className="school-results">
              {result.schools.map((school) => (
                <article key={school.school_code} className="meal-card">
                  <h4>
                    {school.school_name}{" "}
                    <span className="total-score">총점 {school.total}점</span>
                    {!result.is_tie &&
                      result.winner_school_code === school.school_code && (
                        <span className="badge">승자</span>
                      )}
                    {!result.is_tie &&
                      result.winner_school_code !== school.school_code && (
                        <span className="badge loser">패자</span>
                      )}
                  </h4>
                  <ul>
                    {school.areas.map((area) => (
                      <li key={area.area_id}>
                        <strong>
                          {area.area_name} ({area.weight}%):
                        </strong>{" "}
                        {area.excluded
                          ? "채점 불가"
                          : `${area.score}점 (환산 ${area.converted}점)`}
                        <br />
                        <span className="meta">{area.rationale}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
            <article className="meal-card">
              <h4>총평 (judge-agent)</h4>
              <p className="verdict-text">{result.verdict}</p>
              {result.excluded_areas.length > 0 && (
                <p className="meta">
                  일부 영역은 데이터 부족으로 채점에서 제외되어 나머지 가중치 기준으로
                  재환산되었습니다.
                </p>
              )}
            </article>
          </div>
        )}
      </section>
    </section>
  );
}
