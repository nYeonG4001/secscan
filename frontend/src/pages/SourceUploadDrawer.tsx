import { AxiosError, isCancel } from "axios";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";

import { uploadProjectSource } from "../api/sourceUpload";
import { ActionDrawer } from "../components/ActionDrawer";

type UploadState = "selecting" | "uploading" | "failed" | "succeeded";

const UPLOAD_ERROR_MESSAGES: Record<string, string> = {
  ANALYSIS_ACTIVE: "분석이 끝난 뒤 업로드할 수 있습니다.",
  UPLOAD_IN_PROGRESS: "다른 업로드가 진행 중입니다.",
  ARCHIVE_TOO_LARGE: "25MB 이하 ZIP만 업로드할 수 있습니다.",
  ARCHIVE_LIMIT_EXCEEDED: "ZIP 압축 해제 제한을 초과했습니다.",
  UNSAFE_ARCHIVE: "안전하지 않은 ZIP입니다.",
  NO_SUPPORTED_SOURCE: "지원하는 소스 파일이 없습니다.",
};

function uploadErrorMessage(error: unknown) {
  const data = (error as AxiosError<{ code?: string; detail?: { code?: string } }>).response?.data;
  const code = data?.code ?? data?.detail?.code;
  return (code && UPLOAD_ERROR_MESSAGES[code]) ?? "업로드에 실패했습니다. 다시 시도해 주세요.";
}

interface SourceUploadDrawerProps {
  projectId: string;
  onClose: () => void;
  onProjectRefresh: () => Promise<void>;
  onRequestError: (error: unknown) => void;
}

export function SourceUploadDrawer({ projectId, onClose, onProjectRefresh, onRequestError }: SourceUploadDrawerProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("selecting");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const controllerRef = useRef<AbortController | null>(null);
  const isUploadingRef = useRef(false);

  useEffect(() => () => controllerRef.current?.abort(), []);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    setFile(selectedFile);
    setUploadState("selecting");
    setProgress(0);
    setError(null);
  }

  async function refreshAfterCancellation() {
    try {
      await onProjectRefresh();
    } catch {
      // 새로고침 오류는 기존 페이지 오류 처리에서 표시한다.
    }
  }

  async function startUpload() {
    if (!file || isUploadingRef.current) return;

    isUploadingRef.current = true;
    const controller = new AbortController();
    controllerRef.current = controller;
    setUploadState("uploading");
    setProgress(0);
    setError(null);

    try {
      const result = await uploadProjectSource(projectId, file, {
        signal: controller.signal,
        onUploadProgress: (event) => {
          if (event.total && event.total > 0) {
            setProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      });
      setTargetLanguages(result.target_languages);
      setUploadState("succeeded");
      try {
        await onProjectRefresh();
      } catch {
        // 업로드 성공 뒤 새로고침이 실패해도 ZIP을 다시 전송하지 않는다.
      }
    } catch (requestError) {
      if (isCancel(requestError) || controller.signal.aborted) {
        setUploadState("selecting");
        await refreshAfterCancellation();
      } else {
        const status = (requestError as AxiosError).response?.status;
        if (status === 401 || status === 403 || status === 404) {
          onRequestError(requestError);
          return;
        }
        setUploadState("failed");
        setError(uploadErrorMessage(requestError));
      }
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
      isUploadingRef.current = false;
    }
  }

  function cancelUpload() {
    controllerRef.current?.abort();
  }

  function closeDrawer() {
    if (isUploadingRef.current) {
      controllerRef.current?.abort();
      void refreshAfterCancellation();
    }
    onClose();
  }

  const footer = uploadState === "uploading" ? (
    <button type="button" onClick={cancelUpload} className="w-full rounded border px-3 py-2 text-sm text-red-600">
      업로드 취소
    </button>
  ) : uploadState === "succeeded" ? (
    <button type="button" onClick={closeDrawer} className="w-full rounded bg-black px-3 py-2 text-sm text-white">
      확인
    </button>
  ) : uploadState === "failed" ? (
    <div className="flex gap-2">
      <button type="button" onClick={closeDrawer} className="flex-1 rounded border px-3 py-2 text-sm">
        닫기
      </button>
      <button type="button" onClick={startUpload} disabled={!file} className="flex-1 rounded bg-black px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50">
        다시 시도
      </button>
    </div>
  ) : (
    <button type="button" onClick={startUpload} disabled={!file} className="w-full rounded bg-black px-3 py-2 text-sm text-white disabled:cursor-not-allowed disabled:opacity-50">
      소스 등록
    </button>
  );

  return (
    <ActionDrawer title="소스 등록" onClose={closeDrawer} footer={footer}>
      {uploadState === "succeeded" ? (
        <div aria-live="polite">
          <p className="text-sm font-medium text-green-700">소스가 등록되었습니다.</p>
          <p className="mt-2 text-sm text-gray-600">분석은 자동으로 시작되지 않습니다.</p>
          <p className="mt-4 text-sm font-medium">감지된 언어</p>
          <p className="mt-1 text-sm text-gray-600">{targetLanguages.join(", ") || "감지된 언어 없음"}</p>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-600">25MB 이하의 ZIP 파일을 선택해 주세요. 소스 등록은 분석을 자동으로 시작하지 않습니다.</p>
          <label htmlFor="source-archive" className="mt-5 block text-sm font-medium">ZIP 파일</label>
          <input
            id="source-archive"
            type="file"
            accept=".zip,application/zip"
            onChange={selectFile}
            disabled={uploadState === "uploading"}
            className="mt-2 block w-full text-sm"
          />
          {file && <p className="mt-2 break-all text-sm text-gray-600">선택한 파일: {file.name}</p>}
          {uploadState === "uploading" && (
            <div className="mt-5" aria-live="polite">
              <div className="flex justify-between text-sm">
                <span>업로드 중</span>
                <span>{progress}%</span>
              </div>
              <progress aria-label="업로드 진행률" className="mt-2 w-full" value={progress} max="100">{progress}%</progress>
            </div>
          )}
          {error && <p role="alert" className="mt-4 text-sm text-red-600">{error}</p>}
        </>
      )}
    </ActionDrawer>
  );
}
