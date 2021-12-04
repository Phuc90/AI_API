from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import json
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import tokenizer_from_json
import numpy as np
from . import encoders


@dataclass
class AIModel:
    model_path:Path = None
    tokenizer_path: Optional[Path] = None
    metadata_path: Optional[Path] = None

    model = None
    tokenizer = None
    metadata = None

    def __post_init__(self):
        if self.model_path.exists():
            self.model = load_model(self.model_path)
        if self.tokenizer_path.exists() and self.tokenizer_path.name.endswith('json'):
            tokenizer_text = self.tokenizer_path.read_text()
            self.tokenizer = tokenizer_from_json(tokenizer_text)
        if self.metadata_path.exists() and self.metadata_path.name.endswith('json'):
            self.metadata = json.loads(self.metadata_path.read_text())

    def get_model(self):
        if not self.model:
            raise Exception('Model not implemented')
        return self.model

    def get_tokenizer(self):
        if not self.tokenizer:
            raise Exception('tokenizer not implemented')
        return self.tokenizer

    def get_metadata(self):
        if not self.metadata:
            raise Exception('metadata not implemented')
        return self.metadata

    def get_label_legend_inverted(self):
        legend = self.get_metadata().get('labels_legend_inverted') or {}
        if len(legend.keys()) != 2:
            raise Exception('You need legend inversion')
        return legend

    def get_sequence_from_text(self,texts: List[str]):
        tokenizer = self.get_tokenizer()
        sequences = tokenizer.texts_to_sequences(texts)
        return sequences
    
    def get_input_from_sequences(self,sequences):
        maxlen = self.get_metadata().get('max_sequence') or 280
        x_input = pad_sequences(sequences,maxlen=maxlen)
        return x_input

    def get_labels_pred(self,idx,val):
        legend =self.get_label_legend_inverted()
        return {'label':legend[str(idx)],'confidence':val}

    def get_top_preds_label(self,preds):
        top_idx_val = np.argmax(preds)
        val = preds[top_idx_val]
        return self.get_labels_pred(top_idx_val,val)


    
    def predict_text(self,query,include_top=True,encode_to_json=True):
        model = self.get_model()
        sequences = self.get_sequence_from_text([query])
        x_input = self.get_input_from_sequences(sequences)
        preds = model.predict(x_input)[0]
        labeled_preds = [self.get_labels_pred(i,x) for i,x in enumerate(list(preds))]
        
        results = {'predictions':labeled_preds}

        if include_top:
            results['top'] = self.get_top_preds_label(preds)

        encoded_results = encoders.encode_to_json(results,as_py=True)

        return encoded_results



