import { useParams } from "react-router-dom";

export default function AnalysisStatusPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  return (
    <div className="p-8">
      <h1 className="text-xl font-bold text-gray-800">분석 상태</h1>
      <p className="mt-2 text-sm text-gray-500">분석 ID: {analysisId} — 상태 폴링 구현 예정</p>
    </div>
  );
}
