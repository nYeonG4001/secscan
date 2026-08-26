import { useParams } from "react-router-dom";

export default function FindingsPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  return (
    <div className="p-8">
      <h1 className="text-xl font-bold text-gray-800">결과 조회</h1>
      <p className="mt-2 text-sm text-gray-500">
        분석 ID: {analysisId} — 리스트 + 심각도 필터 + 상세 구현 예정
      </p>
    </div>
  );
}
