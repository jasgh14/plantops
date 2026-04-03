.PHONY: test run-app

test:
	pytest -q

run-app:
	streamlit run app/Home.py
