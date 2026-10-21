import os
import csv
import io
import json
import requests
from bottle import Bottle, request, response, static_file, run

app = Bottle()

GO_API = os.getenv("GO_API", "http://localhost:8080")
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")

@app.route('/')
def index():
    return static_file("index.html", root=UI_DIR)

@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=UI_DIR)

@app.route('/api/health')
def health():
    try:
        r = requests.get(f"{GO_API}/api/v1/jobs", timeout=3)
        return {"status": "ok", "go_engine": "connected", "code": r.status_code}
    except Exception as e:
        return {"status": "error", "go_engine": "unreachable", "error": str(e)}

@app.route('/api/jobs', method=['GET'])
def get_jobs():
    try:
        r = requests.get(f"{GO_API}/api/v1/jobs")
        response.content_type = 'application/json'
        return r.text
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

@app.route('/api/jobs', method=['POST'])
def create_job():
    try:
        payload = request.json
        r = requests.post(f"{GO_API}/api/v1/jobs", json=payload)
        response.status = r.status_code
        response.content_type = 'application/json'
        return r.text
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

@app.route('/api/jobs/<job_id>', method=['DELETE'])
def delete_job(job_id):
    try:
        r = requests.delete(f"{GO_API}/api/v1/jobs/{job_id}")
        response.status = r.status_code
        return r.text
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

@app.route('/api/jobs/<job_id>/download')
def download_csv(job_id):
    try:
        r = requests.get(f"{GO_API}/api/v1/jobs/{job_id}/download", stream=True)
        response.status = r.status_code
        for k, v in r.headers.items():
            if k.lower() in ['content-type', 'content-disposition']:
                response.headers[k] = v
        return r.content
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

@app.route('/api/jobs/<job_id>/preview')
def preview_job(job_id):
    try:
        r = requests.get(f"{GO_API}/api/v1/jobs/{job_id}/download")
        if r.status_code != 200:
            response.status = r.status_code
            return {"error": "Failed to retrieve CSV data", "status_code": r.status_code}

        csv_text = r.content.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(csv_text))
        leads = []

        for row in reader:
            raw_emails = row.get("emails", "") or ""
            # emails can be comma or semicolon separated
            emails = [e.strip() for e in raw_emails.replace(";", ",").split(",") if e.strip() and "@" in e]
            
            raw_addr = row.get("complete_address", "") or row.get("address", "") or ""
            clean_addr = raw_addr
            if clean_addr.startswith("{") and clean_addr.endswith("}"):
                try:
                    obj = json.loads(clean_addr)
                    parts = [obj.get("street"), obj.get("city"), obj.get("state"), obj.get("postal_code")]
                    clean_addr = ", ".join([p for p in parts if p])
                except Exception:
                    pass

            rating = row.get("review_rating", "") or ""
            if rating:
                try:
                    rating = f"{float(rating):.1f}"
                except Exception:
                    pass

            leads.append({
                "title": row.get("title", "") or "",
                "category": row.get("category", "") or "",
                "phone": row.get("phone", "") or "",
                "website": row.get("website", "") or "",
                "address": clean_addr,
                "emails": emails,
                "review_rating": rating,
                "review_count": row.get("review_count", "") or "",
                "thumbnail": row.get("thumbnail", "") or "",
                "link": row.get("link", "") or "",
                "status": row.get("status", "") or ""
            })

        response.content_type = 'application/json'
        return json.dumps({"job_id": job_id, "total": len(leads), "leads": leads})
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

@app.route('/api/jobs/<job_id>/download-json')
def download_json(job_id):
    try:
        r = requests.get(f"{GO_API}/api/v1/jobs/{job_id}/download")
        if r.status_code != 200:
            response.status = r.status_code
            return {"error": "Failed to fetch data"}

        csv_text = r.content.decode('utf-8', errors='replace')
        reader = csv.DictReader(io.StringIO(csv_text))
        leads = list(reader)

        response.headers['Content-Disposition'] = f'attachment; filename=leads_{job_id}.json'
        response.content_type = 'application/json'
        return json.dumps(leads, indent=2)
    except Exception as e:
        response.status = 500
        return {"error": str(e)}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("============================================================")
    print("  Google Maps Leads Studio Dashboard")
    print(f"  UI Port:    {port}")
    print(f"  Go Engine:  {GO_API}")
    print("============================================================")
    run(app, host='0.0.0.0', port=port, quiet=True)
