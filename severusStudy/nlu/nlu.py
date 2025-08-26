import pandas as pd
import torch
from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer, AutoConfig
from ollama import Client
from config import OLLAMA_HOST, OLLAMA_MODEL_NLU
import json_repair
import os
import time
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle
#from severusStudy.nlu.nlu_finetuning_gemma3_hyperparatuning import ontology


class NLU:
    def __init__(self):
        # So far these folder addressess are still hard coded to fit to the one on the robusto computer as this is by now the only one that can handle the model.
        # Needs a one-time connection to huggingface in order to cache the model/tockenizer, although it is not uploaded to hugging face
        #nlu_model_dir = "/home/scsuser/Desktop/Adaptive_Explanation_Generation/finetuneNLU/triple_extraction/results/llama3/final_checkpoint/prompt_engineered_model"
        #self.tokenizer = AutoTokenizer.from_pretrained('/home/scsuser/Desktop/Adaptive_Explanation_Generation/finetuneNLU/triple_extraction/tockenizer', local_files_only=True)
        #self.model = AutoPeftModelForCausalLM.from_pretrained(nlu_model_dir, device_map={"": 0}, torch_dtype=torch.bfloat16, local_files_only=True)
        #self.model.eval()
        self.instruction = "Extrahiere die passenden Sätze aus der folgenden Frage in deutscher Sprache."

        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'new_ontology_NLU.csv')

        df_data_ontology = pd.read_csv(path, delimiter=',')
        ontology = []
        sentence_ontology = []
        for _, row in df_data_ontology.iterrows():
            ontology.append(f"({row['Start Node']}, {row['Relation']}, {row['End Node']})")
            sentence_ontology.append(row['Sentence'])
        self.sentence_ontology = sentence_ontology
        self.ontology = ontology

        # base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, 'new_ontology_NLU.csv')
        self.df = pd.read_csv(path)
        self.compare_sentences = self.df['Sentence'].tolist()
        self.nlu_cache = {}
        if os.path.exists("nlu_cache.pkl"):
            #load cache
            with open('nlu_cache.pkl', 'rb') as f:
                self.nlu_cache = pickle.load(f)

    def get_embedding(self,text):
        text = text.strip()
        if text in self.nlu_cache:
            return self.nlu_cache[text]
        else:
            print("Debug: Calling ollama for embedding. This should be as few times as possible.")
            model = 'nomic-embed-text'
            client = Client(host=OLLAMA_HOST)
            embedding = client.embed(model=model, input=text).embeddings
            self.nlu_cache[text] = embedding
            #pickle output for consequent calls
            #with open('nlu_cache.pkl', 'wb') as f:
            #    import pickle
            #    pickle.dump(self.nlu_cache, f)
            return embedding


    def nlu_pass_olama(self, feedback: str, is_verification) -> (str, str):

            client = Client(
                host=OLLAMA_HOST,
            )

            PROMPT_MESSAGE = """
            You are an expert linguistic evaluator and need to match a question to the correct sentences that are provided as ontology.

            ### Input Question:
            "{input}"

            ### Instructions:
            1. **Identify the Triple**: 
               - Match the question to all appropriate sentences from the ontology provided below.
               - If the question refers to several sentences you should mention all of them, pay special attention to what sentences actually answer the question. Do not add any sentence that is not relevant for answering the question. 
               - If the question does not fit to any of the provided sentence, just answer "None" and skip step 2. 
            2. **Identify the question Type**
               The question types are:
               a) open question
               b) confirmation: this is a closed question which ask for confirmation and the information provided in the question is correct. If you would answer the question with yes, the question type is confirmation. For example: Is the ball blue, while the ball is actually blue.
               c) rejection: this is a closed question which contains wrong information. If you would answer the question with no, the question type is rejection. For example: Is the ball blue?, while the ball is actually not blue.

            ### Respond *only* with a valid JSON object. Use the following format exactly (keys must match):
            {{
                "Triple": <list_of_sentences>,
                "Question_type": <open/confirm/rejection>,
                "Reasoning": <your_reasoning>
            }}   
                
            ### Ontology Context:
            {ontology}
            """

            PROMPT_VERIFICATION_QUESTION = """ You are a teacher and you asked a question to verify the understanding of your student. 
            Therefore, you know the question and the short answer. You should rate how well the students answer fits to the real answer. 
            The rating should be between 1 and 10 with 10 being the exact answer as given. 
            You can use the summary to have more guidance about what the answer should yield. You have to be strict, only answers that semantically match the true answer should be rated above a 5.
            The question, answer, summary combination is: {question},{answer},{summary}
            The student answer is: {answer_student}
            ### REQUIRED JSON OUTPUT FORMAT:
            {{
                "score": <integer 1 to 10>,
                "Reasoning": <your_reasoning>
            }}   
            """
            print("Entry into nlu")
            print("Is verification question: ", is_verification['is_verification'])
            if is_verification['is_verification']:
                input_text = PROMPT_VERIFICATION_QUESTION.format(question=is_verification["info"]["question"],
                                                                 answer=is_verification["info"]["answers"],
                                                                 summary=is_verification["info"]["summary"],
                                                                 answer_student=feedback)

                start_time = time.time()
                message = [{'role': 'user', 'content': input_text}]
                response = client.chat(model=OLLAMA_MODEL_NLU, messages=message)
                content = response.message.content
                end_time = time.time()
                runtime = (end_time - start_time) * 1000
                print(f"\n\nRuntime verification: {runtime:.2f} ms\n\n")
                print(content)
                try:
                    json_output = json_repair.loads(content)
                    score = json_output["score"]
                except Exception as e:
                    print("Exception:", e)
                    score = 10
                print("Score for verification Question: ", score)
                if score > 7:
                    return "Correct_Answer", -2
                else:
                    return "False_Answer", -3


            print("In normal processing of NLU.")
            input_text = PROMPT_MESSAGE.format(input=feedback, ontology=self.sentence_ontology)
            start_time = time.time()
            message = [{'role': 'user', 'content': input_text}]
            response = client.chat(model=OLLAMA_MODEL_NLU, messages=message)
            content = response.message.content
            end_time = time.time()
            runtime = (end_time - start_time) * 1000
            print(f"\n\nRuntime: {runtime:.2f} ms\n\n")
            print(content)
            try:
                answer = content.split("json")[1]
                answer = answer.split("```")[0]
                json_output = json_repair.loads(answer)
                print("Json output", json_output)
                sentences = json_output["Triple"][:3]
            except Exception as e:
                print("Json Formatting not successful", e)
                return "No triple found", -1
            try:
                question_type = json_output["Question_type"]
            except Exception as e:
                question_type = 0
            #print(f"extracted triple:\n{triple}\nquestion type: {question_type}")

            triples = []
            if question_type != "unrelated":
                for sentence in sentences:
                    if sentence == "Diese Frage hat nichts mit Quarto zu tun.":
                        continue
                    compare_sentences = [
                        (compare_sentence, cosine_similarity(
                            np.array(self.get_embedding(sentence)).reshape(1, -1),
                            np.array(self.get_embedding(compare_sentence)).reshape(1, -1)
                        )[0][0])
                        for compare_sentence in self.compare_sentences
                    ]
                    matched_sentence, score = max(compare_sentences, key=lambda x: x[1])
                    if score > 0.90:
                        row = self.df[self.df['Sentence'] == matched_sentence].iloc[0]
                        triples.append(f"({str(row['Start Node'])}, {str(row['Relation'])}, {str(row['End Node'])})")
            if not triples:
                print("Sentences in nlu output: ", sentences)
                print("No triples found")
                return "No triple found", -1
            print(triples)
            return triples, 2 if question_type == "rejection" else 1 if question_type == "confirmation" else 0