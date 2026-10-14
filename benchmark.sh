#!/bin/bash
# 墨韵 · 文章创作工作台 - 性能压测脚本
# 用法: ./benchmark.sh [并发数] [请求数]

set -e

HOST="${BENCH_HOST:-http://127.0.0.1:8000}"
CONCURRENCY="${1:-10}"
REQUESTS="${2:-100}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="/var/log/flask-app/benchmarks"

echo "[$(date)] ===== 性能压测开始 ====="
echo "目标: $HOST"
echo "并发: $CONCURRENCY, 请求数: $REQUESTS"

mkdir -p "$RESULT_DIR"
RESULT_FILE="$RESULT_DIR/bench_${TIMESTAMP}.txt"

# 1. 首页压测
echo ""
echo "[1/4] 首页 GET /"
if command -v ab &> /dev/null; then
    ab -n "$REQUESTS" -c "$CONCURRENCY" "$HOST/" 2>&1 | tee -a "$RESULT_FILE"
else
    echo "[WARN] ab 未安装，使用 curl 循环测试"
    START=$(date +%s%N)
    for i in $(seq 1 "$REQUESTS"); do
        curl -s -o /dev/null -w "%{http_code}\n" "$HOST/" &
        if [ $((i % CONCURRENCY)) -eq 0 ]; then
            wait
        fi
    done
    wait
    END=$(date +%s%N)
    ELAPSED=$(( (END - START) / 1000000 ))
    echo "总耗时: ${ELAPSED}ms, 平均: $(( ELAPSED / REQUESTS ))ms/请求" | tee -a "$RESULT_FILE"
fi

# 2. 健康检查压测
echo ""
echo "[2/4] 健康检查 GET /health"
START=$(date +%s%N)
for i in $(seq 1 "$REQUESTS"); do
    curl -s -o /dev/null "$HOST/health" &
    if [ $((i % CONCURRENCY)) -eq 0 ]; then
        wait
    fi
done
wait
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "总耗时: ${ELAPSED}ms, 平均: $(( ELAPSED / REQUESTS ))ms/请求" | tee -a "$RESULT_FILE"

# 3. 体裁列表压测
echo ""
echo "[3/4] 体裁列表 GET /api/genres"
START=$(date +%s%N)
for i in $(seq 1 "$REQUESTS"); do
    curl -s -o /dev/null "$HOST/api/genres" &
    if [ $((i % CONCURRENCY)) -eq 0 ]; then
        wait
    fi
done
wait
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "总耗时: ${ELAPSED}ms, 平均: $(( ELAPSED / REQUESTS ))ms/请求" | tee -a "$RESULT_FILE"

# 4. Prometheus 指标压测
echo ""
echo "[4/4] 指标端点 GET /metrics"
START=$(date +%s%N)
for i in $(seq 1 "$REQUESTS"); do
    curl -s -o /dev/null "$HOST/metrics" &
    if [ $((i % CONCURRENCY)) -eq 0 ]; then
        wait
    fi
done
wait
END=$(date +%s%N)
ELAPSED=$(( (END - START) / 1000000 ))
echo "总耗时: ${ELAPSED}ms, 平均: $(( ELAPSED / REQUESTS ))ms/请求" | tee -a "$RESULT_FILE"

echo ""
echo "[$(date)] ===== 压测完成，结果保存至: $RESULT_FILE ====="
