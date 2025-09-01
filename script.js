document.getElementById('pestForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const location = document.getElementById('location').value;
  const cropAge = document.getElementById('cropAge').value;
  const symptoms = document.getElementById('symptoms').value.split(',').map(s => s.trim());

  const response = await fetch('http://localhost:5000/predict', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ location: location, crop_age: cropAge, symptoms: symptoms })
  });
  const data = await response.json();
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';
// Handle server-side errors
  if (data.error) {
    resultsDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
    return;
  }
 // Add "Result for the above data"
  resultsDiv.innerHTML += `<h2>📊 Results</h2><hr/>`;
// Show crop stage
//resultsDiv.innerHTML += `<h2>🌱 Crop Stage: ${data.crop_stage}</h2><hr/>`;
// Add "Predicted Weather"
  resultsDiv.innerHTML += `<h2>🌦 Predicted Weather</h2>`;
  resultsDiv.innerHTML += `<h3>📍 Location: ${location}</h3>`;
  resultsDiv.innerHTML += `<p><strong>🌡️ Temperature:</strong> ${data.weather.temperature} °C</p>`;
  resultsDiv.innerHTML += `<p><strong>💧 Humidity:</strong> ${data.weather.humidity}%</p>`;
  resultsDiv.innerHTML += `<p><strong>🌤 Condition:</strong> ${data.weather.condition}</p><hr/>`;
// If no pests matched
  if (data.pests.length === 0) {
    resultsDiv.innerHTML += `<p>✅ ${data.note || 'No pest detected at this stage.'}</p>`;
    return;
  }
// Loop through pests
  data.pests.forEach(pest => {
    resultsDiv.innerHTML += `
      <div>
        <h2>🌱 Crop Stage: ${data.crop_stage}</h2><hr/>
        <h3>🐛 Pest Name: ${pest.name}</h3>
        <p><strong>Recommended Strategies to Prevent from Pest</strong></p>
        <p><strong>Management:</strong> ${pest.management}</p>
        <p><strong>Chemical Control:</strong> ${pest.chemical_control}</p>
        <p><strong>Biological Control:</strong> ${pest.biological_control}</p>
        <p><strong>Natural Enemies:</strong> ${pest.natural_enemies.join(", ")}</p>
      </div>
      <hr/>
    `;
  });
});

