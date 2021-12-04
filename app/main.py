import os
import pathlib
from typing import Optional
from app.models import SMSInference
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from . import (ml, config, db, models, schema)
from cassandra.cqlengine.management import sync_table
from cassandra.query import SimpleStatement




app = FastAPI()
settings = config.get_settings()


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
MODEL_DIRS = BASE_DIR / 'models'
MODEL_SPAM_DIR = MODEL_DIRS /'spam-sms'
MODEL_PATH = MODEL_SPAM_DIR/ 'spam-model.h5'
METADATA_PATH = MODEL_SPAM_DIR/ 'spam-classifer-metadata.json'
TOKENIZER_PATH = MODEL_SPAM_DIR / 'spam-classifer-tokenizer.json'

AI_MODEL = None
DB_SESSION = None
SMSInference = models.SMSInference


@app.on_event('startup')
def on_startup():
    global AI_MODEL, DB_SESSION
    AI_MODEL = ml.AIModel(MODEL_PATH,
    TOKENIZER_PATH,
    METADATA_PATH)

    DB_SESSION = db.get_session()
    sync_table(SMSInference)

@app.get("/")
def read_index(q:Optional[str]=None):
    return {"hello",'world'}


@app.post("/")          
def create_inference(query: schema.Query): #?q=this is awesome
    global AI_MODEL
    preds_dict =AI_MODEL.predict_text(query.q)
    top = preds_dict.get('top')
    data = {'query':query.q,**top} #{label:conf}
    obj = SMSInference.objects.create(**data)

    return obj




@app.get("/inferences/")
def read_inference():
    q = SMSInference.objects.all()
    print(q)
    return list(q)


@app.get("/inferences/{my_uuid}")
def read_inference(my_uuid):
    obj = SMSInference.objects.get(uuid=my_uuid)
    return obj


def fetch_rows(stmt:SimpleStatement,fetch_size:int = 10,session=None):
    stmt.fetch_size = fetch_size
    result_set = session.execute(stmt)
    has_pages = result_set.has_more_pages
    yield "uuid,label,confidence,query,version \n"
    # for row in result_set.current_rows:
    #     yield f"{row['uuid']},{row['label']}, {row['confidence']},{row['query']},{row['model_version']}\n"
    while has_pages:
        for row in result_set.current_rows:
            yield f"{row['uuid']},{row['label']}, {row['confidence']},{row['query']},{row['model_version']}\n"
        has_pages = result_set.has_more_pages
        result_set = session.execute(stmt,paging_state=result_set.paging_state)

@app.get("/dataset")
def export_inferences():
    global DB_SESSION
    cql_query = "SELECT * FROM spam_inferences.SMSInference limit 10000"
    statement = SimpleStatement(cql_query)
    # rows = DB_SESSION.execute(cql_query)
    
    return StreamingResponse(fetch_rows(statement,10,DB_SESSION))



