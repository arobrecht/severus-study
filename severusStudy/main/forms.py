#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Some example forms that may be useful
@author: jpoeppel
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, RadioField, FieldList, SelectMultipleField, IntegerField, SubmitField, TextAreaField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, InputRequired, NumberRange, Optional, Length
import csv
from pathlib import Path


VALIDATION_OPTIONAL = False


likert_scale = ["Stimme überhaupt nicht zu", "Stimme nicht zu", "Stimme eher nicht zu", "neutral",
                           "Stimme eher zu", "Stimme zu", "Stimme voll und ganz zu"]
likert_map_positiv = {s: i + 1 for (s, i) in zip(likert_scale, range(len(likert_scale)))}
likert_map_negativ = {s: len(likert_scale) - i for (s, i) in zip(likert_scale, range(len(likert_scale)))}

# print(likert_map_positiv)
# print(likert_map_negativ)
# exit()

class UsernamePasswordForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class EmailForm(FlaskForm):
    email = EmailField("Email address", [DataRequired(), Email()])

class FeedbackForm(FlaskForm):
    feedback = TextAreaField('Ihr Feedback', validators=[DataRequired(), Length(max=250)])
    submit_feedback = SubmitField("Absenden")

class IDForm(FlaskForm):
    crowd_ID = StringField('ID', validators=[DataRequired()])
    submit_ID = SubmitField("Eingeben")


class CheckboxForm(FlaskForm):
    checkbox2 = BooleanField("Ich werde keine KI-Tools im Rahmen dieser Studie nutzen",
                                       validators=[InputRequired()])
    checkbox = BooleanField("Ich bin mit der Erhebung, Verarbeitung, Speicherung ... einverstanden",
                                        validators=[InputRequired()])


class PersonalInfoForm(FlaskForm):
    alter = IntegerField("alter", validators=[DataRequired("Geben Sie ein Alter an."),
                                          NumberRange(min=18, max=130, message="Geben Sie ein valides Alter an.")])
    was_machen = RadioField(label="was_machen",
                            choices=["Student:in", "Schüler:in", "Auszubildende:r",
                                     "Berufstätige:r", "Sonstiges"], validators=[DataRequired()])
    studiengang = StringField("study", validators=[Optional()])
    fachsemester = IntegerField("fachsemester", validators=[Optional()])
    leistungskurs = StringField("leistungskurs", validators=[Optional()])
    ausbildung = StringField("ausbildung", validators=[Optional()])
    beruf = StringField("beruf", validators=[Optional()])
    muttersprache = RadioField(label="muttersprache", choices=["Ja", "Nein"], validators=[DataRequired()])
    vorwissen_quarto = RadioField(label="vorwissen_quarto",
                                  choices=["Nein, gar nicht.",
                                           "Ich habe davon gehört, es aber noch nie gespielt.",
                                           "Ich habe es einmal gespielt.",
                                           "Ich habe es gelegentlich gespielt.",
                                           "Ich habe es schon oft gespielt."], validators=[DataRequired()])


def check_quarto_vorwissen(form: PersonalInfoForm):
    rauswurfliste = ["Ich habe es einmal gespielt.",
                     "Ich habe es gelegentlich gespielt.",
                     "Ich habe es schon oft gespielt."]
    return form.vorwissen_quarto.data in rauswurfliste

def muttersprache(form: PersonalInfoForm):
    rausliste = ["Nein"]
    return form.muttersprache.data in rausliste

def save_personal_infos(form: PersonalInfoForm, user_id):
    results_path = Path(f"resultsSeverusStudy/{str(user_id)}")
    results_path.mkdir(parents=True, exist_ok=True)
    with open(results_path / Path("personal_infos"), 'w', encoding = "utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["item","answer"])
        writer.writerow(["alter", form.alter.data])
        writer.writerow(["was_machen", form.was_machen.data])
        writer.writerow(["studiengang", form.studiengang.data])
        writer.writerow(["fachsemester", form.fachsemester.data])
        writer.writerow(["leistungskurs", form.leistungskurs.data])
        writer.writerow(["ausbildung", form.ausbildung.data])
        writer.writerow(["beruf", form.beruf.data])
        writer.writerow(["muttersprache", form.muttersprache.data])
        writer.writerow(["vorwissen_quarto", form.vorwissen_quarto.data])


class ExpertiseForm(FlaskForm):
    filepath = Path("severusStudy/questions/csv/2_expertise.csv")
    with open(filepath, newline='', encoding = "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        next(reader) # skip first row
        for idx, (frage, antwortoptionen, _) in enumerate(reader):
            if antwortoptionen == "Likert Scale":
                choices = likert_scale
            else:
                choices = ["Error?"]
            if VALIDATION_OPTIONAL:
                exec(f"q{idx} = RadioField(label=frage, choices=choices, validators=[Optional()])")
            else:
                exec(f"q{idx} = RadioField(label=frage, choices=choices, validators=[DataRequired()])")


class QuestionnaireFormPostOne(FlaskForm):
    filepath = Path("severusStudy/questions/csv/3_general_adaptivity.csv")
    with open(filepath, newline='', encoding = "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader) # skip first row
        for idx, row in enumerate(reader):
            category, adapted_item, scale = row
            if scale == "7point likert scale":
                choices = likert_scale
            else:
                choices = ["Error?"]

            if VALIDATION_OPTIONAL:
                exec(f"q{idx} = RadioField(label=adapted_item, choices=choices, validators=[Optional()])")
            else:
                exec(f"q{idx} = RadioField(label=adapted_item, choices=choices, validators=[DataRequired()])")

class QuestionnaireFormPostTwo(FlaskForm):
    filepath = Path("severusStudy/questions/csv/3_asaq_long.csv")
    with open(filepath, newline='', encoding = "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader) # skip first row
        for idx, row in enumerate(reader):
            category, adapted_item, scale = row
            if scale == "7point likert scale":
                choices = likert_scale
            else:
                choices = ["Error?"]

            if VALIDATION_OPTIONAL:
                exec(f"q{idx} = RadioField(label=adapted_item, choices=choices, validators=[Optional()])")
            else:
                exec(f"q{idx} = RadioField(label=adapted_item, choices=choices, validators=[DataRequired()])")



class QuestionnaireFormUnderstanding(FlaskForm):

    filepath = Path("severusStudy/questions/csv/4a_understanding_questionnaire.csv")
    with open(filepath, newline='', encoding = "utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader) # skip first row
        for idx, row in enumerate(reader):
            question, answer, options, points, comment = row
            choices = options.split(",")

            if VALIDATION_OPTIONAL:
                exec(f"q{idx}= RadioField(label=question, choices=choices, validators=[Optional()])")
            else:
                exec(f"q{idx}= RadioField(label=question, choices=choices, validators=[DataRequired()])")

    # checkboxes cb
    cb1o1 = BooleanField()
    cb1o2 = BooleanField()
    cb1o3 = BooleanField()
    cb1o4 = BooleanField()

    blau = BooleanField()
    grün = BooleanField()
    rot = BooleanField()
    gelb = BooleanField()
    violet = BooleanField()

    cb2o1 = BooleanField()
    cb2o2 = BooleanField()
    cb2o3 = BooleanField()

    cb3o1 = BooleanField()
    cb3o2 = BooleanField()
    cb3o3 = BooleanField()

    cb4o1 = BooleanField()
    cb4o2 = BooleanField()
    cb4o3 = BooleanField()

    cb5o1 = BooleanField()
    cb5o2 = BooleanField()
    cb5o3 = BooleanField()

    cb6o1 = BooleanField()
    cb6o2 = BooleanField()
    cb6o3 = BooleanField()

    cb7o1 = BooleanField()
    cb7o2 = BooleanField()
    cb7o3 = BooleanField()

    cb8_b1 = BooleanField()
    cb8_b2 = BooleanField()
    cb8_c3 = BooleanField()
    cb8_d4 = BooleanField()
    cb8_d1 = BooleanField()
    cb8_e1 = BooleanField()
    cb8_f1 = BooleanField()
    cb8_g1 = BooleanField()
    cb8_f2 = BooleanField()

    cb9_1 = BooleanField()
    cb9_2 = BooleanField()
    cb9_3 = BooleanField()
    cb9_4 = BooleanField()
    cb9_5 = BooleanField()
    cb9_6 = BooleanField()
    cb9_7 = BooleanField()
    cb9_8 = BooleanField()

    save_attention = TextAreaField('Erklären Sie Ihre Entscheidung', validators=[Length(max=3000)])


def save_question_answers(name: str, form, user_id):

    results_path = Path(f"resultsSeverusStudy/{str(user_id)}")
    results_path.mkdir(parents=True, exist_ok=True)

    with open(results_path / Path(f"{name}"), 'w', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["item","answer"])

        for field in form:
            print(field)
            if field.type == "RadioField":
                question = field.label.text
                data = field.data
                writer.writerow([question, data])


def save_understanding_form(form: QuestionnaireFormUnderstanding, user_id):
    results_path = Path(f"resultsSeverusStudy/{str(user_id)}")
    results_path.mkdir(parents=True, exist_ok=True)

    with open(results_path / Path("understanding"), 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for field in form:
            if field.type == "RadioField":
                question = field.label.text
                data = field.data
                writer.writerow([question, data])

        writer.writerow(["q1"] + [form.cb1o1.data, form.cb1o2.data, form.cb1o3.data, form.cb1o4.data])
        writer.writerow(["q2"] + [form.cb2o1.data, form.cb2o2.data, form.cb1o3.data])
        writer.writerow(["q3"] + [form.cb3o1.data, form.cb3o2.data, form.cb3o3.data])
        writer.writerow(["q4"] + [form.cb4o1.data, form.cb4o2.data, form.cb4o3.data])
        writer.writerow(["q5"] + [form.cb5o1.data, form.cb5o2.data, form.cb5o3.data])
        writer.writerow(["q6"] + [form.cb6o1.data, form.cb6o2.data, form.cb6o3.data])
        writer.writerow(["q7"] + [form.cb7o1.data, form.cb7o2.data, form.cb7o3.data])
        writer.writerow(["q8"] + [f"b1:{form.cb8_b1.data}", f"b2:{form.cb8_b2.data}", f"c3:{form.cb8_c3.data}",
                                  f"d4:{form.cb8_d4.data}", f"d1:{form.cb8_d1.data}", f"e1:{form.cb8_e1.data}",
                                  f"f1:{form.cb8_f1.data}", f"g1:{form.cb8_g1.data}", f"f2:{form.cb8_f2.data}"])
        writer.writerow(["q9"] + [form.cb9_1.data, form.cb9_2.data, form.cb9_3.data,
                                  form.cb9_4.data, form.cb9_5.data, form.cb9_6.data,
                                  form.cb9_7.data, form.cb9_8.data])
        writer.writerow(["ac1"]+[form.save_attention.data]),
        writer.writerow(["ac2"]+[form.blau.data, form.grün.data, form.rot.data, form.gelb.data, form.violet.data])

def evaluate_expertise(form: ExpertiseForm):
    score = 0

    filepath = Path("severusStudy/questions/csv/2_expertise.csv")
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        next(reader)  # skip first row
        for idx, (frage, antwortoptionen, richtung) in enumerate(reader):
            for field in form:
                if field.type == "RadioField":
                    form_question = field.label.text
                    form_answer = field.data
                    if frage == form_question:
                        if richtung == "positiv":
                            question_points = likert_map_positiv[form_answer]
                        elif richtung == "negativ":
                            question_points = likert_map_negativ[form_answer]
                        # print("QUESTIONS: CSV:", frage, "FORM:", form_question, "ANSWER:", form_answer, "POINTS:", question_points)
                        score += question_points
    max_score = 56
    return 0.5+(score / max_score*0.5)

def evaluate_understanding_score(form: QuestionnaireFormUnderstanding):

    final_score = 0

    filepath = Path("severusStudy/questions/csv/4a_understanding_questionnaire.csv")
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader)  # skip first row
        for idx, (question, answer, options, points, comment) in enumerate(reader):
            for field in form:
                if field.type == "RadioField":
                    label = field.label.text
                    if label == question:
                        data = field.data
                        if data == answer:
                            final_score += int(points.replace(" ", ""))


    filepath = Path("severusStudy/questions/csv/4b_understanding_questionnaire.csv")
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader)  # skip first row
        for idx, (question, answer, options, points, comment) in enumerate(reader):
            pass

    return final_score
