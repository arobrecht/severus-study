import React, { useCallback, useEffect, useRef, useState } from 'react';
import { connect, Socket } from 'socket.io-client';
import SimpleFeedback from './SimpleFeedback';
import QuestionFeedback from './QuestionFeedback';
import Swal from "sweetalert2";
import exp from 'node:constants';

const TIMEOUT = 4500;           /*display time for explanation*/
const TIMEOUT_SHORT = 2000;     /*time to wait after user unfocused input until next explanation*/
const NO_FEEDBACK_UNTIL_REMINDER = 5;  /*Amount of times no feedback is allowed until reminder popup*/

interface DynamicSpeechBubbleProps {
    text: string;
    className?: string;
}

const DynamicSpeechBubble = ({ text, className = '' }: DynamicSpeechBubbleProps) => {
    return (
      <div className="speech-bubble-container">
        <div className={`speech-bubble ${className}`}>
          {/* Main speech bubble content */}
          <div className="speech-bubble-content">
            <p>{text}</p>
          </div>

          {/* Tail of the speech bubble */}
          <div className={`speech-bubble-tail ${className}`}></div>
        </div>
      </div>
    );
};

let socket: Socket;

/**
 * Creates an Experiment component handling the socket connection and managing the user interaction.
 * @param props object including property "socketPath" containing route to socket accepting server
 * @returns Experiment component.
 */
function Experiment(props: { socketPath: string; feedbackMode: 'FREETEXT' | 'EMOJI'; isBaseline: 'baseline' | 'adaptive' }) {

    if (!props.feedbackMode) {
        //console.log('WARN: feedback mode not defined, fallback to FREETEXT');
        props.feedbackMode = 'FREETEXT';
    }
    const [explanation, setExplanation] = useState('bitte warten...');
    const [feedback, setFeedback] = useState('None');
    const [feedbackMode, setFeedbackMode] = useState(props.feedbackMode);
    const [isBaseline] = useState(props.isBaseline)
    const feedbackRef = useRef('');
    const [requiresFeedback, setRequiresFeedback] = useState(false);
    const [showFeedbackOptions, setShowFeedbackOptions] = useState(false);
    const [isValidation, setIsValidation] = useState(false);
    const partnerUpdateDisabledRef = useRef(false);
    const answerTimeoutRef = useRef<number | null>(null);
    const [isWaitingForExplanation, setIsWaitingForExplanation] = useState(false);
    const noFeedbackCount = useRef<number>(0);



    /**
     * Called once at startup. Setup connection event handlers.
     */
    useEffect(() => {
        socket = connect('', { path: props.socketPath });

        // Setup your socket events/callbacks
        socket.on('disconnect', function() {
            //console.log('Disconnected');
            //Disconnect kann auch ein Netzwerkproblem sein.
            //Hiermit können wir versuchen uns wieder zu verbinden.
            //Das ist wahrscheinlich ein bisschen gefährlich, je nachdem wo wir gerade in der Explanation sind
            //aber immer noch besser als ein kompletter Abbruch weil ein Paket nicht durchgegangen ist.
            setTimeout(() => {
                socket = connect('', { path: props.socketPath });
                socket.emit('get_explanation', handleSnapeExplanation);
            }, 2000);
            return;
        });

        socket.on('finish', function(msg) {
            window.location.href = 'exit';
            return;
        });

        socket.emit('get_explanation', handleSnapeExplanation);

        return () => {
            //console.log('now disconnecting..');
            socket.disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    /**
     * Called every time the value of "feedback" is changed. Updates the
     * "feedbackRef" value.
     */
    useEffect(() => {feedbackRef.current = feedback;}, [feedback]);



    /**
     * Set current state with regards to the explanation (and flags).
     * @param explanation string containing snape explanation.
     * @param block string containing the block the triple is from
     * @param requiresFeedback boolean value indicating if user feedback is expected for this explanation.
     * @param isValidation boolean value indication if the explanation is a validation question.
     * @param triples triple identifier as string.
     * @param partnerUpdateDisabled boolean disabling the partner attribute update following the feedback.
     * @param startOnTimestamp Future timestamp to set state
     * @param is_triapleaction
     * @returns void
     */
    function handleSnapeExplanation(
        explanation: string,
        block: string,
        requiresFeedback: boolean,
        isValidation: boolean,
        triples: [string],
        partnerUpdateDisabled: boolean,
        startOnTimestamp: number = Date.now(),
        is_triapleaction: boolean,
    ) {
        if (explanation == null) {
            //console.log("Explanation is null")

            setExplanation('end reached');
            const newLocation = window.location.href.replace(
                /experiment$/,
                'experiment_post',
            );
            window.location.replace(newLocation);
            //console.log("Window reload")
            window.location.reload();
            return;
        }
        const TIMEOUT = getTimeout(explanation);
        console.log("Progress if explanation is different!")
        /*if (explanation != null) {
            console.log('handleSnapeExplanation called:', {
                explanation: explanation.substring(0, 50) + '...',
                block,
                requiresFeedback,
                isValidation,
                partnerUpdateDisabled,
                timestamp: new Date().toISOString()
            });
        }*/
        //console.log("After explanation is not null!")

        setIsWaitingForExplanation(false);


        setRequiresFeedback(is_triapleaction);
        partnerUpdateDisabledRef.current = partnerUpdateDisabled;
        //console.log("Explanation is asked for")

        if (Date.now() + 1 < startOnTimestamp) {
            //console.log('waiting..');
            setTimeout(
                () =>
                    handleSnapeExplanation(
                        explanation,
                        block,
                        requiresFeedback,
                        isValidation,
                        triples,
                        partnerUpdateDisabled,
                        startOnTimestamp,
                        is_triapleaction,
                    ),
                300,
            );
            return;
        }

        setExplanation(explanation);
        setFeedback('None');

        if (answerTimeoutRef.current != null) {
            //console.log('Clearing existing timeout');
            clearTimeout(answerTimeoutRef.current);
            answerTimeoutRef.current = null;
        }

        if (isValidation) {
            setIsValidation(true);

            return;
        }

        if (requiresFeedback) {
            //console.log('Setting timeout for feedback:', TIMEOUT);
            answerTimeoutRef.current = setTimeout(() => {
                //console.log('Timeout triggered - waiting for feedback');
                setIsWaitingForExplanation(true);
                giveFeedback();
            }, TIMEOUT) as unknown as number;
        } else {
            //console.log('Setting timeout for next explanation:', TIMEOUT);
            answerTimeoutRef.current = setTimeout(() => {
                //console.log('Timeout triggered - getting next explanation');
                setIsWaitingForExplanation(true);
                socket.emit('get_explanation', handleSnapeExplanation);
            }, TIMEOUT) as unknown as number;
        }

    }

    /**
     * Handle snape response. Display answer and continue after TIMEOUT ms.
     * @param answer Socket response.
     * @returns
     */
    function handleSnapeResponse(answer: string) {
        if (!answer) {
            socket.emit('get_explanation', handleSnapeExplanation);
            return;
        }

        setExplanation(answer);
        //console.log('emitting get_explanation in handleSnapeAnswer');
        const endAnswerDisplayTimestamp = Date.now() + TIMEOUT;
        socket.emit(
            'get_explanation',
            (
                exp: string,
                block: string,
                reqFeedback: boolean,
                isValidation: boolean,
                triples: [string],
                partnerUpdateDisabled: boolean,
                is_tripleaction: boolean,
            ) =>
                handleSnapeExplanation(
                    exp,
                    block,
                    reqFeedback,
                    isValidation,
                    triples,
                    partnerUpdateDisabled,
                    endAnswerDisplayTimestamp,
                    is_tripleaction,
                ),
        );
    }

    /**
     * Create a callback to provide feedback via the socket. Send the provided string
     * parameter as feedback and update the state accordingly.
     */
    const giveFeedback = useCallback(async (value: string = '') => {
        setIsWaitingForExplanation(true);
        const feedbackValue = value || feedbackRef.current;
        //console.log('Using feedback value:', feedbackValue);


        // feedback reminder
        if (feedbackValue === 'None') {
            noFeedbackCount.current += 1;
            //console.log('No feedback received, incrementing counter:', noFeedbackCount.current)
            if (noFeedbackCount.current >= NO_FEEDBACK_UNTIL_REMINDER) {
                await Swal.fire({
                    title: "Denk daran mir Feedback zu geben!",
                    text: "Je mehr Rückmeldung ich von dir bekomme, desto besser kann ich mich nach dir richten.",
                    icon: "info",
                    confirmButtonText: "Verstanden",
                    customClass: {
                        confirmButton: 'swal2-confirm-custom'
                    }
                });
                noFeedbackCount.current = 0;
            }
        } else {
            //console.log('feedback received, resetting counter!')
            noFeedbackCount.current = 0;
        }


        setIsValidation(false);
        if (answerTimeoutRef.current != null) {
            //console.log('Clearing feedback timeout');
            clearTimeout(answerTimeoutRef.current);
            answerTimeoutRef.current = null;
        }

        //console.log('Emitting feedback to socket');
        socket.emit('feedback', feedbackValue, handleSnapeResponse);
    }, []);

    const getTimeout = (explanation: string | any[]) => {
        //console.log("Explanation length:",explanation.length)
        if (explanation.slice(-1) === '?') {
            //console.log('Setting timeout one minute for verification question!')
            return 600000
        }
        if (explanation.length > 80) {
            return 8000; // Extra long timeout
        } else if (explanation.length > 60) {
            return 6500; // Long timeout
        } else {
            return 4500; // Short timeout
        }
    };

    // this gets executed when clicking on the text input field
    const handleUserIsAsking = useCallback((toggle: boolean) => {
        //console.log('handleUserIsAsking called with toggle:', toggle);

        if (toggle) {
            if (answerTimeoutRef.current) {
                //console.log('User focused input - clearing timeout');
                clearTimeout(answerTimeoutRef.current);
                answerTimeoutRef.current = null;
            }
        } else {
            //console.log('User unfocused input - setting new timeout');
            answerTimeoutRef.current = setTimeout(() => {
                //console.log('Input blur timeout triggered');
                setIsWaitingForExplanation(true);
                if (requiresFeedback || (requiresFeedback && partnerUpdateDisabledRef.current)) {
                    //console.log('Calling giveFeedback after blur timeout');
                    giveFeedback();
                }
                else{
                    socket.emit('get_explanation', handleSnapeExplanation);
                }
            }, TIMEOUT_SHORT) as unknown as number;
            //console.log('User unfocused input, setting short timeout')
        }
    }, [requiresFeedback, giveFeedback]);


    return (
        <div className={`flexBottomContainer`}>
            <div id='wrapper'>
                {!showFeedbackOptions && (
                    <div id='game'>
                        <DynamicSpeechBubble
                            text={explanation}
                            className={feedback === '+' ? 'understood' : feedback === '-' ? 'not-understood' : ''}
                        />
                    </div>
                )}
            </div>

            {/* loading animation */}
            {!(showFeedbackOptions || isValidation) && isBaseline !== 'baseline' &&(
                <div className='flexBottom lds-ellipsis'>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
            )}

            {/* show simple sentiment feedback as long as triple specific feedback is not activated */}
            {!showFeedbackOptions && isBaseline !== 'baseline' &&(
                <SimpleFeedback
                    hidden={requiresFeedback}
                    mode={feedbackMode}
                    setFeedback={setFeedback}
                    disabled={isWaitingForExplanation || (explanation.slice(-1) === '?')}
                />
            )}
            {feedbackMode === 'FREETEXT' &&
                isBaseline !== 'baseline' &&
                !isValidation &&
                !requiresFeedback &&
                (
                    <QuestionFeedback
                        socket={socket}
                        processFeedback={giveFeedback}
                        onUserIsAsking={handleUserIsAsking}
                        disabled={isWaitingForExplanation}
                    />
                )}
        </div>
    );
}

export default Experiment;
