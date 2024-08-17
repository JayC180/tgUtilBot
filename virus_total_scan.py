import requests
import json

config_file = json.load(open("config.json"))
virus_total_api = config_file["virusTotalApi"]

def virus_scan(file_path: str) -> str:
    url = 'https://www.virustotal.com/api/v3/files'
    headers = {
        'x-apikey': virus_total_api,
    }

    try:
        with open(file_path, 'rb') as file:
            files = {'file': (file_path, file)}
            resp = requests.post(url, headers=headers, files=files)

        if resp.status_code == 200:
            resp_data = resp.json()
            analysis_id = resp_data.get('data', {}).get('id', '')
            return analysis_id
        else:
            return f"Error uploading file to VirusTotal: {resp.status_code}"
    except Exception as e:
        return f"Error scanning file: {e}"

def get_scan_results(analysis_id: str) -> str:
    url = f'https://www.virustotal.com/api/v3/analyses/{analysis_id}'
    headers = {
        'x-apikey': virus_total_api,
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            results = response_data.get('data', {}).get('attributes', {}).get('results', {})
            malicious_count = sum(1 for result in results.values() if result['category'] == 'malicious')
            if malicious_count > 0:
                return f"File is malicious with {malicious_count} detections."
            else:
                return "File is clean."
        else:
            return f"Error getting scan results: {response.status_code}"
    except Exception as e:
        return f"Error getting scan results: {e}"
