export const options = {
  vus: 200,
  duration: '30s',
};

export default function () {
  http.post(`${BASE_URL}/donate/send`, JSON.stringify({
    user_id: Math.floor(Math.random() * 100000),
    streamer_id: 12345,
    amount: 100,
    message: "spike test"
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}