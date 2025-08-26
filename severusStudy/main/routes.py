from typing import Any
from flask import render_template, current_app, session, redirect, request, url_for, make_response

from severusStudy.user import User
from . import main
from .forms import FeedbackForm, IDForm, CheckboxForm, ExpertiseForm, QuestionnaireFormPostOne, \
    QuestionnaireFormPostTwo, \
    QuestionnaireFormUnderstanding, save_question_answers, save_understanding_form, PersonalInfoForm, \
    save_personal_infos, evaluate_understanding_score, evaluate_expertise, check_quarto_vorwissen, muttersprache
from .. import manager, logger

from enum import Enum


class StudyState(Enum):
    Initial = "Initial"
    ConsentGiven = "ConsentGiven"
    PersonalInfosGiven = "PersonalInfosGiven"
    # ExpertiseGiven = "ExpertiseGiven"
    InExperiment = "InExperiment"
    ExperimentDone = "ExperimentDone"
    PostQuestionsOneDone = "PostQuestionsOneDone"
    PostQuestionsDone = "PostQuestionsDone"
    UnderstandingDone = "UnderstandingDone"
    Finished = "Finished"
    Ausschluss = "Ausschluss"


def check_user_existing():
    try:
        return manager.get_user(session["uid"])
    except KeyError:
        logger.debug("User id not found, redirect")
        return None


def get_or_create_user():
    exp_type = current_app.config["EXPERIMENT_TYPE"]
    session["experiment_type"] = exp_type
    try:
        user = manager.get_user(session["uid"])
        if not user:
            logger.debug("No user for existing session uid ({})".format(session["uid"]))
            user = manager.new_user(request.environ['REMOTE_ADDR'], experiment_type=exp_type,
                                    user_agent=request.user_agent, is_crowd=True)
            session["uid"] = user.uid
        user.log_routing_time("intro")
    except KeyError:
        user = manager.new_user(request.environ['REMOTE_ADDR'], experiment_type=exp_type,
                                user_agent=request.user_agent, is_crowd=True)
        session["uid"] = user.uid
    return user
def get_redirect(state: StudyState):
    print("GET_REDIRECT STATE:", state, type(state))
    if state == StudyState.ConsentGiven:
        return ".intro"
    elif state == StudyState.PersonalInfosGiven:
        return ".before_experiment"
        #return ".survey_expertise"
    #elif state == StudyState.ExpertiseGiven:
        #return ".before_experiment"
    elif state == StudyState.InExperiment:
        return ".experiment"
    elif state == StudyState.ExperimentDone:
        return ".survey_post_one"
    elif state == StudyState.PostQuestionsOneDone:
        return ".survey_post_two"
    elif state == StudyState.PostQuestionsDone:
        return ".questionnaire_understanding"
    elif state == StudyState.UnderstandingDone:
        return ".exit"
    elif state == StudyState.Finished:
        return ".exit"
    elif state == StudyState.Ausschluss:
        return ".exit"
    else:
        assert False, "Should never land here."


@main.route("/updateBrowser")
def update_browser():
    print("UPDATE_BROWSER")
    # remove user with incompatible browser
    del manager.users[session["uid"]]
    del session["uid"]
    return render_template("updateBrowser.html")


@main.route('/', methods=['GET', 'POST'])
@main.route('/index', methods=['GET', 'POST'])
def index():
    print("INDEX")

    prolific_id = request.args.get('PROLIFIC_PID')
    if prolific_id is not None:
        session["prolific_id"] = prolific_id

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))
    if current_app.config["SKIP_QUESTIONNAIRE"]:
        user = get_or_create_user()
        session["state"] = StudyState.InExperiment.value
        return render_template('before_experiment.html', socket_path=current_app.config["SOCKET_PATH"])
    session_state = session.get("state")
    state = StudyState(session_state)
    if state == StudyState.Initial:

        form = CheckboxForm()
        if form.validate_on_submit():
            if form.checkbox:
                session["consent"] = True
                session["state"] = StudyState.ConsentGiven.value
            return redirect(url_for('.intro'))
        return render_template("index.html", form=form)

    else:
        return redirect(url_for(get_redirect(state)))


@main.route("/belehrung", methods=['GET', 'POST'])
def belehrung():

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    # user = check_user_existing()
    # if user is None:
    #     return redirect(url_for(".intro"))
    # user.log_routing_time("belehrung")

    return render_template('belehrung.html', socket_path=current_app.config["SOCKET_PATH"])


@main.route('/intro')
def intro():
    print("INTRO")
    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))


    state = StudyState(session.get("state"))
    if state == StudyState.ConsentGiven:
        user = get_or_create_user()
        if session.get("prolific_id") is not None:
            user.add_crowd_id(session.get("prolific_id"))
        return render_template("intro.html")
    else:
        return redirect(url_for(get_redirect(state)))


@main.route("/personal_infos", methods=['GET', 'POST'])
def personal_infos():
    print("PERSONAL_INFOS")

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("personal_infos")


    state = StudyState(session.get("state"))
    if state == StudyState.ConsentGiven:

        form = PersonalInfoForm()
        if form.validate_on_submit():
            save_personal_infos(form, manager.get_user(session["uid"]).uid)

            # If users are non-native speakers
            if muttersprache(form):
                session["ausschluss"] = True
                session["state"] = StudyState.Ausschluss.value
                return redirect(url_for('.exit'))
            # If users already have knowledge of the game quarto they are redirected to the exit page
            elif check_quarto_vorwissen(form):
                session["ausschluss"] = True
                session["state"] = StudyState.Ausschluss.value
                return redirect(url_for('.exit'))
            else:
                session["ausschluss"] = False

            session["state"] = StudyState.PersonalInfosGiven.value
            #return redirect(url_for('.survey_expertise'))
            return redirect(url_for('.before_experiment'))
        else:
            return render_template('personal_infos.html', form=form, socket_path=current_app.config["SOCKET_PATH"])

    else:
        return redirect(url_for(get_redirect(state)))





# @main.route("/survey_expertise", methods=['GET', 'POST'])
# def survey_expertise():
#     print("SURVEY_PRE")
#
#     if session.get("state") is None:
#         session["state"] = StudyState.Initial.value
#         return redirect(url_for(".index"))
#
#     user = check_user_existing()
#     if user is None:
#         return redirect(url_for(".intro"))
#     user.log_routing_time("expertise")
#
#
#     state = StudyState(session.get("state"))
#     if state == StudyState.PersonalInfosGiven:
#
#         form = ExpertiseForm()
#
#         if form.validate_on_submit():
#             save_question_answers("expertise", form, manager.get_user(session["uid"]).uid)
#             score = evaluate_expertise(form)
#             user.snape.partner.expertise = score
#             print("partner expertise:", user.snape.partner.expertise)
#             session["state"] = StudyState.ExpertiseGiven.value
#             return redirect(url_for('.before_experiment'))
#
#         else:
#             return render_template('survey_expertise.html', form=form, socket_path=current_app.config["SOCKET_PATH"])
#
#     else:
#         return redirect(url_for(get_redirect(state)))



@main.route("/before_experiment", methods=['GET', 'POST'])
def before_experiment():
    print("BEFORE_EXPERIMENT")

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("before_experiment")

    state = StudyState(session.get("state"))
    #if state == StudyState.ExpertiseGiven:
    if state == StudyState.PersonalInfosGiven:
        session["state"] = StudyState.InExperiment.value
        return render_template('before_experiment.html', socket_path=current_app.config["SOCKET_PATH"])
    else:
        return redirect(url_for(get_redirect(state)))


@main.route('/experiment')
def experiment():
    print("EXPERIMENT")
    """
        Route where the actual experiment is being performed. As this example assumes that
        the data to be presented is adapted using websockets, we only need one route for
        the experiment.
    """

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("experiment")

    state = StudyState(session.get("state"))
    print(state)
    if state == StudyState.InExperiment:
        if user.snape_finished:
            session["state"] = StudyState.ExperimentDone.value
            return redirect(url_for(".survey_post_one"))
        else:
            print(current_app.config["FEEDBACK_MODE"])
            print(user.uid)
            return render_template('experiment.html',
                                   socket_path=current_app.config["SOCKET_PATH"],
                                   feedback_mode=current_app.config["FEEDBACK_MODE"],
                                   is_baseline = current_app.config["EXPERIMENT_TYPE"] )

    else:
        return redirect(url_for(get_redirect(state)))



@main.route("/survey_post_one", methods=['GET', 'POST'])
def survey_post_one():
    print("SUBJECTIVE")

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("survey_subjective_1")

    state = StudyState(session.get("state"))
    if state == StudyState.ExperimentDone:

        form = QuestionnaireFormPostOne()
        if form.validate_on_submit():
            save_question_answers("post_one", form, manager.get_user(session["uid"]).uid)
            session["state"] = StudyState.PostQuestionsOneDone.value
            return redirect(url_for('.survey_post_two'))
        else:
            return render_template('survey_post_one.html', form=form, socket_path=current_app.config["SOCKET_PATH"])

    else:
        return redirect(url_for(get_redirect(state)))

@main.route("/survey_post_two", methods=['GET', 'POST'])
def survey_post_two():
    print("SUBJECTIVE")

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("survey_subjective_2")

    state = StudyState(session.get("state"))
    if state == StudyState.PostQuestionsOneDone:

        form = QuestionnaireFormPostTwo()
        if form.validate_on_submit():
            save_question_answers("post_two", form, manager.get_user(session["uid"]).uid)
            session["state"] = StudyState.PostQuestionsDone.value
            return redirect(url_for('.questionnaire_understanding'))
        else:
            return render_template('survey_post_two.html', form=form, socket_path=current_app.config["SOCKET_PATH"])

    else:
        return redirect(url_for(get_redirect(state)))

@main.route("/questionnaire_understanding", methods=['GET', 'POST'])
def questionnaire_understanding():
    print("UNDERSTANDING")

    if session.get("state") is None:
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()
    if user is None:
        return redirect(url_for(".intro"))
    user.log_routing_time("survey_understanding")

    state = StudyState(session.get("state"))
    if state == StudyState.PostQuestionsDone:

        form = QuestionnaireFormUnderstanding()
        if form.validate_on_submit():
            save_question_answers("understanding", form, manager.get_user(session["uid"]).uid)
            session["state"] = StudyState.UnderstandingDone.value

            user.finished = True

            save_understanding_form(form, manager.get_user(session["uid"]).uid)
            return redirect(url_for('.exit'))
        else:
            return render_template('survey_understanding.html', form=form,
                                   socket_path=current_app.config["SOCKET_PATH"])

    else:
        return redirect(url_for(get_redirect(state)))


@main.route('/exit', methods=['GET', 'POST'])
def exit():
    """
        A route for finalizing the experiment. I usually present the MTurk code here or
        maybe also ask for additional information (could also be done at index).
    """
    print("EXIT")

    template_args: dict[str, Any] = dict()

    if session.get("state") is None:
        print("NO SESSION STATE!")
        session["state"] = StudyState.Initial.value
        return redirect(url_for(".index"))

    user = check_user_existing()

    if user is None:
        if session.get("key") is not None and session.get("uid") is not None:
            feedback_form = FeedbackForm()
            template_args["feedback_form"] = feedback_form

            if feedback_form.submit_feedback.data and feedback_form.validate():
                User.log_feedback_exit(session["uid"], feedback_form.feedback.data)
                template_args["got_feedback"] = True
                # del session["uid"]                    

            return render_template("exit.html", **template_args, form=None, added=True, crowd_key=session.get('key'))
        return redirect(url_for(".intro"))

    user.log_routing_time("exit")

    state = StudyState(session.get("state"))

    if state == StudyState.UnderstandingDone or state == StudyState.Ausschluss or state == StudyState.Finished:
        template_args["user"] = user

        if user.finished and user.uid != current_app.config["SECRET_ADMIN_USERNAME"] or session["ausschluss"]:
            feedback_form = FeedbackForm()
            if not user.got_feedback:
                template_args["feedback_form"] = feedback_form
                if feedback_form.submit_feedback.data and feedback_form.validate():
                    print(feedback_form.feedback.data)
                    user.log_feedback(feedback_form.feedback.data)
                    user.got_feedback = True
                    template_args["got_feedback"] = True
            if user.crowd_user:
                form = IDForm()
                if user.crowd_id or (form.submit_ID.data and form.validate()):
                    if not user.crowd_id:
                        user.add_crowd_id(form.crowd_ID.data)
                    logger.debug("Crowd id added to user {}".format(user.uid))
                    #                    disconnect()

                    # Generate a result key
                    key = "{}{}{}{}".format(user.crowd_id[-1], current_app.config["CROWD_KEY"], user.user_number,
                                            user.crowd_id[0])

                    # Clean up after the user finished, this includes deleting his cookie
                    del manager.users[session["uid"]]
                    # del session["state"]
                    session["key"] = key

                    return render_template("exit.html", **template_args, form=None, added=True, crowd_key=key)
                return render_template("exit.html", **template_args, form=form, added=False)
            else:
                del manager.users[session["uid"]]
                del session["uid"]
                #                disconnect()
                return render_template("exit.html", user=user, form=None)


        session["state"] = StudyState.Finished.value

        return redirect(url_for('.exit'))

    else:
        return redirect(url_for(get_redirect(state)))
