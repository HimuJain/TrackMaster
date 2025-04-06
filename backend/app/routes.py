from flask import Flask, Blueprint, request
from flask_cors import CORS

bp = Blueprint('api',__name__)

CORS(bp)

from .services.mongoclient import MusicMongoClient

client = MusicMongoClient(data_path = "/Users/ryan/Desktop/diamondhacks/backend/mlh-hackathon-flask-starter/app/feature_jsons")

@bp.route('/classify_genre', methods = ['POST'])
def classify_genre():
    # TODO get the form ka he
    try:
        if(request.method == 'POST'):
            # print(request.json())
            audio = request.files.get('audio')
            if audio:
                print(audio)
                
                print("processing request...")
                matches = client.process_vector_request(audio)

                return {"status":"200", "message":f"{matches}"}
            else:
                return {"status":"400","message":"no file found in request."}
            
        
        return {"status":"401","message":"bad method"}
    except Exception as e:
        print(f"error:{e}")
        return {"status":"500", "message":"internal server error"}

@bp.route('/generate')
def generate_idea():
    if(request.method == 'GET'):
        # we will need data on hand, but this doesn't make sense really.
        print(request)

    return {"status":"200", "message":"2"}