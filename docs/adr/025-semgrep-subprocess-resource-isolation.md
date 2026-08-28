# ADR-025: Semgrep subprocess 자원 제한과 non-root 실행

**Context**: E4는 단일 인스턴스의 스레드 기반 실행기에서 Semgrep을 subprocess로 실행한다. E3의 ZIP 제한만으로는 파싱 비용이 높은 소스가 Semgrep 메모리나 CPU를 과도하게 사용하는 상황을 막을 수 없다. 또한 Docker socket을 백엔드에 연결해 별도 컨테이너를 실행하면 업로드를 처리하는 서비스에 호스트 수준 권한을 부여하게 된다. 현재 개발 Compose의 `./backend:/app` bind mount 안의 상대 `storage/` 경로는 non-root 사용자와 호스트 파일 권한이 충돌할 수 있다.

**Decision**: Docker socket이나 별도 컨테이너 실행 없이, 고정 버전 Semgrep CLI를 포함한 백엔드 컨테이너에서 subprocess로 실행한다. 백엔드 컨테이너 전체는 전용 non-root 사용자로 실행한다. `backend/app/core/config.py`의 `STORAGE_ROOT` 기본값은 `/var/lib/secscan/storage`로 변경한다. 런타임 소스 저장소는 코드 bind mount와 분리한 `source_storage` named volume을 같은 경로에 mount하며, 이 경로는 `backend/Dockerfile`에서 이미지 빌드 시 전용 사용자에게 소유권을 부여한다. `docker-compose.yml` backend에는 `mem_limit: 1.5g`를 적용한다. 개발 Compose에서도 같은 저장소를 사용하고 실제 업로드, 스냅샷 복사, 정리 작업의 쓰기 권한을 검증한다.

분석 실행기는 Semgrep용 별도 실행 래퍼를 새 프로세스 그룹으로 시작한다. 래퍼는 Semgrep 실행 전에 Linux `RLIMIT_AS`를 1 GiB, `RLIMIT_CPU`를 120초로 제한한다. 부모 프로세스는 별도로 120초의 경과 시간 제한을 적용한다. 제한 초과 시 `SIGTERM`을 프로세스 그룹 전체에 보내고 짧게 대기한 뒤, 남아 있으면 `SIGKILL`을 같은 그룹 전체에 보낸다. 이때 `shell=False`와 인자 배열을 사용하며, 스레드 환경에서 교착 상태 위험이 있는 `preexec_fn`은 사용하지 않는다.

Docker Compose의 backend 컨테이너에는 1.5 GiB 메모리 상한을 적용한다. Semgrep의 1 GiB 제한이 1차 방어이고, 컨테이너 제한은 백엔드 전체가 과도한 메모리를 점유하는 상황을 막는 2차 방어다. timeout, CPU 또는 메모리 제한으로 실패한 분석은 `FAILED`와 관리자용 `ANALYSIS_TIMEOUT` 또는 안전한 자원 제한 오류 코드로 기록한다.

MVP에서는 backend와 Semgrep이 같은 non-root 사용자로 실행되므로, 스냅샷에 대한 별도 OS 사용자 수준의 강제 읽기 전용 격리는 제공하지 않는다. 분석 프로세스 격리와 읽기 전용 공유 저장소가 필요한 경우는 Docker socket을 사용하지 않는 Semgrep sidecar 또는 별도 실행 환경으로 후속 확장한다.

**Alternatives**: Docker socket으로 일회성 Semgrep 컨테이너 실행, root 백엔드에서 Semgrep 자식만 다른 사용자로 실행, `preexec_fn`으로 자원 제한, 백엔드 이미지의 Semgrep subprocess와 non-root 컨테이너 실행

**Consequences**: 단일 인스턴스 MVP에서 Docker daemon 권한 없이 시간, CPU, 주소 공간, 컨테이너 메모리를 다층 제한한다. Semgrep 하위 워커도 timeout 때 함께 종료된다. named volume을 쓰므로 로컬 bind mount의 사용자 ID와 저장소 권한이 섞이지 않는다. Semgrep의 강한 프로세스 격리는 후속 범위로 남는다.

**References**: ADR-012, ADR-022, ADR-023, SFR-008, SFR-015, SEC-007, SEC-009, SEC-010
