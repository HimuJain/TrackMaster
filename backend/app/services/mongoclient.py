
# TODO big todo

from pymongo import MongoClient

import json

import os

import glob as g
import numpy as np

from pydub import AudioSegment
# import certifi
from ..data.feature_vector_extract import AudioFeatureExtractor

# ca = certifi.where()

connection_string = os.getenv('CONNECTION_STRING')

class MusicMongoClient:
    

    def __init__(self, data_path = None):
        
        self.data_path = data_path

        print("initializing mongodb client...")
        self.mongoose = MongoClient(
            connection_string,
            tlsAllowInvalidCertificates= True,
        )
        # self.mongoose.admin.command('ping')
        print("connected succesfully.")

        print("initializing extractor...")
        self.extractor = AudioFeatureExtractor()

        print("doing setup vector upsertion...")
        self.insert_init_collection()


    def insert_init_collection(self):
        """
            Upserts vectors for the initial database, if the collection is empty
        """

        try:
            database = self.mongoose.get_database("Music_Data")
            assert database is not None, "Something went wrong fetching database."
            songs = database.get_collection("Known_Music") # check vectors as if no vectors, then nothing else.
            if songs.count_documents({}) == 0:
                print("Collection is empty. Upserting data from local files...") # Thank you copilot
                assert self.data_path is not None, "There must be directory with data from which to initialize the database."
                print(f"datapath exists! {self.data_path}")
                # print(g.glob(f"{self.data_path}/*.json"))
                for i, file in enumerate(g.glob(f"{self.data_path}/*.json")): # TODO change the extension because 
                    print(f"reading from file {file}")
                    try: # TODO this is prob a good way to go about it. either way we'll need to parse this shit.
                        with open(file, 'r') as f:
                            data = json.load(f)
                            for song in data['songs']:
                                song_vec = song["feature_vector"] # there is a precompiled feature vector.

                                result = songs.update_one(
                                    {"file_name": song["path"]},
                                    {
                                        "$set": {
                                            "features": {
                                                "type": "vector",
                                                "vector": song_vec
                                            },
                                            "genre_index": i  # Save the genre index from enumerate, we can use this later.
                                        }
                                    },
                                    upsert=True
                                )
                                print(result)

                    except Exception as e:
                        print(f"Failed to upsert data for {file}: {e}")
            else:
                print("Collection is not empty. Skipping upsert.")

        except Exception as e:
            print(f"An error occurred while initializing: {e}")
        

    def run_query(self, query_embedding):

        """
            Taken straight from the MongoDB docs
            Params:
                query_embedding: np array of the extracted features
            that's p much it.
        """
        print(len(query_embedding))

        pipeline = [
            {
                "$vectorSearch": {
                    "exact": True,
                    "index": "vector-index",
                    "limit": 10,
                    "numCandidates": 5,
                    "path": "features",
                    "queryVector": query_embedding,
                }
            },
            {
                "$project": {
                    "file_name": 1, # since we have the files locally loaded, we can just load them from there.
                    "genre_index": 1,
                    "score": {"$meta": "vectorSearchScore"},
                    "_id": 0
                }
            }
        ]
        database = self.mongoose.get_database("Music_Data")
        coll = database.get_collection("Known_Music")


        nearest_neighbors = coll.aggregate(pipeline)

        return [*nearest_neighbors] # hoping this works to unpack i have no idea.




    def process_vector_request(self, audio_file):

        # use the built in stream attribute to read in as a file. pelase sworkd
        audio_array = AudioSegment.from_file(audio_file.stream, format="webm")
        print(audio_array.get_array_of_samples())
        audio_array = np.array(audio_array.get_array_of_samples())
        audio_array = np.float32(audio_array)
        print(f"audio array:{audio_array}")


        # before we process the request, extract features from the audio passed in from the client
        audio_feature_vector = self.extractor.extract_features(audio=audio_array, sr = 22050)

        result = self.run_query(audio_feature_vector) # this will return 

        # we need the GROUND TRUTH CLASSES boss. Maybe as a separate table? Yeah probably

        return result # TODO ==> can we use the id indices to figure out what class these are?
        # sanity check for now, def nothing will come out of this.
    

    def return_audio_files(self, results):
        """
            Parse the results to send over files to the client to listen to. Suggestions I suppose.
        """



        return None
        # query for those indices in our database.
        # file and class
            
