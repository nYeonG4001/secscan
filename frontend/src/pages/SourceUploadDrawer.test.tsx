import { CanceledError } from "axios";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { SourceUploadOptions } from "../api/sourceUpload";
import { SourceUploadDrawer } from "./SourceUploadDrawer";

const { uploadProjectSource } = vi.hoisted(() => ({
  uploadProjectSource: vi.fn(),
}));

vi.mock("../api/sourceUpload", () => ({ uploadProjectSource }));

const onClose = vi.fn();
const onProjectRefresh = vi.fn();
const onRequestError = vi.fn();

function renderDrawer() {
  return render(
    <SourceUploadDrawer
      projectId="12"
      onClose={onClose}
      onProjectRefresh={onProjectRefresh}
      onRequestError={onRequestError}
    />,
  );
}

function selectZip() {
  fireEvent.change(screen.getByLabelText("ZIP 파일"), {
    target: { files: [new File(["source"], "sample.zip", { type: "application/zip" })] },
  });
}

describe("SourceUploadDrawer", () => {
  beforeEach(() => {
    uploadProjectSource.mockReset();
    onClose.mockReset();
    onProjectRefresh.mockReset();
    onProjectRefresh.mockResolvedValue(undefined);
    onRequestError.mockReset();
  });

  afterEach(cleanup);

  it("uploads the selected ZIP, shows progress, and refreshes the project after success", async () => {
    uploadProjectSource.mockImplementation(async (_projectId: string, _file: File, options: SourceUploadOptions) => {
      options.onUploadProgress({ loaded: 5, total: 10, bytes: 5, lengthComputable: true });
      return { project_id: 12, source_status: "REGISTERED", target_languages: ["JAVA", "PYTHON"] };
    });

    renderDrawer();
    selectZip();
    fireEvent.click(screen.getByRole("button", { name: "소스 등록" }));

    expect(await screen.findByText("소스가 등록되었습니다.")).toBeInTheDocument();
    expect(screen.getByText("JAVA, PYTHON")).toBeInTheDocument();
    expect(onProjectRefresh).toHaveBeenCalledOnce();
    expect(uploadProjectSource).toHaveBeenCalledWith(
      "12",
      expect.any(File),
      expect.objectContaining({ signal: expect.any(AbortSignal), onUploadProgress: expect.any(Function) }),
    );
  });

  it.each([
    ["ANALYSIS_ACTIVE", "분석이 끝난 뒤 업로드할 수 있습니다."],
    ["UPLOAD_IN_PROGRESS", "다른 업로드가 진행 중입니다."],
    ["ARCHIVE_TOO_LARGE", "25MB 이하 ZIP만 업로드할 수 있습니다."],
    ["ARCHIVE_LIMIT_EXCEEDED", "ZIP 압축 해제 제한을 초과했습니다."],
    ["UNSAFE_ARCHIVE", "안전하지 않은 ZIP입니다."],
    ["NO_SUPPORTED_SOURCE", "지원하는 소스 파일이 없습니다."],
  ])("shows only the safe message for %s", async (code, message) => {
    uploadProjectSource.mockRejectedValue({ response: { status: 422, data: { code, detail: "/internal/archive/path" } } });

    renderDrawer();
    selectZip();
    fireEvent.click(screen.getByRole("button", { name: "소스 등록" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(message);
    expect(screen.queryByText("/internal/archive/path")).not.toBeInTheDocument();
  });

  it("does not resubmit during an active upload and refreshes after cancellation", async () => {
    uploadProjectSource.mockImplementation((_projectId: string, _file: File, options: SourceUploadOptions) => new Promise<never>((_, reject) => {
      options.onUploadProgress({ loaded: 3, total: 10, bytes: 3, lengthComputable: true });
      options.signal.addEventListener("abort", () => reject(new CanceledError()));
    }));

    renderDrawer();
    selectZip();
    fireEvent.click(screen.getByRole("button", { name: "소스 등록" }));
    expect(await screen.findByRole("progressbar", { name: "업로드 진행률" })).toHaveValue(30);
    fireEvent.click(screen.getByRole("button", { name: "업로드 취소" }));

    await waitFor(() => expect(onProjectRefresh).toHaveBeenCalledOnce());
    expect(uploadProjectSource).toHaveBeenCalledOnce();
    expect(screen.getByRole("button", { name: "소스 등록" })).toBeInTheDocument();
  });

  it("requires an explicit retry after a failed upload", async () => {
    uploadProjectSource
      .mockRejectedValueOnce({ response: { status: 500, data: { detail: "server trace" } } })
      .mockResolvedValueOnce({ project_id: 12, source_status: "REGISTERED", target_languages: ["JAVASCRIPT"] });

    renderDrawer();
    selectZip();
    fireEvent.click(screen.getByRole("button", { name: "소스 등록" }));

    expect(await screen.findByText("업로드에 실패했습니다. 다시 시도해 주세요.")).toBeInTheDocument();
    expect(uploadProjectSource).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "다시 시도" }));

    expect(await screen.findByText("소스가 등록되었습니다.")).toBeInTheDocument();
    expect(uploadProjectSource).toHaveBeenCalledTimes(2);
  });
});
