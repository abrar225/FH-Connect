
const API_BASE = "http://localhost:8000";
async function test() {
  try {
    const res = await fetch(API_BASE + "/");
    console.log("Status:", res.status);
    const data = await res.json();
    console.log("Data:", data);
  } catch (err) {
    console.error("Fetch failed:", err.message);
  }
}
test();
