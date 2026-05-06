export default function () {

  // 1. донат
  const res = http.post(`${BASE_URL}/donate/send`, JSON.stringify({
    user_id: 1,
    streamer_id: 12345,
    amount: 50,
    message: "nice stream"
  }), { headers: { 'Content-Type': 'application/json' } });

  const donation = res.json();

  check(res, {
    'donation created': (r) => r.status === 200,
  });

  sleep(2);

  // 2. получение истории (нагрузка на SELECT)
  http.get(`${BASE_URL}/donate/history?limit=20&offset=0`);

  sleep(1);

  // 3. stats (нагрузка на агрегации)
  http.get(`${BASE_URL}/donate/session-stats`);
}