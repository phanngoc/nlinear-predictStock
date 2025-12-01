#!/bin/bash
cd "$(dirname "$0")"
source ../myenv/bin/activate
streamlit run app_trading.py --server.port 8502
