from flask import Flask, jsonify, request
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# تحميل البيانات من ملف Excel
def load_data_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        df.fillna('', inplace=True)
        # تحويل التاريخ إلى string للتأكد من JSON compatibility
        if 'interaction_date' in df.columns:
            df['interaction_date'] = df['interaction_date'].astype(str)
        if 'follow_up_required' in df.columns:
            df['follow_up_required'] = df['follow_up_required'].apply(lambda x: bool(x) if x != '' else False)
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"❌ Error loading Excel file: {e}")
        return []

# تحميل البيانات من ملف Excel
service_interactions_data = load_data_from_excel('service_interactions.xlsx')

@app.route('/')
def home():
    return jsonify({
        "message": "Banking Service Interactions API",
        "version": "1.0",
        "endpoints": {
            "all_interactions": "/api/interactions",
            "customer_interactions": "/api/interactions/customer/<customer_id>",
            "interaction_by_id": "/api/interactions/<interaction_id>"
        }
    })

@app.route('/api/interactions', methods=['GET'])
def get_all_interactions():
    """استرجاع جميع التفاعلات مع إمكانية الـ pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return jsonify({
        "data": service_interactions_data[start:end],
        "total": len(service_interactions_data),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(service_interactions_data) + per_page - 1) // per_page
    })

@app.route('/api/interactions/<interaction_id>', methods=['GET'])
def get_interaction_by_id(interaction_id):
    """استرجاع تفاعل محدد"""
    interaction = next((item for item in service_interactions_data 
                      if str(item["interaction_id"]) == interaction_id), None)
    
    if interaction:
        return jsonify({"data": interaction})
    else:
        return jsonify({"error": "Interaction not found"}), 404

@app.route('/api/interactions/customer/<customer_id>', methods=['GET'])
def get_customer_interactions(customer_id):
    """استرجاع تفاعلات عميل محدد"""
    customer_interactions = [item for item in service_interactions_data 
                           if str(item["customer_id"]) == customer_id]
    
    return jsonify({
        "data": customer_interactions,
        "customer_id": customer_id,
        "total_interactions": len(customer_interactions)
    })

@app.route('/api/interactions', methods=['POST'])
def create_interaction():
    """إضافة تفاعل جديد"""
    new_interaction = request.json

    # الحقول المطلوبة
    required_fields = ['interaction_id', 'customer_id', 'interaction_type']
    for field in required_fields:
        if field not in new_interaction:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    new_interaction['created_at'] = datetime.now().isoformat()

    service_interactions_data.append(new_interaction)
    
    return jsonify({
        "message": "Interaction created successfully",
        "data": new_interaction
    }), 201

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة الـ API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "total_interactions": len(service_interactions_data)
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
