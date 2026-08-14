"""E2E용 NEIS 대역 서버.

실백엔드 관통 E2E에서 실제 NEIS 대신 사용한다. 외부 계약(openapi.json)의
응답 구조를 흉내 낸다.

실행: python neis_stub.py  (기본 포트 9310)
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

SCHOOL_ROWS = [
    {
        "ATPT_OFCDC_SC_CODE": "B10",
        "ATPT_OFCDC_SC_NM": "서울특별시교육청",
        "SD_SCHUL_CODE": "7010083",
        "SCHUL_NM": "서울고등학교",
        "SCHUL_KND_SC_NM": "고등학교",
        "ORG_RDNMA": "서울특별시 서초구 효령로 197",
    }
]

MEAL_ROWS = [
    {
        "MMEAL_SC_CODE": "2",
        "MMEAL_SC_NM": "중식",
        "MLSV_YMD": "20260513",
        "DDISH_NM": "쌀밥<br/>된장국<br/>제육볶음",
        "CAL_INFO": "800 Kcal",
    },
    {
        "MMEAL_SC_CODE": "2",
        "MMEAL_SC_NM": "중식",
        "MLSV_YMD": "20260512",
        "DDISH_NM": "비빔밥<br/>미역국",
        "CAL_INFO": "750 Kcal",
    },
]

NO_DATA = {"RESULT": {"CODE": "INFO-200", "MESSAGE": "해당하는 데이터가 없습니다."}}


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: dict) -> None:
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802 - http.server 규약
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/hub/schoolInfo":
            name = query.get("SCHUL_NM", [""])[0]
            if "서울고" in name:
                self._send(
                    {"schoolInfo": [{"head": []}, {"row": SCHOOL_ROWS}]}
                )
            else:
                self._send(NO_DATA)
        elif parsed.path == "/hub/mealServiceDietInfo":
            from_ymd = query.get("MLSV_FROM_YMD", [""])[0]
            if from_ymd.startswith("202605"):
                self._send(
                    {"mealServiceDietInfo": [{"head": []}, {"row": MEAL_ROWS}]}
                )
            else:
                self._send(NO_DATA)
        else:
            self.send_error(404)

    def log_message(self, *args) -> None:  # 테스트 출력 소음 제거
        pass


if __name__ == "__main__":
    port = int(os.environ.get("NEIS_STUB_PORT", "9310"))
    print(f"NEIS stub listening on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
