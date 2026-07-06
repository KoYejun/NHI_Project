# Release Checklist

이 문서는 NHI Secret Agent를 공개 저장소 또는 포트폴리오에 올리기 전 확인해야 할 항목을 정리한다.

## 1. 실행 검증

```bash
python scripts/create_sample_project.py
python -m app.main --target-path data/sample_project
streamlit run frontend/streamlit_app.py