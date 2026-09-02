import { CanceledError } from "axios";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { SourceUploadOptions } from "../api/sourceUpload";
import { SourceUploadDrawer } from "./SourceUploadDrawer";

const { preflightProjectSource, uploadProjectSource } = vi.hoisted(() => ({
  preflightProjectSource: vi.fn(),
  uploadProjectSource: vi.fn(),
}));

vi.mock("../api/sourceUpload", () => ({ preflightProjectSource, uploadProjectSource }));

const onClose = vi.fn();
const onProjectRefresh = vi.fn();
const onRequestError = vi.fn();
const onAnalysis = vi.fn();

function renderDrawer({ hasExistingSource = false } = {}) {
  return render(
    <SourceUploadDrawer
      projectId="12"
      hasExistingSource={hasExistingSource}
      onClose={onClose}
      onProjectRefresh={onProjectRefresh}
      onRequestError={onRequestError}
      onAnalysis={onAnalysis}
    />,
  );
}

function selectZip() {
  fireEvent.change(screen.getByLabelText("ZIP 파일"), {
    target: { files: [new File(["source"], "sample.zip", { type: "application/zip" })] },
  });
}

async function finishPreflightDelay() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(3_000);
  });
}

async function completeSafePreflight() {
  await finishPreflightDelay();
  const status = screen.getByRole("status");
  expect(status).toHaveTextContent("파일이 선택되었습니다.");
  expect(status).not.toHaveTextContent("ZIP 안전성 확인을 완료했습니다.");
}

async function flushAsyncWork() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("SourceUploadDrawer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    preflightProjectSource.mockReset();
    preflightProjectSource.mockResolvedValue({ safe: true });
    uploadProjectSource.mockReset();
    onClose.mockReset();
    onProjectRefresh.mockReset();
    onProjectRefresh.mockResolvedValue(undefined);
    onRequestError.mockReset();
    onAnalysis.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("shows a loading state and keeps registration disabled while ZIP safety is checked", async () => {
    let resolvePreflight: ((value: { safe: true }) => void) | undefined;
    preflightProjectSource.mockImplementation(() => new Promise((resolve) => {
      resolvePreflight = resolve;
    }));

    renderDrawer();
    selectZip();

    expect(screen.getByLabelText("ZIP 안전성 확인 중")).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("button", { name: "분석 실행" })).toBeDisabled();
    expect(uploadProjectSource).not.toHaveBeenCalled();
    expect(onAnalysis).not.toHaveBeenCalled();
    resolvePreflight?.({ safe: true });
    await completeSafePreflight();
    expect(screen.getByRole("button", { name: "분석 실행" })).toBeEnabled();
  });

  it("starts registration and analysis only after a safe ZIP preflight succeeds", async () => {
    uploadProjectSource.mockImplementation(async (_projectId: string, _file: File, options: SourceUploadOptions) => {
      options.onUploadProgress({ loaded: 5, total: 10, bytes: 5, lengthComputable: true });
      return { project_id: 12, source_status: "REGISTERED", target_languages: ["JAVA", "PYTHON"] };
    });

    renderDrawer();
    selectZip();
    await completeSafePreflight();
    fireEvent.click(screen.getByRole("button", { name: "분석 실행" }));

    await flushAsyncWork();
    expect(onAnalysis).toHaveBeenCalledOnce();
    expect(onProjectRefresh).toHaveBeenCalledOnce();
    expect(preflightProjectSource).toHaveBeenCalledWith(
      "12",
      expect.any(File),
      { signal: expect.any(AbortSignal) },
    );
    expect(uploadProjectSource).toHaveBeenCalledWith(
      "12",
      expect.any(File),
      expect.objectContaining({ signal: expect.any(AbortSignal), onUploadProgress: expect.any(Function) }),
    );
  });

  it.each([
    ["ARCHIVE_TOO_LARGE", "25MB 이하 ZIP만 업로드할 수 있습니다."],
    ["ARCHIVE_LIMIT_EXCEEDED", "ZIP 압축 해제 제한을 초과했습니다."],
    ["UNSAFE_ARCHIVE", "안전하지 않은 .zip 파일입니다."],
  ])("shows a red safe preflight error for %s and does not register", async (code, message) => {
    preflightProjectSource.mockRejectedValue({ response: { status: 422, data: { code, detail: "/internal/archive/path" } } });

    renderDrawer();
    selectZip();
    await finishPreflightDelay();

    expect(screen.getByRole("alert")).toHaveTextContent(message);
    expect(screen.getByRole("button", { name: "분석 실행" })).toBeDisabled();
    expect(uploadProjectSource).not.toHaveBeenCalled();
    expect(screen.queryByText("/internal/archive/path")).not.toBeInTheDocument();
  });

  it("asks for confirmation before replacing an existing source", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    renderDrawer({ hasExistingSource: true });
    selectZip();
    expect(confirm).not.toHaveBeenCalled();
    await completeSafePreflight();
    fireEvent.click(screen.getByRole("button", { name: "분석 실행" }));

    expect(confirm).toHaveBeenCalledWith("기존 소스를 교체하고 분석을 시작할까요?");
    expect(uploadProjectSource).not.toHaveBeenCalled();
    confirm.mockRestore();
  });

  it("preserves an existing source after an unsafe ZIP preflight", async () => {
    preflightProjectSource.mockRejectedValue({ response: { status: 422, data: { code: "UNSAFE_ARCHIVE" } } });
    renderDrawer({ hasExistingSource: true });
    selectZip();
    await finishPreflightDelay();

    expect(screen.getByRole("alert")).toHaveTextContent("안전하지 않은 .zip 파일입니다.");
    expect(uploadProjectSource).not.toHaveBeenCalled();
    expect(onProjectRefresh).not.toHaveBeenCalled();
    expect(onAnalysis).not.toHaveBeenCalled();
  });

  it("does not resubmit during an active upload and refreshes after cancellation", async () => {
    uploadProjectSource.mockImplementation((_projectId: string, _file: File, options: SourceUploadOptions) => new Promise<never>((_, reject) => {
      options.onUploadProgress({ loaded: 3, total: 10, bytes: 3, lengthComputable: true });
      options.signal.addEventListener("abort", () => reject(new CanceledError()));
    }));

    renderDrawer();
    selectZip();
    await completeSafePreflight();
    fireEvent.click(screen.getByRole("button", { name: "분석 실행" }));
    expect(screen.getByRole("progressbar", { name: "업로드 진행률" })).toHaveValue(30);
    fireEvent.click(screen.getByRole("button", { name: "업로드 취소" }));

    await flushAsyncWork();
    expect(onProjectRefresh).toHaveBeenCalledOnce();
    expect(uploadProjectSource).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "분석 실행" })).toBeEnabled();
  });

  it("requires an explicit retry after a failed upload", async () => {
    uploadProjectSource
      .mockRejectedValueOnce({ response: { status: 500, data: { detail: "server trace" } } })
      .mockResolvedValueOnce({ project_id: 12, source_status: "REGISTERED", target_languages: ["JAVASCRIPT"] });

    renderDrawer();
    selectZip();
    await completeSafePreflight();
    fireEvent.click(screen.getByRole("button", { name: "분석 실행" }));

    await flushAsyncWork();
    expect(screen.getByText("업로드에 실패했습니다. 다시 시도해 주세요.")).toBeInTheDocument();
    expect(uploadProjectSource).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "다시 시도" }));

    await flushAsyncWork();
    expect(onAnalysis).toHaveBeenCalledOnce();
    expect(uploadProjectSource).toHaveBeenCalledTimes(2);
  });
});
