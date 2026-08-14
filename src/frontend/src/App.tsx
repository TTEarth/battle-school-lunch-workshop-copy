import { useState } from "react";
import { ApiError, searchMeals, searchSchools } from "./api/client";
import type { Meal, School } from "./types";

type Phase = "idle" | "loading" | "done";

export default function App() {
  const [keyword, setKeyword] = useState("");
  const [schools, setSchools] = useState<School[]>([]);
  const [searchPhase, setSearchPhase] = useState<Phase>("idle");
  const [selected, setSelected] = useState<School | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [meals, setMeals] = useState<Meal[]>([]);
  const [mealPhase, setMealPhase] = useState<Phase>("idle");
  const [error, setError] = useState("");

  const handleSearch = async () => {
    if (!keyword.trim()) {
      setError("학교명을 입력해 주세요.");
      return;
    }
    setError("");
    setSearchPhase("loading");
    setSelected(null);
    try {
      const data = await searchSchools(keyword.trim());
      setSchools(data.schools);
      setSearchPhase("done");
    } catch (e) {
      setSchools([]);
      setSearchPhase("idle");
      setError(e instanceof ApiError ? e.message : "학교 검색에 실패했습니다.");
    }
  };

  const handleMealSearch = async () => {
    if (!selected) {
      setError("먼저 학교를 선택해 주세요.");
      return;
    }
    if (!startDate || !endDate) {
      setError("시작일과 종료일을 모두 입력해 주세요.");
      return;
    }
    if (startDate > endDate) {
      setError("시작일은 종료일보다 늦을 수 없습니다.");
      return;
    }
    setError("");
    setMealPhase("loading");
    try {
      const data = await searchMeals({
        atptCode: selected.atpt_code,
        schoolCode: selected.school_code,
        startDate,
        endDate,
      });
      setMeals(data.meals);
      setMealPhase("done");
    } catch (e) {
      setMeals([]);
      setMealPhase("idle");
      setError(e instanceof ApiError ? e.message : "급식 조회에 실패했습니다.");
    }
  };

  return (
    <main className="app">
      <h1>급식 배틀 - 학교 급식 조회</h1>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}

      <section className="step" aria-labelledby="step1">
        <h2 id="step1">1단계. 학교 검색</h2>
        <div className="row">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="학교명 일부를 입력하세요"
            aria-label="학교명 검색어"
          />
          <button onClick={handleSearch} disabled={searchPhase === "loading"}>
            {searchPhase === "loading" ? "검색 중..." : "학교 검색"}
          </button>
        </div>
        {searchPhase === "done" && schools.length === 0 && (
          <p className="notice">검색 결과가 없습니다. 검색어를 수정해 다시 시도해 주세요.</p>
        )}
        {schools.length > 0 && (
          <ul className="school-list">
            {schools.map((school) => {
              const isSelected =
                selected?.atpt_code === school.atpt_code &&
                selected?.school_code === school.school_code;
              return (
                <li key={`${school.atpt_code}-${school.school_code}`}>
                  <button
                    className={isSelected ? "selected" : ""}
                    onClick={() => setSelected(school)}
                    aria-pressed={isSelected}
                  >
                    <strong>{school.school_name}</strong>{" "}
                    <span className="meta">
                      {school.atpt_name}
                      {school.school_kind ? ` · ${school.school_kind}` : ""}
                      {school.address ? ` · ${school.address}` : ""}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="step" aria-labelledby="step2">
        <h2 id="step2">2단계. 날짜 범위 선택</h2>
        {selected ? (
          <p>
            선택된 학교: <strong>{selected.school_name}</strong>
          </p>
        ) : (
          <p className="meta">학교를 먼저 선택해 주세요.</p>
        )}
        <div className="row">
          <label>
            시작일{" "}
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              aria-label="시작일"
            />
          </label>
          <label>
            종료일{" "}
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              aria-label="종료일"
            />
          </label>
          <button onClick={handleMealSearch} disabled={mealPhase === "loading"}>
            {mealPhase === "loading" ? "조회 중..." : "중식 조회"}
          </button>
        </div>
      </section>

      <section className="step" aria-labelledby="step3">
        <h2 id="step3">3단계. 급식 결과</h2>
        {mealPhase === "idle" && <p className="meta">조회 결과가 여기에 표시됩니다.</p>}
        {mealPhase === "loading" && <p>급식 정보를 조회하고 있습니다...</p>}
        {mealPhase === "done" && meals.length === 0 && (
          <p className="notice">
            표시할 급식 정보가 없습니다. 학교 또는 날짜 범위를 수정해 다시 조회해 주세요.
          </p>
        )}
        {meals.map((meal) => (
          <article key={meal.meal_date} className="meal-card">
            <h3>
              {meal.meal_date} · {meal.meal_name}
            </h3>
            <ul>
              {meal.dishes.map((dish) => (
                <li key={dish}>{dish}</li>
              ))}
            </ul>
            {meal.calories && <p className="meta">칼로리: {meal.calories}</p>}
          </article>
        ))}
      </section>
    </main>
  );
}
