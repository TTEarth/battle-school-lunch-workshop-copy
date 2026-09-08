import { useState } from "react";
import AnalysisPage from "./pages/AnalysisPage";
import LunchLookupPage from "./pages/LunchLookupPage";

type Tab = "lookup" | "analysis";

export default function App() {
  const [tab, setTab] = useState<Tab>("lookup");
  // 분석 페이지는 첫 진입 시 마운트하고 이후 탭 전환에도 상태를 유지한다.
  const [analysisMounted, setAnalysisMounted] = useState(false);

  const openAnalysis = () => {
    setTab("analysis");
    setAnalysisMounted(true);
  };

  return (
    <main className="app">
      <header className="app-header">
        <h1>급식 배틀</h1>
        <nav className="tabs" role="tablist" aria-label="페이지 탭">
          <button
            role="tab"
            aria-selected={tab === "lookup"}
            className={tab === "lookup" ? "tab active" : "tab"}
            onClick={() => setTab("lookup")}
          >
            급식 조회
          </button>
          <button
            role="tab"
            aria-selected={tab === "analysis"}
            className={tab === "analysis" ? "tab active" : "tab"}
            onClick={openAnalysis}
          >
            급식 분석
          </button>
        </nav>
      </header>
      <div style={{ display: tab === "lookup" ? "block" : "none" }}>
        <LunchLookupPage />
      </div>
      {analysisMounted && (
        <div style={{ display: tab === "analysis" ? "block" : "none" }}>
          <AnalysisPage />
        </div>
      )}
    </main>
  );
}
