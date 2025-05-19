#!/bin/bash
curl -N -H "Authorization: Bearer changeme" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "can you analyze this ton wallet address about its portofolios, jetton, nft holdings and activities? UQBXbfJhkqlCpDXPn_x5uXDR_cqC7xfjx3jhwx5DOO1DWqZn"}' \
     http://localhost:5100/analyze 