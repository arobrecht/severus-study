import React, { useState } from 'react';

/**
 * Component handling validation freetext input.
 * @param props object props.
 * "giveFeedback": callback to submit validation answer to parent.
 * "resetHistory": callback resetting the explanation history.
 * @returns ValidationFeedback component.
 */
function ValidationFeedback(props: {
    giveFeedback: (x: string) => void;
    resetHistory: () => void;
}) {
    const { giveFeedback, resetHistory } = props;
    const [answer, setAnswer] = useState('');

    function submitFeedbackEnter(e: React.KeyboardEvent<HTMLInputElement>) {
        if (e.key === 'Enter') {
            submitFeedback();
            return;
        }
    }

    function submitFeedback() {
        resetHistory();
        giveFeedback(answer);
        setAnswer('');
    }

    return (
        <div id="validationFeedback" className="flexBottom">
            <input
                id="validationInput"
                type="text"
                placeholder="Ihre Antwort..."
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={submitFeedbackEnter}
            />
            <input type="button" onClick={submitFeedback} value="OK" />
        </div>
    );
}

export default ValidationFeedback;
