from flask import Flask, request, jsonify
from flask_cors import CORS
import json,schedule,time,threading,config
from weather_model import predict_weather
from twilio.rest import Client
from datetime import datetime
app = Flask(__name__)
CORS(app)
# Load pest data
with open('tomato_pest_data_with_ages.json', 'r') as f:
    pest_knowledge = json.load(f)
# Twilio Setup
client = Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN)
def send_sms_alert(to_number, pest_name, temp, humidity):
    try:
        body = (
            f"🌡 Good Morning Farmer!\n"
            f"Predicted Temp: {temp}°C, Humidity: {humidity}%\n"
            f"⚠️ Pest Risk: {pest_name}\n"
            f"More info: https://random-id.ngrok-free.app{pest_name.replace(' ', '_')}"
        )

        message = client.messages.create(
            body=body,
            from_=config.TWILIO_PHONE, # Twilio SMS number
            to=to_number
        )
        print(f"✅ SMS sent to {to_number}, SID: {message.sid}")

    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")
    #crop prediction
def get_crop_stage(crop_age):
    age = int(crop_age)
    if 1 <= age <= 25:
        return "Seedling stage"
    elif 26 <= age <= 30:
        return "Early growth stage"
    elif 31 <= age <= 50:
        return "Vegetative stage"
    elif 51 <= age <= 70:
        return "Flowering stage"
    elif 71 <= age <= 90:
        return "Fruit formation stage"
    elif 91 <= age <= 115:
        return "Fruit maturity stage"
    else:
        return "Unknown stage"
    #pest prediction
def predict_pests(crop_age, symptoms, weather):
    results = []
    crop_age = int(crop_age)

    for pest in pest_knowledge:
        # ✅ Convert numeric fields safely
        def safe_float(val):
            try:
                return float(val)
            except:
                return None

        min_temp = safe_float(pest.get("min_temperature"))
        max_temp = safe_float(pest.get("max_temperature"))
        min_hum = safe_float(pest.get("min_humidity"))
        max_hum = safe_float(pest.get("max_humidity"))

        # ✅ Crop age range check (if dataset has range)
        crop_ok = True
        if pest.get("min_crop_age") and pest.get("max_crop_age"):
            crop_ok = pest["min_crop_age"] <= crop_age <= pest["max_crop_age"]

        # ✅ Symptom fuzzy match
        match_score = 0
        for user_symptom in symptoms:
            for pest_symptom in pest.get("symptoms", []):
                if user_symptom.lower() in pest_symptom.lower() or pest_symptom.lower() in user_symptom.lower():
                    match_score += 1
                    break
        if match_score == 0:
            continue

        # ✅ Weather range check
        temp_ok = (min_temp is None or weather["temperature"] >= min_temp) and \
                  (max_temp is None or weather["temperature"] <= max_temp)
        hum_ok = (min_hum is None or weather["humidity"] >= min_hum) and \
                 (max_hum is None or weather["humidity"] <= max_hum)

        if not (temp_ok and hum_ok and crop_ok):
            continue

        results.append({
            "name": pest.get("name", "unknown"),
            "matched_symptoms": match_score,
            "management": pest.get("management", ""),
            "chemical_control": pest.get("chemical_control", ""),
            "biological_control": pest.get("biological_control", ""),
            "natural_enemies": pest.get("natural_enemies", []),
            "min_temperature": min_temp,
            "max_temperature": max_temp,
            "min_humidity": min_hum,
            "max_humidity": max_hum
        })

    return sorted(results, key=lambda x: x["matched_symptoms"], reverse=True)
#predicted by weather
# ✅ Add parse_value here
def parse_value(val, default=None):
    """
    Convert dataset values like '20C' or '50%' into float.
    Returns default if conversion fails.
    """
    if val is None or val == "":
        return default
    try:
        cleaned = str(val).replace("C", "").replace("%", "").strip()
        return float(cleaned)
    except Exception:
        return default
# ✅ Then use it in pest prediction
def predict_pests_by_weather(weather):
    matching_pests = []
    for pest in pest_knowledge:
        try:
            min_temp = parse_value(pest.get("min_temperature"))
            max_temp = parse_value(pest.get("max_temperature"))
            min_hum = parse_value(pest.get("min_humidity"))
            max_hum = parse_value(pest.get("max_humidity"))

            temp_ok = (min_temp is None or weather["temperature"] >= min_temp) and \
                      (max_temp is None or weather["temperature"] <= max_temp)
            hum_ok = (min_hum is None or weather["humidity"] >= min_hum) and \
                     (max_hum is None or weather["humidity"] <= max_hum)
            if temp_ok and hum_ok:
                matching_pests.append(pest)
        except Exception as e:
            print(f"⚠️ Error with pest {pest.get('name')}: {e}")
    return matching_pests

# rest point wesite use
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    crop_age = data.get("crop_age")
    symptoms = data.get("symptoms", [])
    location = data.get("location")
    if not crop_age:
        return jsonify({"error": "Missing crop age"}), 400
    if not location:
        return jsonify({"error": "Missing location"}), 400
    crop_stage = get_crop_stage(crop_age)
    # ✅ Get weather for location
    try:
        weather = predict_weather(location)
    except Exception as e:
        return jsonify({"error": f"Weather API failed: {str(e)}"}), 500
    # If no symptoms
    if not symptoms or all(s.strip() == "" for s in symptoms):
        return jsonify({
            "crop_age": crop_age,
            "crop_stage": crop_stage,
            "weather": weather,
            "pests": [],
            "note": "Please enter the symptoms on your crop."
        })
    # ✅ Match by symptoms + weather
    pests = predict_pests(crop_age, symptoms, weather)
    note = "" if pests else "No pest matched with given symptoms & weather."
    return jsonify({
        "crop_age": crop_age,
        "crop_stage": crop_stage,
        "weather": weather,
        "pests": pests,
        "note": note
    })
# Automatic Morning Alerts (weather only)
# -----------------------------
def automatic_alert():
    print("🔄 Running automatic pest alert job...")
    weather = predict_weather("Bangalore") # change city if needed
    temp, humidity = weather["temperature"], weather["humidity"]

    matching_pests = predict_pests_by_weather(weather)

    if matching_pests:
        for pest in matching_pests:
            send_sms_alert(config.TO_NUMBER, pest["name"], temp, humidity)
    else:
        send_sms_alert(config.TO_NUMBER, "No major pest risk", temp, humidity)

def run_scheduler():
# 4. Schedule to run daily at 7 AM
    schedule.every().day.at("07:00").do(automatic_alert)
    while True:
        schedule.run_pending()
        time.sleep(60)
#run flask
if __name__ == "__main__":
    threading.Thread(target=run_scheduler,daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
