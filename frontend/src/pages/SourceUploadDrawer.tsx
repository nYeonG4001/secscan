import { AxiosError, isCancel } from "axios";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";

import { preflightProjectSource, uploadProjectSource } from "../api/sourceUpload";
import { ActionDrawer } from "../components/ActionDrawer";

type UploadState = "selecting" | "uploading" | "failed" | "succeeded";
type PreflightState = "idle" | "checking" | "safe" | "failed";

const UPLOAD_ERROR_MESSAGES: Record<string, string> = {
  ANALYSIS_ACTIVE: "분석이 끝난 뒤 업로드할 수 있습니다.",
  UPLOAD_IN_PROGRESS: "다른 업로드가 진행 중입니다.",
  ARCHIVE_TOO_LARGE: "25MB 이하 ZIP만 업로드할 수 있습니다.",
  ARCHIVE_LIMIT_EXCEEDED: "ZIP 압축 해제 제한을 초과했습니다.",
  UNSAFE_ARCHIVE: "안전하지 않은 .zip 파일입니다.",
  NO_SUPPORTED_SOURCE: "지원하는 소스 파일이 없습니다.",
};

const PREFLIGHT_MIN_DISPLAY_MS = 3000;

function uploadErrorMessage(error: unknown) {
  const data = (error as AxiosError<{ code?: string; detail?: { code?: string } }>).response?.data;
  const code = data?.code ?? data?.detail?.code;
  return (code && UPLOAD_ERROR_MESSAGES[code]) ?? "업로드에 실패했습니다. 다시 시도해 주세요.";
}

function preflightErrorMessage(error: unknown) {
  const data = (error as AxiosError<{ code?: string; detail?: { code?: string } }>).response?.data;
  const code = data?.code ?? data?.detail?.code;
  return (code && UPLOAD_ERROR_MESSAGES[code]) ?? "ZIP 안전성 확인에 실패했습니다. 다시 선택해 주세요.";
}

interface SourceUploadDrawerProps {
  projectId: string;
  hasExistingSource: boolean;
  onClose: () => void;
  onProjectRefresh: () => Promise<void>;
  onRequestError: (error: unknown) => void;
  onAnalysis: () => void;
}

export function SourceUploadDrawer({ projectId, hasExistingSource, onClose, onProjectRefresh, onRequestError, onAnalysis }: SourceUploadDrawerProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("selecting");
  const [preflightState, setPreflightState] = useState<PreflightState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [targetLanguages, setTargetLanguages] = useState<string[]>([]);
  const controllerRef = useRef<AbortController | null>(null);
  const preflightControllerRef = useRef<AbortController | null>(null);
  const preflightRequestIdRef = useRef(0);
  const isUploadingRef = useRef(false);

  useEffect(() => () => {
    controllerRef.current?.abort();
    preflightControllerRef.current?.abort();
    preflightRequestIdRef.current += 1;
  }, []);

  function selectFile(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0] ?? null;
    const requestId = preflightRequestIdRef.current + 1;
    preflightRequestIdRef.current = requestId;
    preflightControllerRef.current?.abort();
    setFile(selectedFile);
    setUploadState("selecting");
    setPreflightState(selectedFile ? "checking" : "idle");
    setProgress(0);
    setError(null);
    setTargetLanguages([]);
    if (selectedFile) void startPreflight(selectedFile, requestId);
  }

  async function startPreflight(selectedFile: File, requestId: number) {
    const controller = new AbortController();
    preflightControllerRef.current = controller;

    try {
      const result = await preflightProjectSource(projectId, selectedFile, { signal: controller.signal });
      if (requestId !== preflightRequestIdRef.current) return;
      if (preflightControllerRef.current !== controller) return;
      await new Promise<void>((resolve) => window.setTimeout(resolve, PREFLIGHT_MIN_DISPLAY_MS));
      if (requestId !== preflightRequestIdRef.current || controller.signal.aborted) return;
      setPreflightState(result.safe ? "safe" : "failed");
      if (!result.safe) setError("안전하지 않은 .zip 파일입니다.");
    } catch (requestError) {
      if (isCancel(requestError) || requestId !== preflightRequestIdRef.current) return;
      const status = (requestError as AxiosError).response?.status;
      if (status === 401 || status === 403 || status === 404) {
        setPreflightState("idle");
        onRequestError(requestError);
        return;
      }
      if (requestId !== preflightRequestIdRef.current) return;
      await new Promise<void>((resolve) => window.setTimeout(resolve, PREFLIGHT_MIN_DISPLAY_MS));
      if (requestId !== preflightRequestIdRef.current || controller.signal.aborted) return;
      setPreflightState("failed");
      setError(preflightErrorMessage(requestError));
    } finally {
      if (preflightControllerRef.current === controller) preflightControllerRef.current = null;
    }
  }

  async function refreshAfterCancellation() {
    try {
      await onProjectRefresh();
    } catch {
      // 새로고침 오류는 기존 페이지 오류 처리에서 표시한다.
    }
  }

  async function startUpload() {
    if (!file || preflightState !== "safe" || isUploadingRef.current) return;
    if (hasExistingSource && !window.confirm("기존 소스를 교체하고 분석을 시작할까요?")) return;

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
      try {
        await onProjectRefresh();
      } catch {
        // 업로드 성공 뒤 새로고침이 실패해도 ZIP을 다시 전송하지 않는다.
      }
      onAnalysis();
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
    if (preflightState === "checking" && !window.confirm("안전성 확인을 중단하고 닫을까요?")) return;
    preflightRequestIdRef.current += 1;
    preflightControllerRef.current?.abort();
    if (isUploadingRef.current) {
      controllerRef.current?.abort();
      void refreshAfterCancellation();
    }
    onClose();
  }

  const footer = uploadState === "uploading" ? (
    <button type="button" onClick={cancelUpload} className="secscan-destructive-button w-full">
      업로드 취소
    </button>
  ) : uploadState === "succeeded" ? (
    <button type="button" onClick={onAnalysis} className="secscan-primary-button w-full">
      분석 시작
    </button>
  ) : uploadState === "failed" ? (
    <div className="flex gap-2">
      <button type="button" onClick={closeDrawer} className="secscan-secondary-button flex-1">
        닫기
      </button>
      <button type="button" onClick={startUpload} disabled={!file} className="secscan-primary-button flex-1 disabled:cursor-not-allowed disabled:opacity-50">
        다시 시도
      </button>
    </div>
  ) : (
    <button type="button" onClick={startUpload} disabled={!file || preflightState !== "safe"} className="secscan-primary-button w-full disabled:cursor-not-allowed disabled:opacity-50">
      분석 실행
    </button>
  );

  return (
    <ActionDrawer title="소스 등록 및 분석 실행" onClose={closeDrawer} footer={footer} hideDividers>
      {uploadState === "succeeded" ? (
        <div aria-live="polite" className="secscan-panel p-4">
          <p className="text-sm font-semibold text-green-700">소스가 등록되었습니다.</p>
          <p className="mt-2 text-sm text-gray-600">분석은 자동으로 시작되지 않습니다.</p>
          <p className="mt-4 text-sm font-medium">감지된 언어</p>
          <p className="mt-2 break-words text-sm text-gray-600">{targetLanguages.join(", ") || "감지된 언어 없음"}</p>
        </div>
      ) : (
        <>
          <label htmlFor="source-archive" className="mt-2 flex h-64 -translate-y-3 cursor-pointer flex-col items-center justify-center gap-4 rounded-xl border border-secscan-border bg-secscan-surface-2 text-center text-sm text-secscan-muted">
            <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-10 w-10">
              <path d="M12 15V3" />
              <path d="m8.5 6.5 3.5-3.5 3.5 3.5" />
              <path d="M5 13.5v4.25A2.25 2.25 0 0 0 7.25 20h9.5A2.25 2.25 0 0 0 19 17.75V13.5" />
            </svg>
            <span>.zip 파일을 선택하거나 끌어 놓으세요</span>
            <input
              id="source-archive"
              type="file"
              aria-label="ZIP 파일"
              accept=".zip,application/zip"
              onChange={selectFile}
              disabled={uploadState === "uploading"}
              className="sr-only"
            />
          </label>
          {file && preflightState === "safe" && (
            <p role="status" className="mt-3 flex items-center gap-3 rounded-lg border border-secscan-border bg-secscan-surface-2 px-3 py-3 text-sm text-secscan-foreground">
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5 shrink-0 text-secscan-cyan">
                <path d="M6 3.75h8.25L18 7.5v12.75H6z" />
                <path d="M14 3.75V8h4" />
                <path d="M9 12h6M9 15h4" />
              </svg>
              <span>파일이 선택되었습니다.</span>
            </p>
          )}
          {preflightState === "checking" && (
            <div aria-label="ZIP 안전성 확인 중" aria-live="polite" aria-busy="true" className="secscan-preflight-progress mt-4">
              <span />
            </div>
          )}
          {uploadState === "uploading" && (
            <div className="secscan-panel mt-5 p-4" aria-live="polite">
              <div className="flex justify-between text-sm">
                <span className="font-medium">업로드 중</span>
                <span className="text-secscan-cyan">{progress}%</span>
              </div>
              <progress aria-label="업로드 진행률" className="mt-2 w-full" value={progress} max="100">{progress}%</progress>
            </div>
          )}
          {error && <p role="alert" className={`mt-4 text-sm ${preflightState === "failed" ? "text-red-400" : "secscan-error-state"}`}>{error}</p>}
        </>
      )}
    </ActionDrawer>
  );
}
