import subprocess


# 이 파일은 secscan.python.subprocess-run-shell 규칙의 대상 외 API 회귀 fixture로만
# 안전하다. subprocess.Popen(shell=True) 호출 자체는 secscan.python.subprocess-popen-shell
# 규칙의 진짜 취약 sink이며, 전체 규칙 집합에서는 의도적으로 탐지된다.
def run_command(command):
    subprocess.Popen(command, shell=True)
