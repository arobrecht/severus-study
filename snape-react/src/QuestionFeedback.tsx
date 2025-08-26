import React, { FormEvent, useState } from 'react';
import { Socket } from 'socket.io-client';

function QuestionFeedback(props: {
    socket: Socket;
    processFeedback: (feedback: string) => void;
    onUserIsAsking: (toggle: boolean) => void;
    disabled: boolean;
}) {


    const { processFeedback, onUserIsAsking, disabled } = props;
    const [answer, setAnswer] = useState('');
    const [log, setLog] = useState<string>('');

    // function to submit feedback if button is pressed
    async function submitFeedback(event: FormEvent) {
        event.preventDefault();
        const feedback = `Log: \n${log}`;

        //console.log('# START PROCESSING')
        await processFeedback(feedback);
        //console.log('# FINISHED PROCESSING')

        setAnswer('');
        setLog(''); // Clear log after submission
        (document.activeElement as HTMLElement | undefined)?.blur();  // Blur the input field
    }

    function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
        const newValue = e.target.value;
        const timestamp = new Date().toISOString();

        if (newValue.length < answer.length) {
            setLog((prevLog) => prevLog + `{time: ${timestamp}, char: 'DELETE'}\n`);
        } else {
            const newChar = newValue.slice(-1);
            setLog((prevLog) => prevLog + `{time: ${timestamp}, char: '${newChar}'}\n`);
        }

        setAnswer(newValue);
    }

    return (
        <div id="questionFeedback" className="feedbackBox">
            <input
                id="questionInput"
                type="text"
                placeholder="Ihre Frage..."
                value={answer}
                onChange={handleInputChange}
                onFocus={() => !disabled && onUserIsAsking(true)}
                onBlur={() => !disabled && onUserIsAsking(false)}
                onKeyDown={(e) => !disabled && e.key === 'Enter' && submitFeedback(e)}
                maxLength={100}
                disabled={disabled}
                className={disabled ? 'input.disabled' : ''}
            />
            <input
                type="submit"
                id = "questionButton"
                value="Frage senden"
                onClick={submitFeedback}
                disabled={disabled}
                className={disabled ? 'disabled-feedback' : ''}
            />
        </div>
    );
}

export default QuestionFeedback;