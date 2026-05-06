import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // прогрев
    { duration: '1m', target: 50 },    // норм нагрузка
    { duration: '1m', target: 100 },   // пик
    { duration: '30s', target: 0 },     // спад
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'], // <1% ошибок
    http_req_duration: ['p(95)<800'], // p95 < 800ms
  },
};

const BASE_URL = 'http://localhost:8000';

// фиксированные тестовые данные (важно для консистентности)
const STREAMER_ID = 12345;

function randomUserId() {
  return Math.floor(Math.random() * 1000000);
}

function randomAmount() {
  return Math.floor(Math.random() * 500) + 10;
}

export default function () {

  const payload = JSON.stringify({
    user_id: randomUserId(),
    streamer_id: STREAMER_ID,
    amount: randomAmount(),
    message: "hello stream donation test"
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      // если есть auth:
      // 'Authorization': `Bearer ${TOKEN}`
    },
  };

  const res = http.post(`${BASE_URL}/donate/send`, payload, params);

  check(res, {
    'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'response has id': (r) => {
      try {
        return JSON.parse(r.body).id !== undefined;
      } catch (e) {
        return false;
      }
    }
  });

  sleep(1);
}