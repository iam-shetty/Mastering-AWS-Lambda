cat <<EOF > all_transactions.json
[
  {
    "transaction_id": "txn-g-001",
    "user_id": "user-1",
    "amount": 520,
    "country": "India",
    "device_id": "android-1",
    "timestamp": "2026-01-03T09:00:00"
  },
  {
    "transaction_id": "txn-g-002",
    "user_id": "user-1",
    "amount": 680,
    "country": "India",
    "device_id": "android-1",
    "timestamp": "2026-01-03T09:10:00"
  },
  {
    "transaction_id": "txn-g-003",
    "user_id": "user-1",
    "amount": 610,
    "country": "India",
    "device_id": "android-1",
    "timestamp": "2026-01-03T09:20:00"
  },
  {
    "transaction_id": "txn-g-004",
    "user_id": "user-1",
    "amount": 750,
    "country": "India",
    "device_id": "android-1",
    "timestamp": "2026-01-03T09:30:00"
  },
  {
    "transaction_id": "txn-g-005",
    "user_id": "user-1",
    "amount": 690,
    "country": "India",
    "device_id": "android-1",
    "timestamp": "2026-01-03T09:40:00"
  },
  {
    "transaction_id": "txn-f-001",
    "user_id": "user-1",
    "amount": 45000,
    "country": "Germany",
    "device_id": "iphone-17",
    "timestamp": "2026-01-03T10:00:00"
  },
  {
    "transaction_id": "txn-f-002",
    "user_id": "user-1",
    "amount": 52000,
    "country": "Germany",
    "device_id": "iphone-17",
    "timestamp": "2026-01-03T10:02:00"
  },
  {
    "transaction_id": "txn-f-003",
    "user_id": "user-1",
    "amount": 60000,
    "country": "France",
    "device_id": "iphone-17",
    "timestamp": "2026-01-03T10:05:00"
  },
  {
    "transaction_id": "txn-f-004",
    "user_id": "user-1",
    "amount": 90000,
    "country": "United States of America",
    "device_id": "iphone-99",
    "timestamp": "2026-01-03T10:08:00"
  },
  {
    "transaction_id": "txn-f-005",
    "user_id": "user-1",
    "amount": 85000,
    "country": "United Kingdom",
    "device_id": "iphone-99",
    "timestamp": "2026-01-03T10:10:00"
  }
]
EOF

jq -c '.[]' all_transactions.json | while read txn; do
  aws kinesis put-record \
    --stream-name fault-stream \
    --partition-key user-1 \
    --data "$txn" \
    --region ap-south-1 \
    --cli-binary-format raw-in-base64-out
done

Imp:  stream name, partition key and region as per your setup.